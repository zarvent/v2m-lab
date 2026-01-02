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
clase base abstracta para comandos del patrón cqrs

este módulo define la clase base ``Command`` de la cual heredan todos los
comandos específicos de la aplicación en el patrón cqrs (command query
responsibility segregation) un comando representa la intención de modificar
el estado del sistema

características de los comandos
    - representan acciones no consultas
    - son objetos de datos inmutables (idealmente)
    - no contienen lógica de negocio solo datos
    - son procesados por exactamente un ``CommandHandler``

flujo de un comando
    1 se crea una instancia del comando con los datos necesarios
    2 se envía al ``CommandBus`` mediante ``dispatch()``
    3 el bus localiza el handler registrado para ese tipo de comando
    4 el handler ejecuta la lógica de negocio correspondiente

example
    definir un comando personalizado::

        from v2m.core.cqrs.command import Command

        class EnviarEmailCommand(Command):
            def __init__(self, destinatario: str, asunto: str):
                self.destinatario = destinatario
                self.asunto = asunto
"""

from abc import ABC


class Command(ABC):
    """
    clase base abstracta para todos los comandos de la aplicación

    todos los comandos específicos (ej ``StartRecordingCommand``
    ``StopRecordingCommand``) deben heredar de esta clase esto garantiza
    que todos los comandos sigan un contrato común y puedan ser despachados
    por el ``CommandBus``

    la clase es intencionalmente vacía (marker class) ya que su propósito
    es proporcionar un tipo base común para el sistema de tipos y el
    despacho polimórfico

    example
        comando sin datos adicionales::

            class PingCommand(Command):
                pass

        comando con datos::

            class CrearUsuarioCommand(Command):
                def __init__(self, nombre: str, email: str):
                    self.nombre = nombre
                    self.email = email
    """
    pass
