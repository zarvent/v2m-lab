"""Implementación del Servicio LLM utilizando la API de Google Gemini.

Esta es una implementación concreta de la interfaz `LLMService`. Es responsable
de toda la lógica de comunicación con el servicio de Google Gemini, incluyendo
la autenticación, la construcción de la solicitud y el manejo de reintentos
para resiliencia ante fallos transitorios.
"""

import os

import httpx
from google import genai
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from v2m.features.llm.service import LLMService
from v2m.shared.config import BASE_DIR, config
from v2m.shared.logging import logger
from v2m.shared.errors import LLMError


class GeminiLLMService(LLMService):
    """Implementación del `LLMService` que se conecta con Google Gemini.

    Gestiona la configuración del cliente de la API, la formulación de las
    peticiones y la lógica de reintentos para asegurar una comunicación robusta.
    """

    def __init__(self) -> None:
        """Inicializa el servicio de Google Gemini.

        Acciones del constructor:
        1. Obtiene la configuración y la API Key desde `config.py` (Pydantic Settings).
        2. Configura e instancia el cliente de la API de Google.
        3. Almacena los parámetros del modelo y la configuración de reintentos.

        Raises:
            LLMError: Si la variable `GEMINI_API_KEY` no se encuentra en la configuración.
        """
        # --- Carga de configuración y secretos ---
        gemini_config = config.gemini
        api_key = gemini_config.api_key

        if not api_key:
            raise LLMError("La variable de entorno GEMINI_API_KEY no fue encontrada")

        # --- Inicialización del cliente de la API ---
        # La librería de Google utiliza `GOOGLE_API_KEY` por defecto
        os.environ["GOOGLE_API_KEY"] = api_key
        self.client = genai.Client(api_key=api_key)
        self.model = gemini_config.model
        self.temperature = gemini_config.temperature
        self.max_tokens = gemini_config.max_tokens

        # Cargar prompt del sistema
        prompt_path = BASE_DIR / "prompts" / "refine_system.txt"
        try:
            with open(prompt_path, encoding="utf-8") as f:
                self.system_instruction = f.read()
        except FileNotFoundError:
            logger.warning("prompt del sistema no encontrado, usando valor por defecto")
            self.system_instruction = "Eres un editor de texto experto."

    # Estrategia de reintentos para errores transitorios de red (rate-limit, timeout).
    # Tiempos reducidos para baja latencia: 0.5s, 1s, 2s (máx 3.5s total).
    @retry(
        stop=stop_after_attempt(config.gemini.retry_attempts),
        wait=wait_exponential(
            multiplier=0.5,
            min=0.5,
            max=2,
        ),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, ConnectionError)),
        reraise=True,  # Re-lanzar la excepción si se agotan los intentos
    )
    async def process_text(self, text: str) -> str:
        """Procesa un texto utilizando el modelo de Google Gemini.

        Implementa una estrategia de reintentos con `tenacity` para manejar
        errores transitorios de red o de la API de forma resiliente.

        Args:
            text: El texto a procesar.

        Returns:
            str: El texto refinado por el LLM.

        Raises:
            LLMError: Si la comunicación con la API falla después de todos los reintentos.
        """
        try:
            logger.info("procesando texto con gemini...")
            generation_config = {
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                "system_instruction": self.system_instruction,
            }

            # --- Construcción del payload para la API ---
            contents = [genai.types.Content(role="user", parts=[genai.types.Part(text=text)])]

            response = await self.client.aio.models.generate_content(
                model=self.model, contents=contents, config=generation_config
            )
            logger.info("procesamiento con gemini completado")
            if response.text:
                return response.text.strip()
            else:
                raise LLMError("respuesta vacía de gemini")
        except Exception as e:
            # --- Manejo de errores ---
            # Se captura cualquier excepción de la librería de Google o de red
            # y se relanza como un error de dominio para no filtrar detalles
            # de la infraestructura a la capa de aplicación.
            error_msg = str(e)
            if "API key not valid" in error_msg:
                logger.critical("GEMINI_API_KEY inválida o expirada")
                raise LLMError("API Key de Gemini inválida, revisa tu archivo .env") from e

            logger.error(f"error procesando texto con gemini: {e}")
            raise LLMError("falló el procesamiento de texto con gemini") from e

    @retry(
        stop=stop_after_attempt(config.gemini.retry_attempts),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, ConnectionError)),
        reraise=True,
    )
    async def translate_text(self, text: str, target_lang: str) -> str:
        """Traduce un texto utilizando el modelo de Google Gemini.

        Args:
            text: El texto a traducir.
            target_lang: Idioma objetivo (ej. "es", "en", "fr").

        Returns:
            str: El texto traducido.
        """
        try:
            logger.info(f"traduciendo texto a {target_lang} con gemini...")

            # Prompt de sistema específico para traducción
            system_instruction = (
                f"Eres un traductor experto. Traduce el siguiente texto al idioma '{target_lang}'. "
                "Devuelve SOLO el texto traducido, sin explicaciones ni notas adicionales."
            )

            generation_config = {
                "temperature": config.gemini.translation_temperature,
                "max_output_tokens": self.max_tokens,
                "system_instruction": system_instruction,
            }

            contents = [genai.types.Content(role="user", parts=[genai.types.Part(text=text)])]

            response = await self.client.aio.models.generate_content(
                model=self.model, contents=contents, config=generation_config
            )
            logger.info("traducción con gemini completada")
            if response.text:
                return response.text.strip()
            else:
                raise LLMError("respuesta vacía de gemini en traducción")
        except Exception as e:
            error_msg = str(e)
            if "API key not valid" in error_msg:
                logger.critical("GEMINI_API_KEY inválida o expirada")
                raise LLMError("API Key de Gemini inválida") from e

            logger.error(f"error traduciendo texto con gemini: {e}")
            raise LLMError("falló la traducción con gemini") from e
