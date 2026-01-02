# cqrs

Implementación del patrón Command Query Responsibility Segregation (CQRS) para la gestión de acciones en el sistema.

## Componentes

- `command.py` - Clase base para todos los comandos (intenciones de cambio de estado)
- `command_bus.py` - Mediador que recibe comandos y los enruta al handler correspondiente
- `command_handler.py` - Interfaz base para la lógica que procesa un comando específico

## Flujo

1. El cliente envía una solicitud (ej. iniciar grabación)
2. Se crea un objeto `Command`
3. El `CommandBus` recibe el comando
4. El bus busca el `CommandHandler` registrado para ese comando
5. El handler ejecuta la lógica de negocio

## Beneficios

Desacopla quién invoca la acción de quién la ejecuta, permitiendo una arquitectura más limpia y testear cada parte aisladamente.
