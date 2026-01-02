# 🔧 Troubleshooting

This guide compiles the most common problems and their solutions. If you find an error not listed here, please check the logs at `/tmp/v2m.log`.

---

## 🛑 Audio Issues

### "Microphone not detected" or Empty Recording
*   **Symptom**: System says "Recording started" but when stopped, nothing transcribes or gives error.
*   **Solution**:
    1.  Verify `ffmpeg` and `pactl` are installed.
    2.  Ensure your default system microphone is active and has volume.
    3.  Run `arecord -l` to list devices.

### Transcription cuts off phrases or words
*   **Cause**: VAD (Voice Activity Detection) may be too aggressive.
*   **Solution**:
    1.  Edit `config.toml`.
    2.  In `[whisper.vad_parameters]`, reduce `threshold` (e.g., to `0.3`) or increase `min_speech_duration_ms`.

---

## 🐢 Performance Issues

### Transcription is very slow (>5 seconds for short phrases)
*   **Cause**: Whisper is probably running on **CPU** instead of **GPU**.
*   **Diagnosis**: Run `python scripts/test_whisper_gpu.py`.
*   **Solution**:
    1.  Verify you have NVIDIA drivers and CUDA installed.
    2.  Reinstall `torch` with explicit CUDA support.
    3.  In `config.toml`, ensure `device = "cuda"`.

### `OutOfMemoryError` (OOM) on GPU
*   **Cause**: The `large-v3` model is too large for your VRAM.
*   **Solution**:
    1.  Change model in `config.toml` to `medium` or `small`.
    2.  Change `compute_type` to `int8_float16` (hybrid) if your card supports it.

---

## 🤖 Gemini (LLM) Issues

### "Authentication error" or "Invalid API Key"
*   **Solution**:
    1.  Verify `.env` file exists at root.
    2.  Ensure variable is named `GEMINI_API_KEY`.
    3.  Generate a new key at Google AI Studio.

### Refined text is worse than original
*   **Solution**:
    1.  Adjust `system_prompt` in `src/v2m/infrastructure/gemini_llm_service.py` (or in `prompts/` if externalized).
    2.  Lower `temperature` in `config.toml` to `0.1` to make it more deterministic.

---

## 📜 Logs and Debugging

To see what's happening in real-time:

```bash
# View live log
tail -f /tmp/v2m.log
```

If reporting a bug, please include the last lines from this file.
