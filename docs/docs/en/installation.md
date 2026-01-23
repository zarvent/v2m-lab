---
title: Installation and Setup
description: Step-by-step guide to installing Voice2Machine and its dependencies on Linux.
ai_context: "Installation, Linux, CUDA, Python 3.12, Rust"
depends_on: []
status: stable
---

# 🛠️ Installation and Setup

!!! note "Prerequisite"
This project is optimized for **Linux (Debian/Ubuntu)**.
**State of the Art 2026**: We use hardware acceleration (CUDA) and a modular approach to ensure privacy and performance.

This guide will take you from zero to a fully functional dictation system on your local machine.

---

## 🚀 Method 1: Automatic Installation (Recommended)

We've created a script that handles all the "dirty work" for you: verifies your system, installs dependencies (apt), creates the virtual environment (venv), and configures credentials.

```bash
# Run from the project root
./apps/daemon/backend/scripts/setup/install.sh
```

**What this script does:**

1.  📦 Installs system libraries (`ffmpeg`, `xclip`, `pulseaudio-utils`).
2.  🐍 Creates an isolated Python environment (`venv`).
3.  ⚙️ Installs project dependencies (`faster-whisper`, `torch`).
4.  🔑 Helps you configure your Gemini API Key (optional, for generative AI).
5.  🖥️ Verifies if you have a compatible NVIDIA GPU.

---

## 🛠️ Method 2: Manual Installation

If you prefer full control or the automatic script fails, follow these steps.

### 1. System Dependencies (System Level)

We need tools to manipulate audio and clipboard at the OS level.

```bash
sudo apt update
sudo apt install ffmpeg xclip pulseaudio-utils python3-venv build-essential python3-dev
```

### 2. Python Environment

We isolate libraries to avoid conflicts.

```bash
# Navigate to the backend directory
cd apps/daemon/backend

# Create virtual environment
python3 -m venv venv

# Activate environment (Do this every time you work on the project!)
source venv/bin/activate

# Install dependencies
pip install -e .
```

### 3. AI Configuration (Optional)

To use "Text Refinement" features (rewriting with LLM), you need a Google Gemini API Key.

1.  Get your key at [Google AI Studio](https://aistudio.google.com/).
2.  Create a `.env` file at the root:

```bash
echo 'GEMINI_API_KEY="your_api_key_here"' > .env
```

---

## ✅ Verification

Make sure everything works before continuing.

### 1. Verify GPU Acceleration

This confirms that Whisper can use your graphics card (essential for speed).

```bash
python apps/daemon/backend/scripts/diagnostics/check_cuda.py
```

### 2. System Diagnostics

Verify that the daemon and audio services are ready.

```bash
python apps/daemon/backend/scripts/diagnostics/health_check.py
```

---

## ⏭️ Next Steps

Once installed, it's time to configure how you interact with the tool.

- [Detailed Configuration](configuration.md) - Adjust models and sensitivity.
- [Keyboard Shortcuts](keyboard_shortcuts.md) - Configure your magic keys.
