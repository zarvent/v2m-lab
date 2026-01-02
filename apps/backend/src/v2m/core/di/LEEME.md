# Dependency Injection

Este módulo maneja la inyección de dependencias (DI) de toda la aplicación utilizando un contenedor centralizado.

## Componentes

- `container.py` - Define la clase `Container` que instancia y almacena todos los servicios y handlers como singletons

## Responsabilidades

- **Composition Root**: Es el único lugar donde se conocen las implementaciones concretas (ej. `WhisperTranscriptionService`)
- **Cableado**: Inyecta las dependencias necesarias en los constructores de las clases (ej. pasar `NotificationInterface` a `StartRecordingHandler`)
- **Ciclo de vida**: Asegura que los servicios pesados (como modelos de ML) se instancien una sola vez y se reutilicen

## Uso

Para acceder a un servicio desde cualquier punto de la aplicación (aunque se recomienda hacerlo solo en puntos de entrada):

```python
from v2m.core.di.container import container
bus = container.get_command_bus()
```
