# Interfaces (Protocolos)

Esta página documenta los protocolos (interfaces) que definen los contratos del sistema.

---

## Orchestrator

El Orchestrator es el componente central que coordina todo el flujo de trabajo.

### Métodos Principales

```python
class Orchestrator:
    async def toggle(self) -> ToggleResponse:
        """Toggle de grabación (iniciar/detener)."""

    async def start(self) -> ToggleResponse:
        """Inicia la grabación de audio."""

    async def stop(self) -> ToggleResponse:
        """Detiene la grabación y transcribe el audio."""

    async def warmup(self) -> None:
        """Pre-carga el modelo Whisper en VRAM."""

    async def shutdown(self) -> None:
        """Libera recursos al apagar el servidor."""

    def get_status(self) -> StatusResponse:
        """Retorna estado actual del daemon."""

    async def process_text(self, text: str) -> LLMResponse:
        """Procesa texto con LLM (limpieza, puntuación)."""

    async def translate_text(self, text: str, target_lang: str) -> LLMResponse:
        """Traduce texto con LLM."""
```

---

## Response Models

### ToggleResponse

```python
class ToggleResponse(BaseModel):
    status: str      # 'recording' | 'idle'
    message: str     # Mensaje descriptivo
    text: str | None # Texto transcrito (solo en stop)
```

### StatusResponse

```python
class StatusResponse(BaseModel):
    state: str        # 'idle' | 'recording' | 'processing'
    recording: bool   # True si está grabando
    model_loaded: bool # True si Whisper está en VRAM
```

### LLMResponse

```python
class LLMResponse(BaseModel):
    text: str    # Texto procesado/traducido
    backend: str # 'gemini' | 'ollama' | 'local'
```
