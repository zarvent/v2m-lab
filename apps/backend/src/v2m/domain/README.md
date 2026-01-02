# domain

la capa de dominio encapsula las reglas de negocio y las definiciones fundamentales del problema que resuelve la aplicación esta capa no debe depender de ninguna tecnología externa (base de datos frameworks web etc)

contenido
- `errors.py` jerarquía de excepciones del dominio que representan errores de negocio semánticos (ej `MicrophoneNotFoundError` `TranscriptionError`)

filosofía
el dominio es el corazón de la aplicación y debe permanecer puro y agnóstico a la infraestructura los cambios en librerías externas no deberían afectar este directorio
