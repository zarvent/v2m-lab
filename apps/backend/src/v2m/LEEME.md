# voice2machine package

este es el paquete principal de la aplicación voice2machine contiene toda la lógica de negocio infraestructura y configuración del sistema

estructura
el paquete sigue una arquitectura hexagonal (ports and adapters) modificada

- `application/` casos de uso y lógica de aplicación
- `core/` núcleo del sistema interfaces protocolos y utilidades compartidas
- `domain/` entidades de negocio y errores del dominio
- `infrastructure/` implementaciones concretas de interfaces (adaptadores)
- `gui/` interfaz gráfica de usuario (si aplica)

archivos principales
- `main.py` punto de entrada de la aplicación (cli y daemon)
- `daemon.py` implementación del proceso en segundo plano
- `client.py` cliente para comunicarse con el daemon vía ipc
- `config.py` gestión centralizada de configuración
