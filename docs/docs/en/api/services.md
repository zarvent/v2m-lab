---
title: Services and Application Logic
description: Overview of Workflows and Features.
status: stable
last_update: 2026-01-23
language: US English
---

# Services and Application Logic

In the 2026 model, application logic is divided into **Workflows** and **Features**.

## Workflows

Located in `v2m.orchestration`. They are the high-level coordinators.

- **RecordingWorkflow**: Manages the audio -> VAD -> transcription -> paste cycle.
- **LLMWorkflow**: Manages the text -> refinement/translation -> paste cycle.

## Features

Located in `v2m.features`. They are the functional building blocks of the system.

| Feature | Purpose | Main Implementation |
|---------|---------|---------------------|
| **Audio** | Capture and pre-processing | `v2m_engine` (Rust) |
| **Transcription** | Audio-to-text conversion | `faster-whisper` |
| **LLM** | Intelligent processing | `gemini` / `ollama` |

### Lazy Initialization

To minimize resource consumption (especially VRAM), heavy services are initialized only when first required.
