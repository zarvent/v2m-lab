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
Clase Base Abstracta para Comandos del Patrón CQRS.

Este módulo define la clase base `Command` de la cual heredan todos los
comandos específicos de la aplicación. En el patrón CQRS (Command Query
Responsibility Segregation), un comando representa la intención imperativa
de realizar una acción o modificar el estado del sistema.

Características de los comandos:
    - Representan acciones ("Hacer algo"), no consultas ("Deme datos").
    - Son objetos de transferencia de datos (DTOs), idealmente inmutables.
    - No contienen lógica de negocio, solo los datos necesarios para la acción.
    - Son procesados por exactamente un `CommandHandler`.

Ejemplo de definición:
    ```python
    class EnviarEmailCommand(Command):
        def __init__(self, destinatario: str, asunto: str):
            self.destinatario = destinatario
            self.asunto = asunto
    ```
"""

from abc import ABC


class Command(ABC):
    """
    Clase base abstracta (Marker Interface) para todos los comandos.

    Todos los comandos específicos (ej. `StartRecordingCommand`,
    `StopRecordingCommand`) deben heredar de esta clase. Esto garantiza
    un contrato común para el sistema de tipos y permite el despacho
    polimórfico a través del `CommandBus`.
    """

    pass
