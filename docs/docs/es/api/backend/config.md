---
title: Configuración (API)
description: Documentación del sistema de configuración tipada usando Pydantic Settings.
status: stable
last_update: 2026-01-23
language: Native Latin American Spanish
ai_context: "Configuración, Pydantic Settings, TOML"
---

# Configuración

Sistema de configuración tipada usando Pydantic Settings.

---

## Settings Principal

::: v2m.shared.config.Settings
options:
show_source: false
members: - paths - transcription - llm - notifications

---

## Configuración de Rutas

::: v2m.shared.config.PathsConfig
options:
show_source: false

---

## Configuración de Transcripción

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

## Configuración LLM

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

## Configuración de Notificaciones

::: v2m.shared.config.NotificationsConfig
options:
show_source: false
