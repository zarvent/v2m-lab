# Backend Voice2Machine (Python Core)

The "brain" of the system. Handles business logic, audio processing, and AI inference.

## 🚀 Quick Start (Dev Mode)

### Automated Installation (Recommended)

Run the installer:

```bash
# From apps/daemon/backend/ scripts/setup/
./install.sh
```

### Manual Development Setup

```bash
# 1. Navigate to backend
cd apps/daemon/backend

# 2. Activate virtual environment
source venv/bin/activate

# 3. Install in editable mode (useful for dev)
uv pip install -e .  # or: pip install -e .

# 4. Launch the Daemon (Server)
# This will keep the process alive listening on /tmp/v2m.sock
python -m v2m.main --daemon
```

## 🏗️ Development Commands

We use modern tools to ensure code quality.

### Testing (Pytest)

```bash
# Fast unit tests
pytest tests/unit/

# Integration tests (requires GPU/Audio)
pytest tests/integration/
```

### Linting & Formatting (Ruff)

We use `ruff` (the fastest linter in the West) to replace flake8, isort, and black.

```bash
# Check and autofix
ruff check src/ --fix

# Format
ruff format src/
```

## 📦 Project Structure

```
apps/daemon/backend/
├── src/v2m/
│   ├── api/            # FastAPI (Routes, App, Schemas)
│   ├── features/       # Modular features (audio, llm, processing)
│   ├── orchestration/  # Business workflows (Recording, LLM)
│   ├── shared/         # Common logic (config, errors, interfaces)
│   └── main.py         # Entrypoint
├── config.toml         # Default configuration
└── pyproject.toml      # Build and tooling configuration
```

## 🔌 Socket API (DEPRECATED)

> **IMPORTANT**: The Unix Socket IPC has been replaced by **FastAPI** (REST/WebSocket).
> This section is kept for historical reference during the migration period.

The backend exposes a Unix Socket at `$XDG_RUNTIME_DIR/v2m/v2m.sock` (typically `/run/user/<uid>/v2m/v2m.sock`).

> **Note**: The socket location follows the XDG Base Directory Specification for secure, user-isolated runtime files.

**Protocol:**

1.  **Header**: 4 bytes (Big Endian) indicating message length.
2.  **Body**: JSON string encoded in UTF-8.

_Message example:_ `{"type": "toggle_recording"}`
