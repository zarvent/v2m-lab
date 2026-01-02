# 🛠️ Installation and Setup

This guide details the steps to deploy **Voice2Machine** on a Linux environment. The process covers system dependencies, Python environment setup, and AI credentials.

---

## 1. System Requirements

Before starting, ensure you have the following system-level tools installed. These are essential for audio capture and clipboard management.

```bash
sudo apt update
sudo apt install ffmpeg xclip pactl python3-venv build-essential python3-dev
```

### GPU Support (NVIDIA)
For optimal Whisper performance, GPU acceleration is **critical**.
*   **NVIDIA Drivers**: Ensure you have the latest drivers installed.
*   **CUDA Toolkit**: Required for `faster-whisper` and `torch`.

> **note**: if you don't have an NVIDIA GPU, it will work on CPU but will be much slower.

---

## 2. Python Environment

It's strongly recommended to use a virtual environment to isolate project dependencies.

### Creation and Activation

```bash
# 1. Create virtual environment at project root
python3 -m venv venv

# 2. Activate the environment
source venv/bin/activate
```

### Installing Dependencies

```bash
# 3. Install required packages
pip install -r requirements.txt
```

---

## 3. AI Credentials (Google Gemini)

For text refinement functionality (`process-clipboard`), a Google Gemini API Key is required.

1.  Get your key at [Google AI Studio](https://aistudio.google.com/).
2.  Create a `.env` file at the project root.
3.  Add your key following this format:

```bash
echo 'GEMINI_API_KEY="your_api_key_here"' > .env
```

---

## 4. Verifying Installation

To confirm all components are correctly configured, run the included diagnostic scripts.

### Verify Dependencies and Audio
```bash
python scripts/verify_daemon.py
```

### Verify GPU Acceleration
This script loads a small Whisper model to confirm `cuda` is available and functional.
```bash
python scripts/test_whisper_gpu.py
```
