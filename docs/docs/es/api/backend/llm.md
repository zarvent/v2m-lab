---
title: Servicios LLM
description: Proveedores de modelos de lenguaje para procesamiento de texto.
status: stable
last_update: 2026-01-23
language: Native Latin American Spanish
ai_context: "LLM, Gemini, Ollama, local_service"
---

# Servicios LLM

Proveedores de modelos de lenguaje para procesamiento de texto.

---

## Google Gemini (Cloud)

Servicio LLM que conecta con la API de Google Gemini para procesamiento de texto y traducciones.

**Ubicación:** `v2m/features/llm/gemini_service.py`

**Métodos principales:**

- `process_text(text: str) -> str` - Refina texto con puntuación y gramática
- `translate_text(text: str, target_lang: str) -> str` - Traduce texto

---

## Ollama (Local)

Servicio LLM local que conecta con el servidor Ollama para privacidad total.

**Ubicación:** `v2m/features/llm/ollama_service.py`

**Configuración:** `http://localhost:11434`

---

## Local (llama.cpp)

Servicio LLM embebido usando llama-cpp-python directamente.

**Ubicación:** `v2m/features/llm/local_service.py`

---

## Patrón de Diseño

Todos los servicios LLM implementan una interfaz común (Protocolo):

```python
class ILLMService(Protocol):
    async def process_text(self, text: str) -> str:
        """Refina texto con gramática y puntuación."""
        ...

    async def translate_text(self, text: str, target_lang: str) -> str:
        """Traduce texto al idioma especificado."""
        ...
```

El `LLMWorkflow` selecciona el backend según `config.llm.provider`:

- `"gemini"` → GeminiLLMService
- `"ollama"` → OllamaLLMService
- `"local"` → LocalLLMService
