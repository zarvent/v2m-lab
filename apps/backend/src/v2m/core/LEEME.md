# core

El núcleo de la aplicación contiene los componentes fundamentales que son compartidos por todas las capas del sistema. Aquí se definen las abstracciones principales y los mecanismos de comunicación.

## Contenido

- `cqrs/` - Implementación del patrón Command Query Responsibility Segregation
- `di/` - Contenedor de inyección de dependencias
- `interfaces.py` - Definiciones de puertos (interfaces abstractas) para adaptadores
- `ipc_protocol.py` - Definición del protocolo de comunicación inter-procesos
- `logging.py` - Configuración del sistema de logs estructurados

## Propósito

Este módulo busca desacoplar los componentes de alto nivel de los detalles de implementación, proveyendo interfaces claras y mecanismos de comunicación agnósticos.
