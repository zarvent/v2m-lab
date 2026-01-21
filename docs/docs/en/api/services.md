# Services

This page documents backend application services.

---

## Orchestrator

The Orchestrator is the central service that coordinates the entire Voice2Machine workflow.

### Responsibilities

- Manages complete lifecycle: recording → transcription → post-processing
- Maintains system state (idle, recording, processing)
- Coordinates communication between adapters without coupling them directly
- Emits events to connected WebSocket clients

### Lazy Initialization

All sub-services are created when first needed:

```python
@property
def worker(self) -> WhisperWorker:
    """Gets the Whisper worker (lazy init)."""
    if self._worker is None:
        self._worker = WhisperWorker()
    return self._worker
```

### Coordinated Services

| Service                | Description                       |
| ---------------------- | --------------------------------- |
| `WhisperWorker`        | Transcription with faster-whisper |
| `AudioRecorder`        | Audio capture (Rust extension)    |
| `StreamingTranscriber` | Real-time transcription           |
| `ClipboardService`     | System clipboard access           |
| `NotificationService`  | Desktop notifications             |
| `LLMService`           | Processing with Gemini/Ollama     |
