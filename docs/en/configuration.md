# ⚙️ Configuration Guide

**Voice2Machine** is highly configurable through the `config.toml` file located at the project root. This file allows adjusting AI model behavior, system paths, and recording parameters.

---

## `config.toml` Structure

The file is divided into logical sections. Below explains each parameter in detail.

### `[paths]`

Defines critical paths for system operation.

| Parameter        | Description                                                          | Default Value                                |
| :--------------- | :------------------------------------------------------------------- | :------------------------------------------- |
| `recording_flag` | Temporary file used as semaphore to indicate recording status.       | `/tmp/v2m_recording.pid`                     |
| `audio_file`     | Path where recorded audio is temporarily saved before transcription. | `/tmp/v2m_audio.wav`                         |
| `log_file`       | Log file path for debugging.                                         | `/tmp/v2m.log`                               |
| `venv_path`      | Path to Python virtual environment.                                  | Auto-detected: `<project>/apps/backend/venv` |

### `[whisper]`

Configuration for the local transcription engine (Whisper).

| Parameter      | Description                                                        | Recommendation                                                       |
| :------------- | :----------------------------------------------------------------- | :------------------------------------------------------------------- |
| `model`        | Whisper model size to use.                                         | `large-v3-turbo` (best quality), `medium` (balanced), `base` (fast). |
| `device`       | Compute device.                                                    | `cuda` (NVIDIA GPU), `cpu` (Slow).                                   |
| `compute_type` | Calculation precision.                                             | `float16` (GPU), `int8` (CPU).                                       |
| `beam_size`    | Beam search size for decoding. Higher is more accurate but slower. | `3` - `5`                                                            |
| `vad_filter`   | Enables Whisper's internal voice activity detection (VAD) filter.  | `true`                                                               |

### `[whisper.vad_parameters]`

Fine-tuning for VAD (Voice Activity Detection) to truncate silences.

- `threshold`: Probability threshold to consider a segment as speech (0.5).
- `min_speech_duration_ms`: Minimum duration to consider as speech (250ms).

### `[gemini]`

Configuration for text refinement service with Google Gemini.

| Parameter     | Description                                                                        |
| :------------ | :--------------------------------------------------------------------------------- |
| `model`       | Gemini model identifier.                                                           |
| `temperature` | Model creativity (0.0 - 1.0). For text correction, use low values (0.3).           |
| `max_tokens`  | Token limit for response.                                                          |
| `api_key`     | **DO NOT EDIT**. Automatically read from `${GEMINI_API_KEY}` environment variable. |

---

## Environment Variables (`.env`)

For security, sensitive credentials don't go in `config.toml`, but in a `.env` file not shared in the repository.

```ini
# .env
GEMINI_API_KEY="AIzaSy..."
```
