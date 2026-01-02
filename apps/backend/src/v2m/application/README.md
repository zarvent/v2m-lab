# application

la capa de aplicación orquesta la lógica de negocio coordinando las entidades de dominio y las interfaces de infraestructura aquí residen los casos de uso del sistema

contenido
- `commands.py` definiciones de los comandos disponibles (ej `StartRecordingCommand`)
- `command_handlers.py` implementaciones de la lógica para cada comando
- `llm_service.py` interfaz abstracta para servicios de modelos de lenguaje
- `transcription_service.py` interfaz abstracta para servicios de transcripción

responsabilidad
esta capa traduce las intenciones del usuario (comandos) en acciones concretas coordinando los servicios necesarios pero sin conocer los detalles de implementación (ej sabe que debe "transcribir" pero no sabe que usa whisper)
