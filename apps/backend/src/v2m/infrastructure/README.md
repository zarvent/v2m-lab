# infrastructure

This layer contains concrete implementations of interfaces defined in `core` and `application`. This is where the application interacts with the outside world (hardware, APIs, operating system).

## Content

| File                               | Description                                                          |
| ---------------------------------- | -------------------------------------------------------------------- |
| `audio/`                           | Audio recording and device management                                |
| `gemini_llm_service.py`            | LLM service implementation using Google Gemini                       |
| `linux_adapters.py`                | Clipboard adapters (xclip/wl-clipboard)                              |
| `notification_service.py`          | **Production-ready notification service** with auto-dismiss via dbus |
| `vad_service.py`                   | Voice activity detection service using Silero VAD                    |
| `whisper_transcription_service.py` | Transcription implementation using faster-whisper                    |

## notification_service.py

Robust notification service that solves the Unity/GNOME limitation that ignores notify-send's `--expire-time`.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 LinuxNotificationService                     │
├─────────────────────────────────────────────────────────────┤
│  - ThreadPoolExecutor singleton (max 4 workers)             │
│  - DBUS via gdbus (no extra python dependencies)            │
│  - Automatic fallback to notify-send                        │
│  - Configuration injected from config.toml                  │
└─────────────────────────────────────────────────────────────┘
```

### Configuration

In `config.toml`:

```toml
[notifications]
expire_time_ms = 3000  # time before auto-close (3s default)
auto_dismiss = true    # force close via DBUS
```

### Usage

```python
from v2m.infrastructure.notification_service import LinuxNotificationService

service = LinuxNotificationService()
service.notify("✅ Success", "Operation completed")
# -> closes automatically after expire_time_ms
```

## Philosophy

This is the only place where heavy or platform-specific third-party libraries can be imported (e.g., `sounddevice`, `google-generativeai`, `faster_whisper`).
