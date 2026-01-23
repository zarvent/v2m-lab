---
title: Configuration
description: Typed configuration system documentation using Pydantic Settings.
status: stable
last_update: 2026-01-23
language: US English
ai_context: "Configuration, Pydantic Settings, TOML"
---

# Configuration

Typed configuration system using Pydantic Settings.

---

## Main Settings

::: v2m.shared.config.Settings
options:
show_source: false
members: - paths - transcription - llm - notifications

---

## Paths Configuration

::: v2m.shared.config.PathsConfig
options:
show_source: false

---

## Transcription Configuration

::: v2m.shared.config.TranscriptionConfig
options:
show_source: false

::: v2m.shared.config.WhisperConfig
options:
show_source: false

::: v2m.shared.config.VadParametersConfig
options:
show_source: false

---

## LLM Configuration

::: v2m.shared.config.LLMConfig
options:
show_source: false

::: v2m.shared.config.GeminiConfig
options:
show_source: false

::: v2m.shared.config.OllamaConfig
options:
show_source: false

::: v2m.shared.config.LocalLLMConfig
options:
show_source: false

---

## Notifications Configuration

::: v2m.shared.config.NotificationsConfig
options:
show_source: false
