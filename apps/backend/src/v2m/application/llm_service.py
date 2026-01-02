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
MÓDULO QUE DEFINE LA INTERFAZ PARA LOS SERVICIOS DE MODELOS DE LENGUAJE GRANDES LLM

esta clase abstracta define el contrato que cualquier servicio de llm debe
cumplir para ser utilizado por la aplicación la capa de aplicación depende de
esta abstracción no de una implementación concreta como `geminillmservice`
"""

from abc import ABC, abstractmethod


class LLMService(ABC):
    """
    CLASE BASE ABSTRACTA PARA LOS SERVICIOS DE MODELOS DE LENGUAJE

    define las operaciones que se pueden realizar con un llm como procesar texto
    """

    @abstractmethod
    async def process_text(self, text: str) -> str:
        """
        PROCESA Y REFINA UN BLOQUE DE TEXTO UTILIZANDO EL LLM

        ARGS:
            text: el texto de entrada a procesar

        RETURNS:
            el texto procesado y refinado por el llm
        """
        raise NotImplementedError
