# ⚙️ Configuration Guide

> **File Location**: `apps/backend/config.toml` (looked up in local paths at runtime).

Voice2Machine exposes a granular configuration system for developers and power users, allowing tuning from inference latency to AI creativity.

---

## 1. Local Transcription (`[whisper]`)

The core of the system. These parameters control the **Faster-Whisper** engine.

| Parameter | Type | Description & 2026 Best Practice |
| :--- | :--- | :--- |
| `model` | `str` | Model to load. **Default**: `large-v3-turbo` (Current SOTA for speed/accuracy balance). Options: `distil-large-v3`, `medium`, `base`. |
| `device` | `str` | `cuda` (GPU) is mandatory for real-time experience. `cpu` is functional but slow. |
| `compute_type` | `str` | Tensor precision. `int8_float16` is standard for modern GPUs (saves VRAM without quality loss). Use `int8` for CPU. |
| `beam_size` | `int` | `5` is the gold standard. Defines how many decoding paths are explored in parallel. |
| `best_of` | `int` | `3`. Number of candidates to generate before picking the best one. Reduces hallucinations. |
| `temperature` | `float` | `0.0` (deterministic). Crucial to keep at 0 for faithful transcriptions. |

### Voice Activity Detection (`[whisper.vad_parameters]`)

The VAD system filters silence before transcription, drastically speeding up the process.

- **`threshold`** (`0.35`): Sensitivity. Lower = detects whispers but might catch background noise.
- **`min_speech_duration_ms`** (`250`): A sound must last at least 1/4 second to be considered speech.
- **`min_silence_duration_ms`** (`600`): How much silence to wait for before "cutting" a phrase.

---

## 2. LLM Refinement (`[gemini]` & `[llm]`)

Voice2Machine supports a hybrid approach: Cloud (Gemini) or Local (Llama/Qwen).

### Gemini (Cloud)
| Parameter | Default | Notes |
| :--- | :--- | :--- |
| `model` | `gemini-1.5-flash-latest` | Optimized for low latency. |
| `temperature` | `0.3` | Low creativity for style correction. Raise to `0.7` for creative rewriting. |
| `api_key` | `${GEMINI_API_KEY}` | **Security**: Injected from environment variables. |

### Local LLM (Total Privacy)
Configured under `[llm.local]`.
- **`model_path`**: Path to `.gguf` file (e.g., `models/qwen2.5-3b-instruct-q4_k_m.gguf`).
- **`n_gpu_layers`**: `-1` to offload everything to VRAM (max speed).

---

## 3. Notifications (`[notifications]`)

Controls system visual feedback (desktop popups).

- **`expire_time_ms`** (`3000`): Notifications vanish after 3 seconds.
- **`auto_dismiss`** (`true`): Forces closure via DBUS (useful in GNOME/Unity where notifications sometimes "stick").

---

## 4. System Paths (`[paths]`)

> ⚠️ **Danger Zone**: Changing this can break integration with bash scripts.

Temporary paths (`/tmp/v2m_*`) are defined for Inter-Process Communication (IPC) using files as semaphores and buffers. This ensures no residue remains on disk after a reboot.

---

## Secrets (`.env`)

API keys must **never** go in `config.toml`. Create a `.env` file at the root:

```bash
# .env
GEMINI_API_KEY="AIzaSy_YOUR_KEY_HERE"
```
