# Domain

This page documents domain models and data types.

---

## Data Models

### CorrectionResult

Structured output model for text refinement.

This model forces LLMs to respond in a predictable JSON format, facilitating parsing and reducing format hallucinations.

```python
from pydantic import BaseModel, Field

class CorrectionResult(BaseModel):
    corrected_text: str = Field(
        description="Corrected text with improved grammar and coherence"
    )
    explanation: str | None = Field(
        default=None,
        description="Changes made to the original text"
    )
```

**Usage Example:**

```python
result = CorrectionResult(
    corrected_text="Hello, how are you?",
    explanation="Added punctuation and question marks"
)
```

---

## Domain Errors

The system defines specific exceptions for different error types:

| Exception            | Description                                     |
| -------------------- | ----------------------------------------------- |
| `TranscriptionError` | Error during audio transcription                |
| `AudioCaptureError`  | Error in audio capture (microphone unavailable) |
| `LLMError`           | Error communicating with LLM provider           |
| `ConfigurationError` | System configuration error                      |
