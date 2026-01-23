---
title: LLM Services
description: Language model providers for text processing.
status: stable
last_update: 2026-01-23
language: US English
ai_context: "LLM, Gemini, Ollama, local_service"
---

# LLM Services

Language model providers for text processing.

---

## Google Gemini (Cloud)

LLM service connecting to Google Gemini API for text processing and translations.

**Location:** `v2m/features/llm/gemini_service.py`

**Main methods:**

- `process_text(text: str) -> str` - Refines text with punctuation and grammar
- `translate_text(text: str, target_lang: str) -> str` - Translates text

---

## Ollama (Local)

Local LLM service connecting to Ollama server for total privacy.

**Location:** `v2m/features/llm/ollama_service.py`

**Configuration:** `http://localhost:11434`

---

## Local (llama.cpp)

Embedded LLM service using llama-cpp-python directly.

**Location:** `v2m/features/llm/local_service.py`

---

## Design Pattern

All LLM services implement a common interface (Protocol):

```python
class ILLMService(Protocol):
    async def process_text(self, text: str) -> str:
        """Refines text with grammar and punctuation."""
        ...

    async def translate_text(self, text: str, target_lang: str) -> str:
        """Translates text to specified language."""
        ...
```

The `LLMWorkflow` selects the backend based on `config.llm.provider`:

- `"gemini"` → GeminiLLMService
- `"ollama"` → OllamaLLMService
- `"local"` → LocalLLMService
