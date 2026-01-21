# Servicios

Esta página documenta los servicios de aplicación del backend.

---

## Orchestrator

El Orchestrator es el servicio central que coordina todo el flujo de trabajo de Voice2Machine.

### Responsabilidades

- Gestiona el ciclo de vida completo: grabación → transcripción → post-procesamiento
- Mantiene el estado del sistema (idle, recording, processing)
- Coordina la comunicación entre adaptadores sin acoplarlos directamente
- Emite eventos a clientes WebSocket conectados

### Lazy Initialization

Todos los sub-servicios se crean cuando se necesitan por primera vez:

```python
@property
def worker(self) -> WhisperWorker:
    """Obtiene el worker de Whisper (lazy init)."""
    if self._worker is None:
        self._worker = WhisperWorker()
    return self._worker
```

### Servicios Coordinados

| Servicio               | Descripción                        |
| ---------------------- | ---------------------------------- |
| `WhisperWorker`        | Transcripción con faster-whisper   |
| `AudioRecorder`        | Captura de audio (Rust extension)  |
| `StreamingTranscriber` | Transcripción en tiempo real       |
| `ClipboardService`     | Acceso al portapapeles del sistema |
| `NotificationService`  | Notificaciones de escritorio       |
| `LLMService`           | Procesamiento con Gemini/Ollama    |
