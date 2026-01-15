# ⚙️ Configuration Guide

!!! info "Configuration Management"
    Configuration is primarily managed through the Frontend graphical interface (Gear icon ⚙️). However, advanced users can edit the `config.toml` file directly.

> **File Location**: `$XDG_CONFIG_HOME/v2m/config.toml` (usually `~/.config/v2m/config.toml`).

---

## 1. Local Transcription (`[transcription]`)

The heart of the system. These parameters control the **Faster-Whisper** engine.

| Parameter | Type | Default | Description and "Best Practice" 2026 |
| :--- | :--- | :--- | :--- |
| `model` | `str` | `distil-large-v3` | Model to load. `distil-large-v3` offers extreme speed with SOTA accuracy. Options: `large-v3-turbo`, `medium`. |
| `device` | `str` | `cuda` | `cuda` (NVIDIA GPU) is mandatory for real-time experience. `cpu` is functional but not recommended. |
| `compute_type` | `str` | `float16` | Tensor precision. `float16` or `int8_float16` optimize VRAM and throughput on modern GPUs. |
| `use_faster_whisper` | `bool` | `true` | Enables the optimized CTranslate2 backend. |

### Voice Detection (VAD)

The system uses **Silero VAD** (Rust version in `v2m_engine`) to filter silence before invoking Whisper, saving GPU resources.

- **`vad_filter`** (`true`): Activates pre-filtering.
- **`vad_parameters`**: Fine-tuning of sensitivity (silence threshold, minimum speech duration).

---

## 2. LLM Services (`[llm]`)

Voice2Machine implements a **Provider** pattern to support multiple AI backends for text refinement.

### Global Configuration
| Parameter | Description |
| :--- | :--- |
| `provider` | Active provider: `gemini` (Cloud) or `ollama` (Local). |
| `model` | Specific model name (e.g. `gemini-1.5-flash` or `llama3:8b`). |

### Specific Providers

#### Google Gemini (`provider = "gemini"`)
Requires API Key. Ideal for users without a powerful GPU (VRAM < 8GB).
- **Recommended Model**: `gemini-1.5-flash-latest` (minimum latency).
- **Temperature**: `0.3` (conservative) for grammatical correction.

#### Ollama (`provider = "ollama"`)
Total privacy. Requires running the Ollama server (`ollama serve`).
- **Endpoint**: `http://localhost:11434`
- **Recommended Model**: `qwen2.5:7b` or `llama3.1:8b`.

---

## 3. Recording (`[recording]`)

Controls audio capture using `SoundDevice` and `v2m_engine`.

- **`sample_rate`**: `16000` (Fixed, required by Whisper).
- **`channels`**: `1` (Mono).
- **`device_index`**: Microphone ID. If `null`, uses system default (PulseAudio/PipeWire).

---

## 4. System and IPC (`[system]`)

Low-level configuration for the Daemon and communication.

- **`socket_path`**: Path to Unix socket (`/tmp/v2m.sock` or in `$XDG_RUNTIME_DIR`).
- **`log_level`**: `INFO` by default. Change to `DEBUG` for deep diagnostics.
- **`max_retries`**: Connection retry attempts from frontend to backend.

---

## Secrets and Security

API keys are managed via environment variables or secure storage, never in plain text inside `config.toml` if possible.

```bash
# Define in .env or system environment
export GEMINI_API_KEY="AIzaSy_YOUR_KEY_HERE"
```

!!! warning "Important"
    Restart the daemon (`python -m v2m.main --daemon`) after manually editing the configuration file to apply changes.
