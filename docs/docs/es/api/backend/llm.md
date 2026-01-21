# Servicios LLM

Proveedores de modelos de lenguaje para procesamiento de texto.

---

## Google Gemini (Cloud)

Servicio LLM que conecta con la API de Google Gemini para procesamiento de texto y traducciones.

**Ubicación:** `v2m/infrastructure/gemini_llm_service.py`

**Métodos principales:**

- `process_text(text: str) -> str` - Refina texto con puntuación y gramática
- `translate_text(text: str, target_lang: str) -> str` - Traduce texto

---

## Ollama (Local)

Servicio LLM local que conecta con el servidor Ollama para privacidad total.

**Ubicación:** `v2m/infrastructure/ollama_llm_service.py`

**Configuración:** `http://localhost:11434`

---

## Local (llama.cpp)

Servicio LLM embebido usando llama-cpp-python directamente.

**Ubicación:** `v2m/infrastructure/local_llm_service.py`

---

## Patrón de Diseño

Todos los servicios LLM implementan una interfaz común:

```python
class LLMService(Protocol):
    def process_text(self, text: str) -> str:
        """Refina texto con gramática y puntuación."""
        ...

    def translate_text(self, text: str, target_lang: str) -> str:
        """Traduce texto al idioma especificado."""
        ...
```

El `Orchestrator` selecciona el backend según `config.llm.backend`:

- `"gemini"` → GeminiLLMService
- `"ollama"` → OllamaLLMService
- `"local"` → LocalLLMService
