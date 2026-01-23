---
title: Domain
description: Data models and core business logic.
status: stable
last_update: 2026-01-23
language: US English
---

# Domain

This page documents domain models and data types.

## Data Models (Pydantic V2)

Voice2Machine data models use Pydantic V2 for strict validation and fast serialization.

### API Models (Schemas)

Located in `v2m.api.schemas`, they define input/output contracts for the REST API and WebSockets.

| Class | Purpose |
|-------|---------|
| `StatusResponse` | Current daemon state (idle, recording, etc) |
| `ToggleResponse` | Result of starting/stopping recording |
| `TranscriptionUpdate` | Streaming event with provisional text |
| `LLMResponse` | Text processing result |

### CorrectionResult

Structured output model for text refinement (used by LLM Workflows).

```python
class CorrectionResult(BaseModel):
    corrected_text: str = Field(description="Corrected text")
    explanation: str | None = Field(default=None, description="Changes made")
```

---

## Exceptions

The system uses an exception hierarchy based on `ApplicationError`.

| Exception | Context |
|-----------|---------|
| `AudioError` | Hardware or audio buffer failures |
| `TranscriptionError` | Whisper model or VRAM failures |
| `LLMProviderError` | Connection or quota errors with Gemini/Ollama |
| `ConfigError` | Validation error in `config.toml` |
