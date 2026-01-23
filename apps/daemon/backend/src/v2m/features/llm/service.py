"""Protocolo de Servicio de Modelos de Lenguaje (LLM).

Define la interfaz (Protocol) para interactuar con proveedores de LLM
(Gemini, Ollama, Local). Garantiza que cualquier backend de LLM cumpla
con las operaciones requeridas por los casos de uso de la aplicación.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMService(Protocol):
    """Protocolo para servicios de procesamiento de lenguaje natural."""

    async def process_text(self, text: str) -> str:
        """Procesa y refina un bloque de texto (ej. corrección gramatical).

        Args:
            text: El texto original.

        Returns:
            str: El texto procesado/refinado.
        """
        ...

    async def translate_text(self, text: str, target_lang: str) -> str:
        """Traduce un bloque de texto al idioma especificado.

        Args:
            text: El texto original.
            target_lang: Código de idioma destino (ej. "en", "fr").

        Returns:
            str: El texto traducido.
        """
        ...
