# Configuration

Typed configuration system using Pydantic Settings.

---

## Main Settings

::: v2m.config.Settings
options:
show_source: false
members: - paths - transcription - llm - gemini - notifications

---

## Paths Configuration

::: v2m.config.PathsConfig
options:
show_source: false

---

## Transcription Configuration

::: v2m.config.TranscriptionConfig
options:
show_source: false

::: v2m.config.WhisperConfig
options:
show_source: false

::: v2m.config.VadParametersConfig
options:
show_source: false

---

## LLM Configuration

::: v2m.config.LLMConfig
options:
show_source: false

::: v2m.config.GeminiConfig
options:
show_source: false

::: v2m.config.OllamaConfig
options:
show_source: false

::: v2m.config.LocalLLMConfig
options:
show_source: false

---

## Notifications Configuration

::: v2m.config.NotificationsConfig
options:
show_source: false
