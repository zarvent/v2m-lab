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
MÓDULO QUE IMPLEMENTA EL SERVICIO DE LLM UTILIZANDO LA API DE GOOGLE GEMINI

esta es una implementación concreta de la interfaz `llmservice` es responsable
de toda la lógica de comunicación con el servicio de google gemini incluyendo
la autenticación la construcción de la solicitud y el manejo de reintentos
"""

import os

import httpx
from google import genai
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from v2m.application.llm_service import LLMService
from v2m.config import BASE_DIR, config
from v2m.core.logging import logger
from v2m.domain.errors import LLMError


class GeminiLLMService(LLMService):
    """
    IMPLEMENTACIÓN DEL `LLMSERVICE` QUE SE CONECTA CON GOOGLE GEMINI

    gestiona la configuración del cliente de la api la formulación de las
    peticiones y la lógica de reintentos para asegurar una comunicación robusta
    """
    def __init__(self) -> None:
        """
        INICIALIZA EL SERVICIO DE GOOGLE GEMINI

        este constructor realiza las siguientes acciones
        1 obtiene la configuración y la api key desde `config.py` (pydantic settings)
        2 configura e instancia el cliente de la api de google
        3 almacena los parámetros del modelo y la configuración de reintentos

        RAISES:
            LLMError: si la `GEMINI_API_KEY` no se encuentra en la configuración
        """
        # --- carga de configuración y secretos ---
        gemini_config = config.gemini
        api_key = gemini_config.api_key

        if not api_key:
            raise LLMError("la variable de entorno GEMINI_API_KEY no fue encontrada")

        # --- inicialización del cliente de la api ---
        # la librería de google utiliza `GOOGLE_API_KEY` por defecto
        os.environ["GOOGLE_API_KEY"] = api_key
        self.client = genai.Client(api_key=api_key)
        self.model = gemini_config.model
        self.temperature = gemini_config.temperature
        self.max_tokens = gemini_config.max_tokens

        # cargar prompt del sistema
        prompt_path = BASE_DIR / "prompts" / "refine_system.txt"
        try:
            with open(prompt_path, encoding="utf-8") as f:
                self.system_instruction = f.read()
        except FileNotFoundError:
            logger.warning("prompt del sistema no encontrado usando default")
            self.system_instruction = "eres un editor de texto experto"

    # retry solo para errores transitorios de red rate-limit
    # tiempos reducidos para baja latencia 0.5s 1s 2s (máx 3.5s total)
    @retry(
        stop=stop_after_attempt(config.gemini.retry_attempts),
        wait=wait_exponential(
            multiplier=0.5,  # reducido de 1
            min=0.5,         # reducido de 2
            max=2,           # reducido de 10
        ),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, ConnectionError)),
        reraise=True,  # re-lanzar si se agotan los intentos
    )
    async def process_text(self, text: str) -> str:
        """
        PROCESA UN TEXTO UTILIZANDO EL MODELO DE GOOGLE GEMINI

        implementa una estrategia de reintentos con `tenacity` para manejar
        errores transitorios de red o de la api de forma resiliente

        ARGS:
            text: el texto a procesar

        RETURNS:
            el texto refinado por el llm

        RAISES:
            LLMError: si la comunicación con la api falla después de todos los reintentos
        """
        try:
            logger.info("procesando texto con gemini...")
            generation_config = {
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                "system_instruction": self.system_instruction,
            }

            # --- construcción del payload para la api ---
            contents = [
                genai.types.Content(
                    role="user",
                    parts=[genai.types.Part(text=text)]
                )
            ]

            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=generation_config
            )
            logger.info("procesamiento con gemini completado")
            if response.text:
                return response.text.strip()
            else:
                raise LLMError("respuesta vacía de gemini")
        except Exception as e:
            # --- manejo de errores ---
            # se captura cualquier excepción de la librería de google o de red
            # y se relanza como un error de dominio para no filtrar detalles
            # de la infraestructura a la capa de aplicación
            error_msg = str(e)
            if "API key not valid" in error_msg:
                logger.critical("GEMINI_API_KEY inválida o expirada")
                raise LLMError("api key de gemini inválida revisa tu archivo .env") from e

            logger.error(f"error procesando texto con gemini {e}")
            raise LLMError("falló el procesamiento de texto con gemini") from e
