---
title: Dominio
description: Modelos de datos y lógica de negocio principal.
status: stable
last_update: 2026-01-23
language: Native Latin American Spanish
---

# Dominio

Esta página documenta los modelos de dominio y tipos de datos del sistema.

## Modelos de Datos (Pydantic V2)

Los modelos de datos de Voice2Machine utilizan Pydantic V2 para validación estricta y serialización rápida.

### Modelos de API (Schemas)

Se encuentran en `v2m.api.schemas` y definen los contratos de entrada/salida para la API REST y WebSockets.

| Clase | Propósito |
|-------|-----------|
| `StatusResponse` | Estado actual del daemon (idle, recording, etc) |
| `ToggleResponse` | Resultado de iniciar/detener grabación |
| `TranscriptionUpdate` | Evento de streaming con texto provisional |
| `LLMResponse` | Resultado del procesamiento de texto |

### CorrectionResult

Modelo de salida estructurada para refinamiento de texto (usado por los Workflows de LLM).

```python
class CorrectionResult(BaseModel):
    corrected_text: str = Field(description="Texto corregido")
    explanation: str | None = Field(default=None, description="Cambios realizados")
```

---

## Excepciones

El sistema utiliza una jerarquía de excepciones basada en `ApplicationError`.

| Excepción | Contexto |
|-----------|----------|
| `AudioError` | Fallos en el hardware o buffer de audio |
| `TranscriptionError` | Fallos en el modelo Whisper o VRAM |
| `LLMProviderError` | Error de conexión o cuota con Gemini/Ollama |
| `ConfigError` | Error de validación en `config.toml` |
