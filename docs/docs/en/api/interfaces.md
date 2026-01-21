# Interfaces (Protocols)

This page documents the protocols (interfaces) that define system contracts.

---

## Orchestrator

The Orchestrator is the central component that coordinates the entire workflow.

### Main Methods

```python
class Orchestrator:
    async def toggle(self) -> ToggleResponse:
        """Recording toggle (start/stop)."""

    async def start(self) -> ToggleResponse:
        """Starts audio recording."""

    async def stop(self) -> ToggleResponse:
        """Stops recording and transcribes audio."""

    async def warmup(self) -> None:
        """Pre-loads Whisper model into VRAM."""

    async def shutdown(self) -> None:
        """Releases resources on server shutdown."""

    def get_status(self) -> StatusResponse:
        """Returns current daemon state."""

    async def process_text(self, text: str) -> LLMResponse:
        """Processes text with LLM (cleanup, punctuation)."""

    async def translate_text(self, text: str, target_lang: str) -> LLMResponse:
        """Translates text with LLM."""
```

---

## Response Models

### ToggleResponse

```python
class ToggleResponse(BaseModel):
    status: str      # 'recording' | 'idle'
    message: str     # Descriptive message
    text: str | None # Transcribed text (only on stop)
```

### StatusResponse

```python
class StatusResponse(BaseModel):
    state: str        # 'idle' | 'recording' | 'processing'
    recording: bool   # True if recording
    model_loaded: bool # True if Whisper is in VRAM
```

### LLMResponse

```python
class LLMResponse(BaseModel):
    text: str    # Processed/translated text
    backend: str # 'gemini' | 'ollama' | 'local'
```
