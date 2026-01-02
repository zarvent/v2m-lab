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
implementación del bus de comandos para el patrón cqrs

el ``CommandBus`` es el orquestador central del sistema de comandos su
responsabilidad es recibir objetos ``Command`` y despacharlos al
``CommandHandler`` apropiado que ha sido registrado previamente

beneficios del patrón
    - **desacoplamiento** el emisor del comando no conoce al receptor
    - **extensibilidad** nuevos comandos se agregan sin modificar código existente
    - **testabilidad** los handlers pueden probarse de forma aislada
    - **trazabilidad** fácil agregar logging/métricas en un punto central

arquitectura
    ::

        Cliente -> CommandBus -> Handler -> Servicios
                      |
                      +-- Registro de handlers (Dict[Type[Command], Handler])

example
    configuración y uso básico::

        from v2m.core.cqrs.command_bus import CommandBus

        bus = CommandBus()
        bus.register(mi_handler)

        await bus.dispatch(MiComando(datos="valor"))
"""

from typing import Any

from .command import Command
from .command_handler import CommandHandler


class CommandBus:
    """
    despacha comandos a sus respectivos handlers registrados

    actúa como un mediador (patrón mediator) que mantiene un mapeo entre
    tipos de comando y las instancias de handlers que pueden procesarlos

    attributes:
        handlers: diccionario que mapea tipos de ``Command`` a instancias
            de ``CommandHandler`` cada tipo de comando tiene exactamente
            un handler asociado

    example
        flujo completo de configuración::

            bus = CommandBus()

            # registrar handlers (normalmente hecho en el contenedor di)
            bus.register(StartRecordingHandler(transcription_service))
            bus.register(StopRecordingHandler(transcription_service))

            # despachar comandos (en tiempo de ejecución)
            await bus.dispatch(StartRecordingCommand())
    """

    def __init__(self) -> None:
        """
        inicializa el bus de comandos con un registro vacío de handlers

        el diccionario de handlers se pobla mediante llamadas sucesivas
        al método ``register()`` durante la fase de inicialización de
        la aplicación (normalmente en el contenedor de di)
        """
        self.handlers: dict[type[Command], CommandHandler] = {}

    def register(self, handler: CommandHandler) -> None:
        """
        registra un handler de comandos en el bus

        asocia el tipo de comando (obtenido de ``handler.listen_to()``) con
        la instancia del handler este método se llama durante la fase de
        configuración de la aplicación

        args:
            handler: instancia del handler a registrar debe implementar
                ``CommandHandler`` y retornar el tipo de comando que
                maneja en su método ``listen_to()``

        raises:
            ValueError: si ya existe un handler registrado para el mismo
                tipo de comando cada comando debe tener exactamente un
                handler

        example
            registro típico en el contenedor::

                bus = CommandBus()
                bus.register(StartRecordingHandler(deps))
                bus.register(StopRecordingHandler(deps))
        """
        command_type = handler.listen_to()
        if command_type in self.handlers:
            raise ValueError(f"Ya existe un handler registrado para el comando {command_type}")
        self.handlers[command_type] = handler

    async def dispatch(self, command: Command) -> Any:
        """
        despacha un comando a su handler correspondiente

        este es el método principal utilizado en tiempo de ejecución busca
        el handler apropiado basado en el tipo del comando y delega la
        ejecución al método ``handle()`` del handler

        args:
            command: instancia del comando a despachar el tipo del comando
                determina qué handler será invocado

        returns:
            el resultado de la ejecución del método ``handle()`` del handler
            el tipo de retorno depende de la implementación del handler
            específico (generalmente ``None`` para comandos)

        raises:
            ValueError: si no hay ningún handler registrado para el tipo
                de comando proporcionado

        example
            despachar comandos en el daemon::

                if message == IPCCommand.START_RECORDING:
                    await bus.dispatch(StartRecordingCommand())
                elif message == IPCCommand.STOP_RECORDING:
                    await bus.dispatch(StopRecordingCommand())
        """
        command_type = type(command)
        if command_type not in self.handlers:
            raise ValueError(f"No hay un handler registrado para el comando {command_type}")
        return await self.handlers[command_type].handle(command)
