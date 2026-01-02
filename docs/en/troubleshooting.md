# 🔧 Troubleshooting Guide

This guide collects common issues and their solutions. **Golden Rule**: Always check the logs first.

```bash
tail -f /tmp/v2m.log
```

---

## 🛑 Audio Issues

### "Recording started" but nothing transcribes
*   **Symptom**: System beeps, you talk, system beeps again, but clipboard is empty or error notification appears.
*   **Cause**: Input device is muted or not selected.
*   **Solution**:
    1.  Run `python scripts/diagnose_audio.py` to see a VU meter.
    2.  Check system privacy settings (Microphone access).
    3.  Verify `ffmpeg` is installed.

### Cut-off phrases
*   **Cause**: VAD (Voice Activity Detection) is too aggressive.
*   **Solution**:
    *   Edit `config.toml`.
    *   Lower `[whisper.vad_parameters] threshold` (e.g., to `0.3`).
    *   Increase `min_silence_duration_ms` to `800`.

---

## 🐢 Performance Issues

### Transcription is slow (>5s for short phrases)
*   **Cause**: Whisper is likely running on **CPU**.
*   **Diagnostic**: Run `python scripts/test_whisper_gpu.py`.
*   **Solution**:
    1.  Install NVIDIA drivers & CUDA Toolkit 12+.
    2.  Ensure `device = "cuda"` in `config.toml`.
    3.  If you *must* use CPU, switch to `model = "base"` and `compute_type = "int8"`.

### `OutOfMemoryError` (OOM)
*   **Cause**: `large-v3-turbo` requires ~4GB VRAM.
*   **Solution**:
    *   Switch to `medium` model.
    *   Use `compute_type = "int8_float16"`.

---

## 🤖 AI / LLM Issues

### "Authentication Error"
*   **Solution**:
    1.  Check `.env` file exists.
    2.  Verify variable is named `GEMINI_API_KEY`.
    3.  Regenerate key at Google AI Studio.

### Bad quality output from Refinement
*   **Solution**:
    *   Lower `temperature` to `0.1`.
    *   Check if you are selecting the text correctly before triggering the shortcut.

---

## 🖥️ Daemon / Connectivity

### "Connection Refused" (Socket Error)
*   **Symptom**: CLI or GUI complains about `/tmp/v2m.sock`.
*   **Cause**: The daemon is not running.
*   **Solution**:
    ```bash
    # Start it manually to see errors
    python -m v2m.main --daemon
    ```
    If it crashes immediately, check for another instance:
    ```bash
    pkill -f v2m.main
    rm /tmp/v2m.sock
    ```
