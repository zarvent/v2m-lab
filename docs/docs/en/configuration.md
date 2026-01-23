---
title: Configuration Guide
description: Detailed instructions for configuring transcription and LLM services.
ai_context: "Configuration, TOML, Whisper, Gemini, Ollama"
depends_on: []
status: stable
---

# ⚙️ Configuration Guide

!!! info "Configuration Management"
Configuration is primarily managed through the Frontend GUI (Gear icon ⚙️). However, advanced users can directly edit the `config.toml` file.

> **File location**: `$XDG_CONFIG_HOME/v2m/config.toml` (usually `~/.config/v2m/config.toml`).

---

## 1. Local Transcription (`[transcription]`)

The heart of the system. These parameters control the **Faster-Whisper** engine.

| Parameter            | Type   | Default           | Description and Best Practice 2026                                                                             |
| :------------------- | :----- | :---------------- | :------------------------------------------------------------------------------------------------------------- |
| `model`              | `str`  | `distil-large-v3` | Model to load. `distil-large-v3` offers extreme speed with SOTA accuracy. Options: `large-v3-turbo`, `medium`. |
| `device`             | `str`  | `cuda`            | `cuda` (NVIDIA GPU) is mandatory for real-time experience. `cpu` is functional but not recommended.            |
| `compute_type`       | `str`  | `float16`         | Tensor precision. `float16` or `int8_float16` optimize VRAM and throughput on modern GPUs.                     |
| `use_faster_whisper` | `bool` | `true`            | Enables the optimized CTranslate2 backend.                                                                     |

### Voice Activity Detection (VAD)

The system uses **Silero VAD** (Rust version in `v2m_engine`) to filter silence before invoking Whisper, saving GPU cycles.

- **`vad_filter`** (`true`): Activates pre-filtering.
- **`vad_parameters`**: Fine-tune sensitivity (silence threshold, minimum voice duration).

---

## 2. LLM Services (`[llm]`)

Voice2Machine implements a **Provider** pattern to support multiple AI backends for text refinement.

### Global Configuration

| Parameter  | Description                                                    |
| :--------- | :------------------------------------------------------------- |
| `provider` | Active provider: `gemini` (Cloud) or `ollama` (Local).         |
| `model`    | Specific model name (e.g., `gemini-1.5-flash` or `llama3:8b`). |

### Specific Providers

#### Google Gemini (`provider = "gemini"`)

Requires API Key. Ideal for users without powerful GPU (VRAM < 8GB).

- **Recommended model**: `gemini-1.5-flash-latest` (minimum latency).
- **Temperature**: `0.3` (conservative) for grammar correction.

#### Ollama (`provider = "ollama"`)

Total privacy. Requires running the Ollama server (`ollama serve`).

- **Endpoint**: `http://localhost:11434`
- **Recommended model**: `qwen2.5:7b` or `llama3.1:8b`.

---

## 3. Recording (`[recording]`)

Controls audio capture via `SoundDevice` and `v2m_engine`.

- **`sample_rate`**: `16000` (Fixed, required by Whisper).
- **`channels`**: `1` (Mono).
- **`device_index`**: Microphone ID. If `null`, uses system default (PulseAudio/PipeWire).

---

## 4. System (`[system]`)

Low-level configuration for the Daemon and communication.

- **`host`**: Server host (`127.0.0.1` for local-only access).
- **`port`**: HTTP port (`8765` by default).
- **`log_level`**: `INFO` by default. Change to `DEBUG` for deep diagnostics.

---

## Secrets and Security

API keys are managed via environment variables or secure storage, never in plain text inside `config.toml` if possible.

```bash
# Define in .env or system environment
export GEMINI_API_KEY="AIzaSy_YOUR_KEY_HERE"
```

!!! warning "Important"
Restart the daemon (using `scripts/operations/daemon/restart_daemon.sh`) after manually editing the configuration file to apply changes.
