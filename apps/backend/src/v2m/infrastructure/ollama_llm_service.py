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
Ollama LLM Service with Structured Outputs (SOTA 2026).

This module implements the LLMService interface using Ollama as the backend.
It leverages structured outputs via JSON schema to ensure reliable, parseable
responses for text refinement tasks.

Key features:
- AsyncClient for non-blocking inference
- format=JSON schema forces valid structured responses
- options.keep_alive for VRAM management on consumer GPUs
- tenacity retry for resilience against transient failures
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
    LLM Service using Ollama with Structured Outputs.

    Implements the LLMService interface for text refinement using local
    Ollama models. Uses JSON schema constraints (format parameter) to
    guarantee parseable responses.

    Attributes:
        system_prompt: System instruction for the model.

    Example:
        Basic usage::

            service = OllamaLLMService()
            result = await service.process_text("texto a corregir")
    """

    def __init__(self) -> None:
        """Initialize the Ollama LLM Service."""
        self._config = config.llm.ollama
        self._client = AsyncClient(host=self._config.host)

        # Load system prompt
        prompt_path = BASE_DIR / "prompts" / "refine_system.txt"
        try:
            self.system_prompt = prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("system prompt not found, using default")
            self.system_prompt = "Eres un editor experto. Corrige gramática y coherencia del texto."

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, ConnectionError)),
        reraise=True,
    )
    async def process_text(self, text: str) -> str:
        """
        Process text using Ollama with Structured Outputs.

        Uses the format parameter with a JSON schema derived from the
        CorrectionResult Pydantic model to force valid, structured responses.

        Args:
            text: The text to process/refine.

        Returns:
            The corrected text extracted from the structured response.

        Raises:
            LLMError: If Ollama connection fails or response is invalid.
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

            # Parse structured JSON response
            result = CorrectionResult.model_validate_json(response.message.content)
            logger.info("✅ procesamiento con ollama completado")
            return result.corrected_text

        except httpx.ConnectError as e:
            logger.error(f"no se pudo conectar a ollama en {self._config.host}: {e}")
            raise LLMError(f"ollama no disponible en {self._config.host}") from e
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
        Translate text using Ollama.

        Args:
            text: The text to translate.
            target_lang: Target language code.

        Returns:
            The translated text.

        Raises:
            LLMError: If translation fails.
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
