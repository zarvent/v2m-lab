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
Puertos del Dominio (Modelos de Datos).

Este módulo define modelos Pydantic utilizados para estructurar las salidas
de los proveedores de LLM que soportan restricciones de esquema JSON (ej. Ollama).
Asegura que la interacción con el dominio sea tipada y predecible.
"""

from pydantic import BaseModel, Field


class CorrectionResult(BaseModel):
    """
    Modelo de salida estructurada para refinamiento de texto.

    Este modelo fuerza a los LLMs a responder en un formato JSON predecible,
    facilitando el parsing y reduciendo alucinaciones de formato.

    Atributos:
        corrected_text: Versión refinada y corregida del texto.
        explanation: Explicación opcional de los cambios (útil para depuración).
    """

    corrected_text: str = Field(description="Texto corregido con gramática y coherencia mejoradas")
    explanation: str | None = Field(default=None, description="Cambios realizados al texto original")
