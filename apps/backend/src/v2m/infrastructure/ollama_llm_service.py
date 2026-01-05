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
Servicio LLM Ollama con Salidas Estructuradas (State of the Art 2026).

Este módulo implementa la interfaz `LLMService` utilizando Ollama como backend.
Aprovecha las salidas estructuradas mediante JSON schema para garantizar
respuestas fiables y analizables para tareas de refinamiento de texto.

Características clave:
- `AsyncClient` para inferencia no bloqueante.
- `format=JSON schema` fuerza respuestas estructuradas válidas.
- `options.keep_alive` gestiona la carga de VRAM en GPUs de consumidor.
- Reintentos con `tenacity` para resiliencia contra fallos transitorios.
"""

from __future__ import annotations

import httpx
from ollama import AsyncClient
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from v2m.application.llm_service import LLMService
from v2m.config import BASE_DIR, config
from v2m.core.logging import logger
from v2m.domain.errors import LLMError
from v2m.domain.ports import CorrectionResult


class OllamaLLMService(LLMService):
    """
    Servicio LLM utilizando Ollama con Salidas Estructuradas.

    Implementa la interfaz `LLMService` para el refinamiento de texto utilizando
    modelos locales de Ollama. Utiliza restricciones de JSON schema (parámetro `format`)
    para garantizar respuestas parseables.

    Atributos:
        system_prompt: Instrucción del sistema para el modelo.
    """

    def __init__(self) -> None:
        """Inicializa el servicio LLM de Ollama."""
        self._config = config.llm.ollama
        self._client = AsyncClient(host=self._config.host)

        # Cargar prompt del sistema
        prompt_path = BASE_DIR / "prompts" / "refine_system.txt"
        try:
            self.system_prompt = prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("prompt del sistema no encontrado, usando valor por defecto")
            self.system_prompt = "Eres un editor experto. Corrige gramática y coherencia del texto."

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, ConnectionError)),
        reraise=True,
    )
    async def process_text(self, text: str) -> str:
        """
        Procesa texto utilizando Ollama con Salidas Estructuradas.

        Utiliza el parámetro `format` con un esquema JSON derivado del modelo
        Pydantic `CorrectionResult` para forzar respuestas estructuradas válidas.

        Args:
            text: El texto a procesar/refinar.

        Returns:
            str: El texto corregido extraído de la respuesta estructurada.

        Raises:
            LLMError: Si la conexión a Ollama falla o la respuesta es inválida.
        """
        try:
            logger.info(f"procesando texto con ollama ({self._config.model})...")

            response = await self._client.chat(
                model=self._config.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text},
                ],
                format=CorrectionResult.model_json_schema(),
                options={
                    "temperature": self._config.temperature,
                    "keep_alive": self._config.keep_alive,
                },
            )

            # Parsear respuesta JSON estructurada
            result = CorrectionResult.model_validate_json(response.message.content)
            logger.info("✅ procesamiento con ollama completado")
            return result.corrected_text

        except httpx.ConnectError as e:
            logger.error(f"no se pudo conectar a ollama en {self._config.host}: {e}")
            raise LLMError(f"Ollama no disponible en {self._config.host}") from e
        except Exception as e:
            logger.error(f"error procesando texto con ollama: {e}")
            raise LLMError(f"falló el procesamiento con ollama: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, ConnectionError)),
        reraise=True,
    )
    async def translate_text(self, text: str, target_lang: str) -> str:
        """
        Traduce texto utilizando Ollama.

        Args:
            text: El texto a traducir.
            target_lang: Código de idioma destino.

        Returns:
            str: El texto traducido.

        Raises:
            LLMError: Si la traducción falla.
        """
        try:
            logger.info(f"traduciendo texto a {target_lang} con ollama...")

            system_instruction = (
                f"Eres un traductor experto. Traduce el siguiente texto al idioma '{target_lang}'. "
                "Devuelve SOLO el texto traducido, sin explicaciones ni notas adicionales."
            )

            response = await self._client.chat(
                model=self._config.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": text},
                ],
                options={
                    "temperature": self._config.translation_temperature,
                    "keep_alive": self._config.keep_alive,
                },
            )

            logger.info("✅ traducción con ollama completada")
            return response.message.content.strip()

        except Exception as e:
            logger.error(f"error traduciendo con ollama: {e}")
            raise LLMError(f"falló la traducción con ollama: {e}") from e
