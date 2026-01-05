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
Protocolo de Servicio de Modelos de Lenguaje (LLM).

Define la interfaz (Protocol) para interactuar con proveedores de LLM
(Gemini, Ollama, Local). Garantiza que cualquier backend de LLM cumpla
con las operaciones requeridas por los casos de uso de la aplicación.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMService(Protocol):
    """
    Protocolo para servicios de procesamiento de lenguaje natural.
    """

    async def process_text(self, text: str) -> str:
        """
        Procesa y refina un bloque de texto (ej. corrección gramatical).

        Args:
            text: El texto original.

        Returns:
            str: El texto procesado/refinado.
        """
        ...

    async def translate_text(self, text: str, target_lang: str) -> str:
        """
        Traduce un bloque de texto al idioma especificado.

        Args:
            text: El texto original.
            target_lang: Código de idioma destino (ej. "en", "fr").

        Returns:
            str: El texto traducido.
        """
        ...
