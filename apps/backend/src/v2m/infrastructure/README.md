# infrastructure

esta capa contiene las implementaciones concretas de las interfaces definidas en `core` y `application` aquí es donde la aplicación interactúa con el mundo exterior (hardware apis sistema operativo)

## contenido

| archivo | descripción |
|---------|-------------|
| `audio/` | manejo de grabación de audio y dispositivos |
| `gemini_llm_service.py` | implementación del servicio llm usando google gemini |
| `linux_adapters.py` | adaptadores para portapapeles (xclip/wl-clipboard) |
| `notification_service.py` | **servicio de notificaciones production-ready** con auto-dismiss via dbus |
| `vad_service.py` | servicio de detección de actividad de voz usando silero vad |
| `whisper_transcription_service.py` | implementación de transcripción usando faster-whisper |

## notification_service.py

servicio de notificaciones robusto que resuelve la limitación de unity/gnome que ignora `--expire-time` de notify-send

### arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                 LinuxNotificationService                     │
├─────────────────────────────────────────────────────────────┤
│  - ThreadPoolExecutor singleton (max 4 workers)             │
│  - DBUS via gdbus (sin dependencias python extra)           │
│  - Fallback automático a notify-send                        │
│  - Configuración inyectada desde config.toml                │
└─────────────────────────────────────────────────────────────┘
```

### configuración

en `config.toml`:

```toml
[notifications]
expire_time_ms = 3000  # tiempo antes de auto-cerrar (3s default)
auto_dismiss = true    # forzar cierre via DBUS
```

### uso

```python
from v2m.infrastructure.notification_service import LinuxNotificationService

service = LinuxNotificationService()
service.notify("✅ Success", "Operación completada")
# -> se cierra automáticamente después de expire_time_ms
```

## filosofía

este es el único lugar donde se permite importar librerías de terceros pesadas o específicas de plataforma (ej `sounddevice` `google-generativeai` `faster_whisper`)
