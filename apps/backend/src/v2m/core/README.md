# core

el núcleo de la aplicación contiene los componentes fundamentales que son compartidos por todas las capas del sistema aquí se definen las abstracciones principales y los mecanismos de comunicación

contenido
- `cqrs/` implementación del patrón command query responsibility segregation
- `di/` contenedor de inyección de dependencias
- `interfaces.py` definiciones de puertos (interfaces abstractas) para adaptadores
- `ipc_protocol.py` definición del protocolo de comunicación inter-procesos
- `logging.py` configuración del sistema de logs estructurados

propósito
este módulo busca desacoplar los componentes de alto nivel de los detalles de implementación proveyendo interfaces claras y mecanismos de comunicación agnósticos
