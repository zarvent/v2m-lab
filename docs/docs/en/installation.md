# 🛠️ Installation and Setup

> **Prerequisite**: This project is optimized for **Linux (Debian/Ubuntu)**.
> **State of the Art 2026**: We use hardware acceleration (CUDA) and a modular approach to guarantee privacy and performance.

This guide will take you from zero to a fully functional dictation system on your local machine.

---

## 🚀 Method 1: Automatic Installation (Recommended)

We have created a script that handles all the "heavy lifting" for you: checks your system, installs dependencies (apt), creates the virtual environment (venv), and configures credentials.

```bash
# Run from the project root
./scripts/install.sh
```

**What this script does:**
1.  📦 Installs system libraries (`ffmpeg`, `xclip`, `pulseaudio-utils`).
2.  🐍 Creates an isolated Python environment (`venv`).
3.  ⚙️ Installs project dependencies (`faster-whisper`, `torch`).
4.  🔑 Helps you configure your Gemini API Key (optional, for generative AI).
5.  🖥️ Checks if you have a compatible NVIDIA GPU.

---

## 🛠️ Method 2: Manual Installation

If you prefer total control or the automatic script fails, follow these steps.

### 1. System Dependencies

We need tools to manipulate audio and the clipboard at the OS level.

```bash
sudo apt update
sudo apt install ffmpeg xclip pulseaudio-utils python3-venv build-essential python3-dev
```

### 2. Python Environment

We isolate libraries to avoid conflicts.

```bash
# Create virtual environment
python3 -m venv venv

# Activate environment (Do this every time you work on the project!)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. AI Configuration (Optional)

To use the "Text Refinement" features (LLM rewriting), you need a Google Gemini API Key.

1.  Get your key at [Google AI Studio](https://aistudio.google.com/).
2.  Create a `.env` file at the root:

```bash
echo 'GEMINI_API_KEY="your_api_key_here"' > .env
```

---

## ✅ Verification

Ensure everything works before proceeding.

**1. Verify GPU Acceleration**
This confirms that Whisper can use your graphics card (essential for speed).
```bash
python scripts/test_whisper_gpu.py
```

**2. System Diagnostic**
Verifies that the daemon and audio services are ready.
```bash
python scripts/verify_daemon.py
```

---

## ⏭️ Next Steps

Once installed, it's time to configure how you interact with the tool.

- [Detailed Configuration](configuration.md) - Adjust models and sensitivity.
- [Keyboard Shortcuts](troubleshooting.md) - (Note: Check the Spanish docs for keybindings if missing here, or refer to `docs/atajos_teclado.md` translated).
