# Voice2Machine Backend (Python Core)

The "brain" of the system. Handles business logic, audio processing, and AI inference using State of the Art 2026 standards.

**⚠️ AI Agents & Developers**: Please refer to `AGENTS.md` for strict coding standards, mission, and boundaries.

## 🚀 Quick Start (Dev Mode)

### Automated Installation (Recommended)

Run the installer from **anywhere** in the project:

```bash
# From project root OR from scripts/
./scripts/install.sh
```

### Manual Development Setup

We use `uv` for blazing fast package management.

```bash
# 1. Navigate to backend
cd apps/backend

# 2. Create virtualenv
uv venv

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Install dependencies
uv pip install -e .

# 5. Launch the Daemon (Server)
python -m v2m.main --daemon
```

## 🏗️ Development Commands

See `AGENTS.md` for the preferred file-scoped commands.

```bash
# Check all
ruff check src/

# Test all
pytest tests/unit/
```

## 📦 Project Structure

```
apps/backend/src/v2m/
├── domain/          # Entities & Protocols
├── application/     # Use Cases & Handlers
├── infrastructure/  # Adapters (Audio, AI, OS)
├── core/            # Framework (DI, CQRS, Logging, IPC)
└── main.py          # Entrypoint
```

## 🔌 Socket API

The backend exposes a Unix Socket at `$XDG_RUNTIME_DIR/v2m/v2m.sock` (typically `/run/user/<uid>/v2m/v2m.sock`).

**Protocol:**
1.  **Header**: 4 bytes (Big Endian) indicating payload size.
2.  **Body**: JSON string (UTF-8).
