# Frontend Voice2Machine (Tauri + React)

State-of-the-art desktop GUI built with **Tauri 2.0** (Rust) and **React 19**.

## ⚡ Philosophy

- **Ultralight**: < 15MB binary. < 50MB RAM.
- **Secure**: We don't run Node.js at runtime. Everything goes through Rust's secure bridge.
- **Decoupled**: The GUI is just a "view". Heavy logic lives in the Python Daemon.

## 🛠️ Development Requirements

- **Node.js** 20+ (Recommended: use `fnm` or `nvm`).
- **Rust** (stable toolchain) to compile the Tauri backend.
- **System dependencies**: `libwebkit2gtk-4.1-dev` (on Ubuntu).

## 🧑‍💻 Commands

```bash
# 1. Install deps
npm install

# 2. Development Mode (Hot Reload)
# NOTE: Make sure the Python daemon is running to see real data.
npm run tauri dev

# 3. Production Build
npm run tauri build
```

The optimized binary will appear at `src-tauri/target/release/voice2machine`.

## 🧩 Frontend Architecture

```
apps/frontend/
├── src/
│   ├── components/    # Atomic React components
│   ├── hooks/         # Custom hooks (useSocket, useRecording)
│   ├── App.tsx        # Main layout (Glassmorphism)
│   └── main.tsx       # Entry point
├── src-tauri/
│   ├── src/lib.rs     # IPC Client (Rust -> Unix Socket -> Python)
│   └── tauri.conf.json # Permissions and window configuration
```

### IPC Communication

The GUI doesn't talk directly to Python.

1.  **React** invokes a Tauri command: `invoke('send_command', { cmd: 'start' })`.
2.  **Rust** intercepts the call.
3.  **Rust** writes to the Unix socket `/tmp/v2m.sock`.
4.  **Python** receives, processes, and responds.
5.  **Rust** returns the response to React.

This "dance" guarantees the UI never freezes, even if Python is busy transcribing 1 hour of audio.
