# Configuración

Sistema de configuración tipada usando Pydantic Settings.

---

## Settings Principal

::: v2m.config.Settings
options:
show_source: false
members: - paths - transcription - llm - gemini - notifications

---

## Configuración de Rutas

::: v2m.config.PathsConfig
options:
show_source: false

---

## Configuración de Transcripción

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

## Configuración LLM

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

## Configuración de Notificaciones

::: v2m.config.NotificationsConfig
options:
show_source: false
