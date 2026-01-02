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
interfaz base para los manejadores de comandos (command handlers)

este módulo define la clase abstracta ``CommandHandler`` que establece el
contrato que deben cumplir todos los handlers de comandos en la aplicación

en el patrón cqrs un handler es el componente que contiene la lógica de
negocio para procesar un tipo específico de comando cada handler

    - se suscribe a exactamente un tipo de comando
    - es invocado por el ``CommandBus`` cuando llega un comando de su tipo
    - coordina los servicios de dominio e infraestructura necesarios

responsabilidades de un handler
    - validar los datos del comando (si es necesario)
    - orquestar llamadas a servicios de dominio e infraestructura
    - manejar errores y traducirlos a respuestas apropiadas
    - no contener lógica de dominio compleja (delegarla a servicios)

example
    implementación de un handler::

        class EnviarEmailHandler(CommandHandler):
            def __init__(self, email_service: EmailService):
                self.email_service = email_service

            async def handle(self, command: EnviarEmailCommand) -> None:
                await self.email_service.enviar(
                    command.destinatario,
                    command.asunto
                )

            def listen_to(self) -> Type[Command]:
                return EnviarEmailCommand
"""

from abc import ABC, abstractmethod

from .command import Command


class CommandHandler(ABC):
    """
    clase base abstracta para los manejadores de comandos

    todos los handlers de la aplicación deben heredar de esta clase e
    implementar los métodos abstractos ``handle()`` y ``listen_to()``

    el ciclo de vida de un handler es
        1 se instancia durante la configuración (con dependencias inyectadas)
        2 se registra en el ``CommandBus``
        3 es invocado cada vez que llega un comando de su tipo

    note
        los handlers deben ser stateless o manejar su estado de forma
        thread-safe ya que pueden ser invocado concurrentemente
    """

    @abstractmethod
    async def handle(self, command: Command) -> None:
        """
        procesa el comando ejecutando la lógica de negocio correspondiente

        este método es invocado por el ``CommandBus`` cuando un comando del
        tipo apropiado es despachado debe coordinar las operaciones necesarias
        utilizando los servicios inyectados en el constructor

        args:
            command: la instancia del comando a procesar el tipo concreto
                corresponde al tipo retornado por ``listen_to()``

        note:
            este método es asíncrono para soportar operaciones i/o bound
            (llamadas a apis acceso a disco etc) sin bloquear

        raises:
            puede lanzar excepciones de dominio (``ApplicationError`` y
            subclases) que serán capturadas por el daemon y convertidas
            en respuestas de error apropiadas
        """
        raise NotImplementedError

    def listen_to(self) -> type[Command]:
        """
        especifica a qué tipo de comando se suscribe este handler

        el ``CommandBus`` utiliza este método durante el registro para
        construir el mapeo tipo-de-comando -> handler cuando un comando
        es despachado el bus consulta este mapeo para determinar qué
        handler debe procesarlo

        returns:
            el tipo (clase) del comando que este handler puede procesar
            por ejemplo ``StartRecordingCommand`` (la clase no una instancia)

        example
            implementación típica::

                def listen_to(self) -> Type[Command]:
                    return MiComandoEspecifico
        """
        raise NotImplementedError
