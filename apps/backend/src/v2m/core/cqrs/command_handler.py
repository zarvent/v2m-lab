
"""
Interfaz base para los Manejadores de Comandos (Command Handlers).

Este módulo define la clase abstracta `CommandHandler` que establece el
contrato que deben cumplir todos los handlers de comandos en la aplicación.

En el patrón CQRS, un handler es el componente que contiene la lógica de
aplicación para procesar un tipo específico de comando.

Responsabilidades de un Handler:
    - Suscribirse a exactamente un tipo de comando.
    - Orquestar llamadas a servicios de dominio e infraestructura.
    - Manejar la interacción entre capas (Application -> Domain/Infrastructure).
    - No contener lógica de negocio compleja (delegarla al Dominio).

Ejemplo:
    ```python
    class EnviarEmailHandler(CommandHandler):
        def __init__(self, email_service: EmailService):
            self.email_service = email_service

        async def handle(self, command: EnviarEmailCommand) -> None:
            await self.email_service.enviar(
                command.destinatario,
                command.asunto
            )

        def listen_to(self) -> type[Command]:
            return EnviarEmailCommand
    ```
"""

from abc import ABC, abstractmethod

from .command import Command


class CommandHandler(ABC):
    """
    Clase base abstracta para los manejadores de comandos.

    Todos los handlers de la aplicación deben heredar de esta clase e
    implementar los métodos abstractos `handle()` y `listen_to()`.

    Nota:
        Los handlers deben ser stateless (sin estado) o manejar su estado de forma
        segura (thread-safe), ya que son instanciados como Singletons.
    """

    @abstractmethod
    async def handle(self, command: Command) -> None:
        """
        Procesa el comando ejecutando la lógica de aplicación correspondiente.

        Este método es invocado por el `CommandBus`. Debe coordinar las operaciones
        necesarias utilizando los servicios inyectados en el constructor.

        Args:
            command: La instancia del comando a procesar.

        Raises:
            Exception: Cualquier excepción será capturada por la capa superior
            (Daemon) y devuelta como error al cliente.
        """
        raise NotImplementedError

    def listen_to(self) -> type[Command]:
        """
        Especifica a qué tipo de comando se suscribe este handler.

        El `CommandBus` utiliza este método durante el registro para
        construir el enrutamiento.

        Returns:
            type[Command]: La Clase del comando que este handler puede procesar.
        """
        raise NotImplementedError
