# infrastructure

Esta capa contiene las implementaciones concretas de las interfaces definidas en `core` y `application`. Aquí es donde la aplicación interactúa con el mundo exterior (hardware, APIs, sistema operativo).

## Contenido

| Archivo                            | Descripción                                                               |
| ---------------------------------- | ------------------------------------------------------------------------- |
| `audio/`                           | Manejo de grabación de audio y dispositivos                               |
| `gemini_llm_service.py`            | Implementación del servicio LLM usando Google Gemini                      |
| `linux_adapters.py`                | Adaptadores para portapapeles (xclip/wl-clipboard)                        |
| `notification_service.py`          | **Servicio de notificaciones production-ready** con auto-dismiss via dbus |
| `vad_service.py`                   | Servicio de detección de actividad de voz usando Silero VAD               |
| `whisper_transcription_service.py` | Implementación de transcripción usando faster-whisper                     |

## notification_service.py

Servicio de notificaciones robusto que resuelve la limitación de Unity/GNOME que ignora `--expire-time` de notify-send.

### Arquitectura

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

### Configuración

En `config.toml`:

```toml
[notifications]
expire_time_ms = 3000  # tiempo antes de auto-cerrar (3s default)
auto_dismiss = true    # forzar cierre via DBUS
```

### Uso

```python
from v2m.infrastructure.notification_service import LinuxNotificationService

service = LinuxNotificationService()
service.notify("✅ Success", "Operación completada")
# -> se cierra automáticamente después de expire_time_ms
```

## Filosofía

Este es el único lugar donde se permite importar librerías de terceros pesadas o específicas de plataforma (ej. `sounddevice`, `google-generativeai`, `faster_whisper`).
