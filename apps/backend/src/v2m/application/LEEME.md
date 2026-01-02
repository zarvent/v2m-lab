# application

La capa de aplicación orquesta la lógica de negocio coordinando las entidades de dominio y las interfaces de infraestructura. Aquí residen los casos de uso del sistema.

## Contenido

- `commands.py` - Definiciones de los comandos disponibles (ej. `StartRecordingCommand`)
- `command_handlers.py` - Implementaciones de la lógica para cada comando
- `llm_service.py` - Interfaz abstracta para servicios de modelos de lenguaje
- `transcription_service.py` - Interfaz abstracta para servicios de transcripción

## Responsabilidad

Esta capa traduce las intenciones del usuario (comandos) en acciones concretas coordinando los servicios necesarios, pero sin conocer los detalles de implementación (ej. sabe que debe "transcribir" pero no sabe que usa Whisper).
