# LLM Services

Language model providers for text processing.

---

## Google Gemini (Cloud)

LLM service connecting to Google Gemini API for text processing and translations.

**Location:** `v2m/infrastructure/gemini_llm_service.py`

**Main methods:**

- `process_text(text: str) -> str` - Refines text with punctuation and grammar
- `translate_text(text: str, target_lang: str) -> str` - Translates text

---

## Ollama (Local)

Local LLM service connecting to Ollama server for total privacy.

**Location:** `v2m/infrastructure/ollama_llm_service.py`

**Configuration:** `http://localhost:11434`

---

## Local (llama.cpp)

Embedded LLM service using llama-cpp-python directly.

**Location:** `v2m/infrastructure/local_llm_service.py`

---

## Design Pattern

All LLM services implement a common interface:

```python
class LLMService(Protocol):
    def process_text(self, text: str) -> str:
        """Refines text with grammar and punctuation."""
        ...

    def translate_text(self, text: str, target_lang: str) -> str:
        """Translates text to specified language."""
        ...
```

The `Orchestrator` selects the backend based on `config.llm.backend`:

- `"gemini"` → GeminiLLMService
- `"ollama"` → OllamaLLMService
- `"local"` → LocalLLMService
