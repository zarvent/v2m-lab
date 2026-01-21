# API REST

Documentación de los endpoints FastAPI y modelos de datos.

---

## Modelos de Request/Response

::: v2m.api.ToggleResponse
options:
show_source: false

::: v2m.api.StatusResponse
options:
show_source: false

::: v2m.api.LLMResponse
options:
show_source: false

::: v2m.api.ProcessTextRequest
options:
show_source: false

::: v2m.api.TranslateTextRequest
options:
show_source: false

---

## Estado Global

::: v2m.api.DaemonState
options:
show_source: true
members: - **init** - orchestrator - broadcast_event

---

## Endpoints

::: v2m.api.toggle_recording
options:
show_source: true

::: v2m.api.start_recording
options:
show_source: true

::: v2m.api.stop_recording
options:
show_source: true

::: v2m.api.get_status
options:
show_source: true

::: v2m.api.health_check
options:
show_source: true

::: v2m.api.process_text
options:
show_source: true

::: v2m.api.translate_text
options:
show_source: true
