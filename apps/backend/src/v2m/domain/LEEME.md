# domain

La capa de dominio encapsula las reglas de negocio y las definiciones fundamentales del problema que resuelve la aplicación. Esta capa no debe depender de ninguna tecnología externa (base de datos, frameworks web, etc.).

## Contenido

- `errors.py` - Jerarquía de excepciones del dominio que representan errores de negocio semánticos (ej. `MicrophoneNotFoundError`, `TranscriptionError`)

## Filosofía

El dominio es el corazón de la aplicación y debe permanecer puro y agnóstico a la infraestructura. Los cambios en librerías externas no deberían afectar este directorio.
