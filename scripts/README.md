# 🛠️ Utility Scripts (Ops & Maint)

Curated collection of tools for the **Voice2Machine** lifecycle.
From installation to deep diagnostics.

## 🚀 Core Scripts (Daily Use)

| Script          | Purpose                                                                      |
| :-------------- | :--------------------------------------------------------------------------- |
| `v2m-daemon.sh` | **The Service**. Starts/Stops the backend in the background.                 |
| `v2m-toggle.sh` | **The Trigger**. Toggles (Start/Stop) recording. Map to keyboard shortcut.   |
| `v2m-llm.sh`    | **The AI**. Takes the clipboard, refines it with Gemini, and pastes it back. |

## 🩺 Diagnostics and Benchmarks

If something fails, run this before opening an issue.

- **`check_cuda.py`**: Is your GPU visible to PyTorch?
- **`diagnose_audio.py`**: Console VU meter. Verifies if your mic is picking up sound.
- **`benchmark_latency.py`**: Measures exact milliseconds of "Cold Start" vs "Warm Start".
- **`test_whisper_gpu.py`**: Downloads a "tiny" model and transcribes a test audio.
- **`verify_daemon.py`**: End-to-end integration test. Simulates a client connecting to the socket.

## 🧹 Maintenance

- **`cleanup.py`**: Deletes logs, temporary files (`/tmp/v2m_*`), and corrupt model cache.
- **`install.sh`**: The "magic" idempotent installation script.
