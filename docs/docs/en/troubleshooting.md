---
title: Troubleshooting
description: Diagnostic and resolution guide for common errors in Voice2Machine.
ai_context: "Troubleshooting, Logs, Common Errors, CUDA, Audio"
depends_on: []
status: stable
---

# 🔧 Troubleshooting

!!! danger "Golden Rule"
For any problem, the first step is always to check system logs.
`bash
    # View logs in real-time
    tail -f ~/.local/state/v2m/v2m.log
    `

---

## 🛑 Audio and Recording

### No sound / Empty transcription

- **Symptom**: Recording starts and stops, but no text is generated.
- **Diagnosis**:
  Run the audio diagnostic script:
  ```bash
  python scripts/diagnose_audio.py
  ```
- **Solutions**:
  1.  **Audio Driver**: Voice2Machine uses `SoundDevice`. Make sure your system (PulseAudio/PipeWire) has an active default microphone.
  2.  **Permissions**: On Linux, your user must belong to the `audio` group (`sudo usermod -aG audio $USER`).

### Cut-off or incomplete phrases

- **Cause**: The silence detector (VAD) is too aggressive.
- **Solution**:
  Adjust settings in `config.toml` or via the GUI:
  - Reduce the `threshold` (e.g., from `0.35` to `0.30`).
  - Increase `min_silence_duration_ms` (e.g., to `800ms`).

---

## 🐢 Performance and GPU

### Slow transcription (> 2 seconds)

- **Probable Cause**: Whisper is running on **CPU** instead of GPU.
- **Verification**:
  ```bash
  python scripts/test_whisper_gpu.py
  ```
- **Solution**:
  1.  Install updated NVIDIA drivers (CUDA 12 compatible).
  2.  Verify `config.toml` has `device = "cuda"`.
  3.  If you don't have a dedicated GPU, switch model to `distil-medium.en` or `base`.

### Error `CUDA out of memory`

- **Cause**: Your GPU doesn't have enough VRAM for the selected model.
- **Solution**:
  - Change `compute_type` to `int8_float16` (reduces VRAM usage by half).
  - Use a lighter model (`distil-large-v3` consumes less than original `large-v3`).

---

## 🔌 Connectivity and Daemon

### "Connection refused" in GUI or Scripts

- **Cause**: The backend process (Python) isn't running or the server crashed.
- **Solution**:
  1.  Verify status:
      ```bash
      pgrep -a python | grep v2m
      ```
  2.  If not running, start manually to see startup errors:
      ```bash
      python -m v2m.main
      ```
  3.  If it says "Address already in use", kill the existing process:
      ```bash
      pkill -f "v2m.main"
      ```

### Keyboard shortcuts don't respond

- **Cause**: Permission issue or incorrect path in window manager configuration.
- **Solution**:
  - Run the script manually in terminal: `scripts/v2m-toggle.sh`.
  - If it works, the error is in your shortcut configuration (e.g., relative path `~/` instead of `/home/...`).
  - If it doesn't work, verify permissions: `chmod +x scripts/*.sh`.

---

## 🧠 AI Errors (LLM)

### Error 401/403 with Gemini

- **Cause**: Invalid or expired API Key.
- **Solution**: Regenerate your key at Google AI Studio and update the `.env` file or `GEMINI_API_KEY` environment variable.

### "Connection refused" with Ollama

- **Cause**: The Ollama server isn't running.
- **Solution**: Run `ollama serve` in another terminal.
