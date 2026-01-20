# Backend Development Guide

Instructions for setting up the development environment and contributing to the Voice2Machine daemon.

## 🛠️ Initial Setup

### Virtual Environment

The use of `venv` with Python 3.12 is recommended:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Configuration (config.toml)

The backend looks for a `config.toml` file in the project root to define the Whisper model (e.g., `large-v3-turbo`) and API keys for LLMs.

## ⌨️ Development Commands

### Execution

- **Daemon**: `python -m v2m.main --daemon`
- **CLI**: `python -m v2m.main transcribe file.wav`

### Quality (Ruff)

We are committed to the SOTA 2026 standard.

- **Check**: `ruff check .`
- **Formatting**: `ruff format .`

### Testing (Pytest)

- **All**: `pytest`
- **Unit**: `pytest tests/unit`
- **With coverage**: `pytest --cov=v2m`

## 🧪 Testing Strategy

1.  **Rigorous Mocks**: Never call real hardware (Microphone) or external APIs in unit tests. Use the `domain/` protocols to inject mocks.
2.  **Integration Tests**: Test that real adapters work with the daemon, ideally in controlled CI/CD environments with GPU support if possible.
