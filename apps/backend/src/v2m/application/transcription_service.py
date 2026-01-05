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
Protocolo de Servicio de Transcripción.

Define la interfaz (Protocol) que deben implementar los servicios de transcripción
(como Whisper). Utiliza `typing.Protocol` para tipado estructural, desacoplando
completamente la implementación de la abstracción.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class TranscriptionService(Protocol):
    """
    Protocolo que define las operaciones de grabación y transcripción.
    """

    def start_recording(self) -> None:
        """
        Inicia el proceso de grabación de audio de forma asíncrona (non-blocking)
        o en un hilo separado.
        """
        ...

    def stop_and_transcribe(self) -> str:
        """
        Detiene la grabación activa y procesa el audio para generar texto.

        Returns:
            str: El texto transcrito.

        Raises:
            RecordingError: Si ocurre un error durante la captura o procesamiento.
        """
        ...
