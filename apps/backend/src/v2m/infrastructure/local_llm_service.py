# This file is part of voice2machine.
#
# voice2machine is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# voice2machine is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with voice2machine.  If not, see <https://www.gnu.org/licenses/>.

"""
SERVICIO LLM LOCAL USANDO LLAMA-CPP-PYTHON

DISEÑO CLAVE:
- usa create_chat_completion() que lee la plantilla del gguf automáticamente
- funciona con qwen llama phi mistral sin cambiar código
- context manager async para hot-swap de vram

este módulo implementa la interfaz llmservice usando llama.cpp como backend
permitiendo inferencia local en gpu sin depender de apis externas
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
    SERVICIO LLM LOCAL CON GESTIÓN DE VRAM BAJO DEMANDA

    implementa la interfaz llmservice usando llama-cpp-python como backend
    soporta cualquier modelo gguf (qwen llama phi mistral) gracias al uso
    de create_chat_completion() que aplica automáticamente la plantilla
    de chat correcta según los metadatos del archivo gguf

    CARACTERÍSTICAS PRINCIPALES:
        - carga lazy del modelo no consume vram hasta primer uso
        - método unload() para liberar vram inmediatamente
        - context manager async loaded() para hot-swap automático
        - agnóstico al formato de chat (chatml llama etc)

    ATTRIBUTES:
        system_prompt: instrucción del sistema para el modelo
        is_loaded: indica si el modelo está cargado en vram

    EXAMPLE:
        uso básico con carga lazy::

            service = LocalLLMService()
            result = await service.process_text("texto a procesar")

        uso con hot-swap de vram (para gpus con poca memoria)::

            async with service.loaded():
                result = await service.process_text("texto")
            # vram liberada automáticamente al salir
    """

    def __init__(self) -> None:
        """
        INICIALIZA EL SERVICIO DE LLM LOCAL

        carga la configuración desde config.toml y el system prompt desde
        el archivo refine_system.txt el modelo no se carga en este momento
        carga lazy para evitar consumir vram innecesariamente

        RAISES:
            LLMError: si el archivo del modelo no existe
        """
        self._model: Llama | None = None
        self._config = config.llm.local
        self._model_path = BASE_DIR / self._config.model_path

        # cargar system prompt
        prompt_path = BASE_DIR / "prompts" / "refine_system.txt"
        try:
            self.system_prompt = prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("system prompt no encontrado usando default")
            self.system_prompt = "eres un editor de texto experto"

    def _ensure_model_exists(self) -> None:
        """
        VERIFICA QUE EL ARCHIVO DEL MODELO EXISTE EN DISCO

        RAISES:
            LLMError: si el archivo gguf no existe con instrucciones de descarga
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
        CARGA EL MODELO EN VRAM

        si el modelo ya está cargado esta función no hace nada
        la carga es una operación costosa (~2-5 segundos) que debe
        hacerse una vez y reutilizarse

        RAISES:
            LLMError: si el archivo del modelo no existe
            RuntimeError: si hay problemas cargando el modelo en gpu
        """
        if self._model is not None:
            return  # ya cargado

        self._ensure_model_exists()
        logger.info(f"cargando modelo local: {self._model_path.name}")

        # import lazy para evitar error si llama-cpp-python no está instalado
        from llama_cpp import Llama

        self._model = Llama(
            model_path=str(self._model_path),
            n_gpu_layers=self._config.n_gpu_layers,
            n_ctx=self._config.n_ctx,
            verbose=False,
            chat_format="chatml",  # fallback si gguf no tiene metadata de chat
        )
        logger.info("✅ modelo local cargado en vram")

    def unload(self) -> None:
        """
        LIBERA EL MODELO DE VRAM INMEDIATAMENTE

        destruye la instancia del modelo y fuerza garbage collection
        para liberar la memoria cuda lo antes posible
        """
        if self._model is not None:
            logger.info("descargando modelo local de vram...")
            del self._model
            self._model = None
            # forzar liberación de memoria cuda
            gc.collect()
            logger.info("✅ vram liberada")

    @property
    def is_loaded(self) -> bool:
        """
        INDICA SI EL MODELO ESTÁ CARGADO EN VRAM

        RETURNS:
            True si el modelo está cargado y listo para inferencia
        """
        return self._model is not None

    @asynccontextmanager
    async def loaded(self) -> AsyncIterator[None]:
        """
        CONTEXT MANAGER ASYNC PARA HOT-SWAP DE VRAM

        carga el modelo al entrar y lo descarga al salir útil para
        gpus con poca memoria donde no es viable mantener múltiples
        modelos cargados simultáneamente

        EXAMPLE:
            async with llm_service.loaded():
                result = await llm_service.process_text(text)
            # vram liberada automáticamente al salir

        NOTE:
            si prefieres mantener el modelo cargado para menor latencia
            llama a load() una vez al inicio y no uses este context manager

        YIELDS:
            None el modelo está disponible dentro del bloque
        """
        try:
            await asyncio.to_thread(self.load)
            yield
        finally:
            await asyncio.to_thread(self.unload)

    async def process_text(self, text: str) -> str:
        """
        PROCESA TEXTO USANDO EL MODELO LOCAL

        usa create_chat_completion() que aplica automáticamente la plantilla
        de chat correcta según los metadatos del gguf esto hace el código
        agnóstico al modelo funciona con qwen llama phi mistral sin
        cambiar una sola línea de python

        ARGS:
            text: el texto a procesar/refinar

        RETURNS:
            el texto procesado por el modelo

        RAISES:
            LLMError: si el modelo no existe o hay errores de inferencia
        """
        # lazy loading si no está cargado
        if self._model is None:
            await asyncio.to_thread(self.load)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": text},
        ]

        try:
            logger.info("procesando texto con modelo local...")

            # create_chat_completion lee la plantilla del gguf automáticamente
            # no hardcodeamos <|im_start|> ni ningún formato específico
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
