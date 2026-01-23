---
title: REST API (Backend)
description: Documentation for FastAPI endpoints and data models.
status: stable
last_update: 2026-01-23
language: US English
ai_context: "FastAPI, REST, Endpoints, Schemas, JSON"
---

# REST API (Backend)

Documentation for FastAPI endpoints and data models.

---

## Request/Response Models (Schemas)

::: v2m.api.schemas.ToggleResponse
options:
show_source: false

::: v2m.api.schemas.StatusResponse
options:
show_source: false

::: v2m.api.schemas.LLMResponse
options:
show_source: false

::: v2m.api.schemas.ProcessTextRequest
options:
show_source: false

::: v2m.api.schemas.TranslateTextRequest
options:
show_source: false

---

## Global State

::: v2m.api.app.DaemonState
options:
show_source: true
members: - **init** - recording - llm - broadcast_event

---

## Endpoints

### Recording

::: v2m.api.routes.recording.toggle_recording
options:
show_source: true

::: v2m.api.routes.recording.start_recording
options:
show_source: true

::: v2m.api.routes.recording.stop_recording
options:
show_source: true

### Status

::: v2m.api.routes.status.get_status
options:
show_source: true

::: v2m.api.routes.status.health_check
options:
show_source: true

### LLM

::: v2m.api.routes.llm.process_text
options:
show_source: true

::: v2m.api.routes.llm.translate_text
options:
show_source: true
