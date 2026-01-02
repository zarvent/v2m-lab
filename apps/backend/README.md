# Backend Voice2Machine (Python Core)

The "brain" of the system. Handles business logic, audio processing, and AI inference.

## 🚀 Quick Start (Dev Mode)

If you already ran `install.sh` at the root, everything is set up. For manual development:

```bash
# 1. Activate virtual environment
cd apps/backend
source venv/bin/activate

# 2. Install dependencies in editable mode (useful for dev)
pip install -e .

# 3. Launch the Daemon (Server)
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
apps/backend/
├── src/v2m/
│   ├── application/    # Use cases (Commands/Handlers)
│   ├── core/           # Command bus and global configuration
│   ├── domain/         # Pure entities and exceptions
│   ├── infrastructure/ # Real implementations (Whisper, Gemini, Audio)
│   └── main.py         # Entrypoint
├── config.toml         # Default configuration
└── pyproject.toml      # Build and tooling configuration
```

## 🔌 Socket API

The backend exposes a Unix Socket at `/tmp/v2m.sock`.

**Protocol:**

1.  **Header**: 4 bytes (Big Endian) indicating message length.
2.  **Body**: JSON string encoded in UTF-8.

_Message example:_ `{"type": "toggle_recording"}`
