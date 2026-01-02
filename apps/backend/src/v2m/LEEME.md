# voice2machine package

Este es el paquete principal de la aplicación voice2machine. Contiene toda la lógica de negocio, infraestructura y configuración del sistema.

## Estructura

El paquete sigue una arquitectura hexagonal (ports and adapters) modificada:

- `application/` - Casos de uso y lógica de aplicación
- `core/` - Núcleo del sistema, interfaces, protocolos y utilidades compartidas
- `domain/` - Entidades de negocio y errores del dominio
- `infrastructure/` - Implementaciones concretas de interfaces (adaptadores)
- `gui/` - Interfaz gráfica de usuario (si aplica)

## Archivos Principales

- `main.py` - Punto de entrada de la aplicación (CLI y daemon)
- `daemon.py` - Implementación del proceso en segundo plano
- `client.py` - Cliente para comunicarse con el daemon vía IPC
- `config.py` - Gestión centralizada de configuración
