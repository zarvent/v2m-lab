# Dominio

Esta página documenta los modelos de dominio y tipos de datos del sistema.

---

## Modelos de Datos

### CorrectionResult

Modelo de salida estructurada para refinamiento de texto.

Este modelo fuerza a los LLMs a responder en un formato JSON predecible, facilitando el parsing y reduciendo alucinaciones de formato.

```python
from pydantic import BaseModel, Field

class CorrectionResult(BaseModel):
    corrected_text: str = Field(
        description="Texto corregido con gramática y coherencia mejoradas"
    )
    explanation: str | None = Field(
        default=None,
        description="Cambios realizados al texto original"
    )
```

**Ejemplo de uso:**

```python
result = CorrectionResult(
    corrected_text="Hola, ¿cómo estás?",
    explanation="Añadida puntuación y signos de interrogación"
)
```

---

## Errores de Dominio

El sistema define excepciones específicas para diferentes tipos de errores:

| Excepción            | Descripción                                            |
| -------------------- | ------------------------------------------------------ |
| `TranscriptionError` | Error durante la transcripción de audio                |
| `AudioCaptureError`  | Error en la captura de audio (micrófono no disponible) |
| `LLMError`           | Error al comunicarse con el proveedor LLM              |
| `ConfigurationError` | Error en la configuración del sistema                  |
