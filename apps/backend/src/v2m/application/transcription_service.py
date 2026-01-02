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
MÓDULO QUE DEFINE LA INTERFAZ PARA LOS SERVICIOS DE TRANSCRIPCIÓN DE AUDIO

esta clase abstracta establece el contrato que cualquier servicio de transcripción
debe seguir la capa de aplicación interactúa con esta interfaz permitiendo
que la implementación subyacente ej `whispertranscriptionservice` pueda ser
intercambiada sin afectar la lógica de negocio
"""

from abc import ABC, abstractmethod


class TranscriptionService(ABC):
    """
    CLASE BASE ABSTRACTA PARA LOS SERVICIOS DE TRANSCRIPCIÓN

    define las operaciones esenciales para la grabación y transcripción de audio
    """

    @abstractmethod
    def start_recording(self) -> None:
        """
        INICIA EL PROCESO DE GRABACIÓN DE AUDIO DESDE EL DISPOSITIVO DE ENTRADA
        """
        raise NotImplementedError

    @abstractmethod
    def stop_and_transcribe(self) -> str:
        """
        DETIENE LA GRABACIÓN ACTUAL Y PROCESA EL AUDIO PARA OBTENER UNA TRANSCRIPCIÓN

        RETURNS:
            el texto transcrito del audio grabado
        """
        raise NotImplementedError
