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
interfaces abstractas para los adaptadores del sistema

este módulo define las interfaces (puertos) que deben implementar los
adaptadores de infraestructura para interactuar con el sistema operativo
siguiendo el principio de inversión de dependencias la capa de aplicación
depende de estas abstracciones y no de implementaciones concretas

interfaces definidas
    - ``ClipboardInterface`` operaciones del portapapeles del sistema
    - ``NotificationInterface`` envío de notificaciones al escritorio

patrón utilizado
    estas interfaces forman parte del patrón ports and adapters (hexagonal)
    los puertos están aquí y los adaptadores están en
    ``infrastructure/linux_adapters.py``

example
    inyección de dependencias en un handler::

        class MyHandler:
            def __init__(self, clipboard: ClipboardInterface):
                self.clipboard = clipboard

            def execute(self, text: str):
                self.clipboard.copy(text)
"""

from abc import ABC, abstractmethod


class ClipboardInterface(ABC):
    """
    interfaz abstracta para operaciones del portapapeles del sistema

    define el contrato que deben cumplir los adaptadores de portapapeles
    para diferentes sistemas operativos o entornos gráficos (x11 wayland)

    esta interfaz permite desacoplar la lógica de negocio de la implementación
    específica del portapapeles facilitando pruebas unitarias y portabilidad

    example
        implementación mock para pruebas::

            class MockClipboard(ClipboardInterface):
                def __init__(self):
                    self._content = ""

                def copy(self, text: str) -> None:
                    self._content = text

                def paste(self) -> str:
                    return self._content
    """
    @abstractmethod
    def copy(self, text: str) -> None:
        """
        copia el texto proporcionado al portapapeles del sistema

        el texto se almacena en el portapapeles y estará disponible para
        pegar en cualquier aplicación hasta que sea reemplazado por otro
        contenido

        args:
            text: el texto a copiar al portapapeles debe ser una cadena
                válida las cadenas vacías pueden ser ignoradas por algunas
                implementaciones

        note:
            la implementación debe manejar correctamente caracteres unicode
            y saltos de línea
        """
        pass

    @abstractmethod
    def paste(self) -> str:
        """
        obtiene el contenido actual del portapapeles del sistema

        lee y retorna el texto actualmente almacenado en el portapapeles
        si el portapapeles contiene datos no textuales (imágenes archivos)
        el comportamiento depende de la implementación

        returns:
            el texto contenido en el portapapeles retorna una cadena vacía
            si el portapapeles está vacío o contiene datos no textuales

        raises:
            puede lanzar excepciones específicas de la implementación si
            hay problemas de acceso al portapapeles del sistema
        """
        pass

class NotificationInterface(ABC):
    """
    interfaz abstracta para el sistema de notificaciones del escritorio

    define el contrato para enviar notificaciones visuales al usuario
    las implementaciones pueden utilizar diferentes backends según el
    entorno (notify-send en linux toast en windows etc)

    las notificaciones son utilizadas para informar al usuario sobre el
    estado de las operaciones (grabación iniciada transcripción completada
    errores etc)

    example
        implementación mock para pruebas::

            class MockNotification(NotificationInterface):
                def __init__(self):
                    self.notifications = []

                def notify(self, title: str, message: str) -> None:
                    self.notifications.append((title, message))
    """
    @abstractmethod
    def notify(self, title: str, message: str) -> None:
        """
        envía una notificación visual al escritorio del usuario

        muestra un mensaje emergente utilizando el sistema de notificaciones
        del entorno de escritorio la notificación aparece brevemente y
        luego desaparece automáticamente

        args:
            title: el título de la notificación debe ser breve y descriptivo
                ejemplos "grabando" "copiado" "error"
            message: el cuerpo del mensaje de la notificación puede incluir
                más detalles sobre la operación se recomienda limitar a
                80-100 caracteres para mejor legibilidad

        note:
            las implementaciones deben manejar silenciosamente los errores
            (ej si notify-send no está instalado) para no interrumpir
            el flujo principal de la aplicación
        """
        pass
