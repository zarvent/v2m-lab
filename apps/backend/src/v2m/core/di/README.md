# dependency injection

este módulo maneja la inyección de dependencias (di) de toda la aplicación utilizando un contenedor centralizado

componentes
- `container.py` define la clase `Container` que instancia y almacena todos los servicios y handlers como singletons

responsabilidades
- **composición root** es el único lugar donde se conocen las implementaciones concretas (ej `WhisperTranscriptionService`)
- **cableado** inyecta las dependencias necesarias en los constructores de las clases (ej pasar `NotificationInterface` a `StartRecordingHandler`)
- **ciclo de vida** asegura que los servicios pesados (como modelos de ml) se instancien una sola vez y se reutilicen

uso
para acceder a un servicio desde cualquier punto de la aplicación (aunque se recomienda hacerlo solo en puntos de entrada)

```python
from v2m.core.di.container import container
bus = container.get_command_bus()
```
