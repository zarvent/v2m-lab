
"""
Implementación del Bus de Comandos para el Patrón CQRS.

El `CommandBus` es el orquestador central del sistema de comandos. Su
responsabilidad es recibir objetos `Command` y despacharlos al
`CommandHandler` apropiado que ha sido registrado previamente.

Beneficios del Patrón:
    - **Desacoplamiento**: El emisor del comando no conoce al receptor.
    - **Extensibilidad**: Nuevos comandos se agregan sin modificar código existente.
    - **Testabilidad**: Los handlers pueden probarse de forma aislada.
    - **Centralización**: Facilita agregar logging, métricas o validación en un solo punto.

Arquitectura:
    ```
    Cliente -> CommandBus -> Handler -> Servicios de Dominio
                   |
                   +-- Registro de Handlers (Map[Type[Command], Handler])
    ```
"""

from typing import Any

from .command import Command
from .command_handler import CommandHandler


class CommandBus:
    """
    Despachador de comandos (Mediator).

    Mantiene un registro de qué `CommandHandler` es responsable de qué `Command`
    y delega la ejecución en tiempo de ejecución.

    Atributos:
        handlers: Diccionario que mapea tipos de `Command` a instancias
            de `CommandHandler`.
    """

    def __init__(self) -> None:
        """
        Inicializa el bus de comandos.
        """
        self.handlers: dict[type[Command], CommandHandler] = {}

    def register(self, handler: CommandHandler) -> None:
        """
        Registra un handler de comandos en el bus.

        Asocia el tipo de comando (obtenido de `handler.listen_to()`) con
        la instancia del handler. Este método se llama durante la fase de
        configuración de la aplicación (Bootstrapping).

        Args:
            handler: Instancia del handler a registrar.

        Raises:
            ValueError: Si ya existe un handler registrado para ese comando.
                (Cada comando debe tener exactamente un handler).
        """
        command_type = handler.listen_to()
        if command_type in self.handlers:
            raise ValueError(f"Ya existe un handler registrado para el comando {command_type}")
        self.handlers[command_type] = handler

    async def dispatch(self, command: Command) -> Any:
        """
        Despacha un comando a su handler correspondiente.

        Busca el handler apropiado basado en el tipo del comando y ejecuta
        su lógica asíncronamente.

        Args:
            command: Instancia del comando a despachar.

        Returns:
            Any: El resultado de la ejecución del handler (depende de la implementación).

        Raises:
            ValueError: Si no hay ningún handler registrado para ese tipo de comando.
        """
        command_type = type(command)
        if command_type not in self.handlers:
            raise ValueError(f"No hay un handler registrado para el comando {command_type}")
        return await self.handlers[command_type].handle(command)
