# 🛠️ Installation and Setup

> **Prerequisite**: Linux (Debian/Ubuntu/Fedora/Arch)
> **SOTA 2026**: Uses GPU acceleration (CUDA), uv package manager, and Tauri for native performance.

---

## 🚀 Method 1: Automatic Installation (Recommended)

```bash
# From project root
./scripts/install.sh
```

**Options:**

```bash
./scripts/install.sh --help          # Show all options
./scripts/install.sh --skip-frontend # Backend only
./scripts/install.sh --skip-gpu      # Skip GPU verification
```

**What it does:**

1. ✅ Verifies Python 3.12+, Node.js 18+, Rust
2. 📦 Installs system libraries (`ffmpeg`, `xclip`)
3. 🐍 Creates Python venv and installs backend
4. ⚛️ Installs frontend dependencies (npm)
5. 🔑 Configures Gemini API key (optional)
6. 🖥️ Verifies NVIDIA GPU

---

## 🛠️ Method 2: Manual Installation

### 1. Prerequisites

```bash
# Python 3.12+
sudo apt install python3.12 python3.12-venv

# Node.js 20+ (for frontend)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs

# Rust (for Tauri)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# System dependencies
sudo apt install ffmpeg xclip pulseaudio-utils build-essential
```

### 2. Backend Setup

```bash
cd apps/backend

# Create and activate venv
python3.12 -m venv venv
source venv/bin/activate

# Install (editable mode)
pip install -e .
```

### 3. Frontend Setup

```bash
cd apps/frontend
npm install
```

### 4. Configure Gemini (Optional)

```bash
cd apps/backend
echo 'GEMINI_API_KEY="your_key_here"' > .env
```

Get your key at [Google AI Studio](https://aistudio.google.com/).

---

## ✅ Running the Application

**Terminal 1 - Backend:**

```bash
cd apps/backend
source venv/bin/activate
python -m v2m.main --daemon
```

**Terminal 2 - Frontend:**

```bash
cd apps/frontend
npm run tauri dev
```

---

## 🎯 Verification

```bash
# Check daemon is running
ls /run/user/$(id -u)/v2m/v2m.sock

# Check GPU (optional)
nvidia-smi
```

---

## ⏭️ Next Steps

- [Configuration](configuration.md) - Adjust Whisper model, LLM settings
- [Keyboard Shortcuts](../atajos_teclado.md) - Setup global hotkeys
- [Troubleshooting](troubleshooting.md) - Common issues
