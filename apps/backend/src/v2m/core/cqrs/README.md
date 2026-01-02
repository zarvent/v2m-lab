# cqrs

implementación del patrón command query responsibility segregation (cqrs) para la gestión de acciones en el sistema

componentes
- `command.py` clase base para todos los comandos (intenciones de cambio de estado)
- `command_bus.py` mediador que recibe comandos y los enruta al handler correspondiente
- `command_handler.py` interfaz base para la lógica que procesa un comando específico

flujo
1 el cliente envía una solicitud (ej iniciar grabación)
2 se crea un objeto `Command`
3 el `CommandBus` recibe el comando
4 el bus busca el `CommandHandler` registrado para ese comando
5 el handler ejecuta la lógica de negocio

beneficios
desacopla quien invoca la acción de quien la ejecuta permitiendo una arquitectura más limpia y testear cada parte aisladamente
