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
Interfaces (Protocolos) para los adaptadores del sistema.

Este módulo define los contratos que deben cumplir los adaptadores de infraestructura
para interactuar con el sistema operativo (Clipboard, Notificaciones).
Siguiendo las mejores prácticas de 2026, utilizamos `typing.Protocol` para definir
estas interfaces, permitiendo un tipado estructural flexible y desacoplado.

Interfaces definidas:
    - ``ClipboardInterface``: Operaciones del portapapeles.
    - ``NotificationInterface``: Envío de notificaciones al escritorio.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ClipboardInterface(Protocol):
    """
    Protocolo para operaciones del portapapeles del sistema.

    Define el contrato estructural para cualquier adaptador que gestione
    el portapapeles (X11, Wayland, Windows, macOS).
    """

    def copy(self, text: str) -> None:
        """
        Copia el texto proporcionado al portapapeles del sistema.

        Args:
            text: El texto a copiar.
        """
        ...

    def paste(self) -> str:
        """
        Obtiene el contenido actual del portapapeles del sistema.

        Returns:
            str: El texto contenido en el portapapeles.
        """
        ...


@runtime_checkable
class NotificationInterface(Protocol):
    """
    Protocolo para el sistema de notificaciones del escritorio.

    Define el contrato estructural para cualquier adaptador que envíe
    alertas visuales al usuario.
    """

    def notify(self, title: str, message: str) -> None:
        """
        Envía una notificación visual al escritorio del usuario.

        Args:
            title: El título de la notificación.
            message: El cuerpo del mensaje.
        """
        ...
