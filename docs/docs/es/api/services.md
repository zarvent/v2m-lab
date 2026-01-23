---
title: Servicios y Lógica de Aplicación
description: Resumen de flujos de trabajo (Workflows) y características (Features).
status: stable
last_update: 2026-01-23
language: Native Latin American Spanish
---

# Servicios y Lógica de Aplicación

En el modelo 2026, la lógica de aplicación se divide en **Flujos de Trabajo (Workflows)** y **Características (Features)**.

## Flujos de Trabajo (Workflows)

Ubicados en `v2m.orchestration`. Son los coordinadores de alto nivel.

- **RecordingWorkflow**: Gestiona el ciclo audio -> VAD -> transcripción -> pegado.
- **LLMWorkflow**: Gestiona el ciclo texto -> refinamiento/traducción -> pegado.

## Características (Features)

Ubicados en `v2m.features`. Son los bloques de construcción funcionales del sistema.

| Característica | Propósito | Implementación Principal |
|----------------|-----------|---------------------------|
| **Audio** | Captura y pre-procesamiento | `v2m_engine` (Rust) |
| **Transcription** | Conversión audio-a-texto | `faster-whisper` |
| **LLM** | Procesamiento inteligente | `gemini` / `ollama` |

### Inicialización Lazy

Para minimizar el consumo de recursos (especialmente VRAM), los servicios pesados se inicializan solo al ser requeridos por primera vez.
