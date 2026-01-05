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
Interfaces abstractas para los adaptadores del sistema.

Este módulo define las interfaces (puertos) que deben implementar los
adaptadores de infraestructura para interactuar con el sistema operativo.
Siguiendo el Principio de Inversión de Dependencias (DIP), la capa de aplicación
depende de estas abstracciones y no de implementaciones concretas.

Interfaces definidas:
    - ``ClipboardInterface``: Operaciones del portapapeles del sistema.
    - ``NotificationInterface``: Envío de notificaciones al escritorio.

Patrón utilizado:
    Estas interfaces forman parte del patrón Puertos y Adaptadores (Hexagonal).
    Los puertos están aquí y los adaptadores están en
    ``infrastructure/linux_adapters.py``.

Ejemplo:
    Inyección de dependencias en un handler:

    ```python
    class MyHandler:
        def __init__(self, clipboard: ClipboardInterface):
            self.clipboard = clipboard

        def execute(self, text: str):
            self.clipboard.copy(text)
    ```
"""

from abc import ABC, abstractmethod


class ClipboardInterface(ABC):
    """
    Interfaz abstracta para operaciones del portapapeles del sistema.

    Define el contrato que deben cumplir los adaptadores de portapapeles
    para diferentes sistemas operativos o entornos gráficos (X11, Wayland).

    Esta interfaz permite desacoplar la lógica de negocio de la implementación
    específica del portapapeles, facilitando pruebas unitarias y portabilidad.
    """

    @abstractmethod
    def copy(self, text: str) -> None:
        """
        Copia el texto proporcionado al portapapeles del sistema.

        Args:
            text: El texto a copiar al portapapeles.

        Nota:
            La implementación debe manejar correctamente caracteres Unicode
            y saltos de línea.
        """
        pass

    @abstractmethod
    def paste(self) -> str:
        """
        Obtiene el contenido actual del portapapeles del sistema.

        Returns:
            str: El texto contenido en el portapapeles. Retorna una cadena vacía
            si el portapapeles está vacío o contiene datos no textuales.
        """
        pass


class NotificationInterface(ABC):
    """
    Interfaz abstracta para el sistema de notificaciones del escritorio.

    Define el contrato para enviar notificaciones visuales al usuario.
    Las implementaciones pueden utilizar diferentes backends según el
    entorno (notify-send en Linux, Toast en Windows, etc.).
    """

    @abstractmethod
    def notify(self, title: str, message: str) -> None:
        """
        Envía una notificación visual al escritorio del usuario.

        Args:
            title: El título de la notificación.
            message: El cuerpo del mensaje de la notificación.

        Nota:
            Las implementaciones deben manejar silenciosamente los errores
            (ej. si notify-send no está instalado) para no interrumpir
            el flujo principal de la aplicación.
        """
        pass
