
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



class Command:
    """
    Clase base abstracta (Marker Interface) para todos los comandos.

    Todos los comandos específicos (ej. `StartRecordingCommand`,
    `StopRecordingCommand`) deben heredar de esta clase. Esto garantiza
    un contrato común para el sistema de tipos y permite el despacho
    polimórfico a través del `CommandBus`.
    """

    pass
