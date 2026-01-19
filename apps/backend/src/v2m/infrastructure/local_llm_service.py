
"""
Servicio LLM Local usando llama-cpp-python.

Diseño Clave:
- Usa `create_chat_completion()` que lee la plantilla del GGUF automáticamente.
- Funciona con Qwen, Llama, Phi, Mistral sin cambiar código.
- Context Manager Async para Hot-Swap de VRAM.

Este módulo implementa la interfaz `LLMService` usando `llama.cpp` como backend,
permitiendo inferencia local en GPU sin depender de APIs externas.
"""

from __future__ import annotations

import asyncio
import gc
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from v2m.application.llm_service import LLMService
from v2m.config import BASE_DIR, config
from v2m.core.logging import logger
from v2m.domain.errors import LLMError

if TYPE_CHECKING:
    from llama_cpp import Llama


class LocalLLMService(LLMService):
    """
    Servicio LLM Local con gestión de VRAM bajo demanda.

    Implementa la interfaz `LLMService` usando `llama-cpp-python` como backend.
    Soporta cualquier modelo GGUF (Qwen, Llama, Phi, Mistral) gracias al uso
    de `create_chat_completion()` que aplica automáticamente la plantilla
    de chat correcta según los metadatos del archivo GGUF.

    Características principales:
        - Carga Lazy del modelo: no consume VRAM hasta el primer uso.
        - Método `unload()` para liberar VRAM inmediatamente.
        - Context Manager Async `loaded()` para hot-swap automático.
        - Agnóstico al formato de chat (ChatML, Llama, etc.).

    Atributos:
        system_prompt: Instrucción del sistema para el modelo.
        is_loaded: Indica si el modelo está cargado en VRAM.
    """

    def __init__(self) -> None:
        """
        Inicializa el servicio de LLM Local.

        Carga la configuración desde `config.toml` y el prompt del sistema.
        El modelo NO se carga en este momento (Lazy Loading) para evitar
        consumir VRAM innecesariamente al inicio de la aplicación.
        """
        self._model: Llama | None = None
        self._config = config.llm.local
        self._model_path = BASE_DIR / self._config.model_path

        # Cargar system prompt
        prompt_path = BASE_DIR / "prompts" / "refine_system.txt"
        try:
            self.system_prompt = prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("prompt del sistema no encontrado, usando valor por defecto")
            self.system_prompt = "Eres un editor de texto experto."

    def _ensure_model_exists(self) -> None:
        """
        Verifica que el archivo del modelo existe en disco.

        Raises:
            LLMError: Si el archivo GGUF no existe, con instrucciones de descarga.
        """
        if not self._model_path.exists():
            raise LLMError(
                f"modelo no encontrado: {self._model_path}\n"
                f"descarga con: ./scripts/download_model.sh\n"
                f"o manualmente: huggingface-cli download Qwen/Qwen2.5-3B-Instruct-GGUF "
                f"qwen2.5-3b-instruct-q4_k_m.gguf --local-dir {self._model_path.parent}"
            )

    def load(self) -> None:
        """
        Carga el modelo en VRAM.

        Si el modelo ya está cargado, esta función no hace nada.
        La carga es una operación costosa (~2-5 segundos) que debe
        hacerse una vez y reutilizarse.

        Raises:
            LLMError: Si el archivo del modelo no existe.
            RuntimeError: Si hay problemas cargando el modelo en GPU.
        """
        if self._model is not None:
            return  # Ya cargado

        self._ensure_model_exists()
        logger.info(f"cargando modelo local: {self._model_path.name}")

        # Import lazy para evitar error si llama-cpp-python no está instalado
        from llama_cpp import Llama

        self._model = Llama(
            model_path=str(self._model_path),
            n_gpu_layers=self._config.n_gpu_layers,
            n_ctx=self._config.n_ctx,
            verbose=False,
            chat_format="chatml",  # Fallback si el GGUF no tiene metadatos de chat
        )
        logger.info("✅ modelo local cargado en vram")

    def unload(self) -> None:
        """
        Libera el modelo de VRAM inmediatamente.

        Destruye la instancia del modelo y fuerza Garbage Collection
        para liberar la memoria CUDA lo antes posible.
        """
        if self._model is not None:
            logger.info("descargando modelo local de vram...")
            del self._model
            self._model = None
            # Forzar liberación de memoria CUDA
            gc.collect()
            logger.info("✅ vram liberada")

    @property
    def is_loaded(self) -> bool:
        """
        Indica si el modelo está cargado en VRAM.

        Returns:
            bool: True si el modelo está cargado y listo para inferencia.
        """
        return self._model is not None

    @asynccontextmanager
    async def loaded(self) -> AsyncIterator[None]:
        """
        Context Manager Async para Hot-Swap de VRAM.

        Carga el modelo al entrar y lo descarga al salir. Útil para
        GPUs con poca memoria donde no es viable mantener múltiples
        modelos cargados simultáneamente.

        Ejemplo:
            ```python
            async with llm_service.loaded():
                result = await llm_service.process_text(text)
            # vram liberada automáticamente al salir
            ```

        Nota:
            Si prefieres mantener el modelo cargado para menor latencia,
            llama a `load()` una vez al inicio y no uses este context manager.
        """
        try:
            await asyncio.to_thread(self.load)
            yield
        finally:
            await asyncio.to_thread(self.unload)

    async def process_text(self, text: str) -> str:
        """
        Procesa texto usando el modelo local.

        Usa `create_chat_completion()` que aplica automáticamente la plantilla
        de chat correcta según los metadatos del GGUF. Esto hace el código
        agnóstico al modelo (funciona con Qwen, Llama, Phi, Mistral) sin
        cambiar una sola línea de Python.

        Args:
            text: El texto a procesar/refinar.

        Returns:
            str: El texto procesado por el modelo.

        Raises:
            LLMError: Si el modelo no existe o hay errores de inferencia.
        """
        # Lazy loading si no está cargado
        if self._model is None:
            await asyncio.to_thread(self.load)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": text},
        ]

        try:
            logger.info("procesando texto con modelo local...")

            # create_chat_completion lee la plantilla del gguf automáticamente
            # No hardcodeamos <|im_start|> ni ningún formato específico
            response = await asyncio.to_thread(
                self._model.create_chat_completion,  # type: ignore
                messages=messages,
                max_tokens=self._config.max_tokens,
                temperature=self._config.temperature,
            )

            result = response["choices"][0]["message"]["content"].strip()
            logger.info("✅ procesamiento con modelo local completado")
            return result

        except Exception as e:
            logger.error(f"error procesando texto con modelo local: {e}")
            raise LLMError(f"falló el procesamiento con modelo local: {e}") from e

    async def translate_text(self, text: str, target_lang: str) -> str:
        """
        Traduce texto usando el modelo local.

        Args:
            text: El texto a traducir.
            target_lang: Idioma objetivo.

        Returns:
            str: El texto traducido.

        Raises:
            LLMError: Si falla la traducción.
        """
        if self._model is None:
            await asyncio.to_thread(self.load)

        system_instruction = (
            f"Eres un traductor experto. Traduce el siguiente texto al idioma '{target_lang}'. "
            "Devuelve SOLO el texto traducido, sin explicaciones ni notas adicionales."
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": text},
        ]

        try:
            logger.info(f"traduciendo texto a {target_lang} con modelo local...")

            response = await asyncio.to_thread(
                self._model.create_chat_completion,  # type: ignore
                messages=messages,
                max_tokens=self._config.max_tokens,
                temperature=self._config.translation_temperature,
            )

            result = response["choices"][0]["message"]["content"].strip()
            logger.info("✅ traducción con modelo local completada")
            return result

        except Exception as e:
            logger.error(f"error traduciendo con modelo local: {e}")
            raise LLMError(f"falló la traducción con modelo local: {e}") from e
