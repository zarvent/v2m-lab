# Backend API (Python)

This section contains documentation automatically generated from the Voice2Machine backend source code.

!!! info "Auto-generated"
This documentation syncs automatically with code docstrings.
Source of truth: `apps/daemon/backend/src/v2m/`

---

## Main Modules

### Coordination Service

- [**Orchestrator**](orchestrator.md) - Central system coordinator
- [**REST API**](api.md) - FastAPI endpoints and data models

### Configuration

- [**Config**](config.md) - Typed configuration system

### Infrastructure

- [**Transcription**](transcription.md) - Whisper and streaming
- [**LLM Services**](llm.md) - Gemini, Ollama, Local

---

## Layer Navigation

```mermaid
graph TD
    A[REST API] --> B[Orchestrator]
    B --> C[Infrastructure]
    C --> D[Whisper]
    C --> E[Audio Recorder]
    C --> F[LLM Providers]

    style A fill:#e3f2fd
    style B fill:#fff3e0
    style C fill:#f3e5f5
```

| Layer              | Responsibility                            |
| ------------------ | ----------------------------------------- |
| **API**            | HTTP endpoints, validation, serialization |
| **Services**       | Workflow coordination                     |
| **Infrastructure** | External service adapters                 |

---

## Code Status

| Metric             | Value        |
| ------------------ | ------------ |
| Python Files       | 27           |
| Docstring Coverage | ~70%         |
| Style              | Google Style |
