# Voice2Machine Backend

**Mission**: Provide a low-latency, privacy-first AI backend that orchestrates audio processing and intelligence locally using State of the Art 2026 standards.

---

## Tech Stack

| Component | Version/Tool |
|-----------|--------------|
| Language | Python 3.12+ (Asyncio-native) |
| Runtime | `uv` (Package Manager), `uvloop` (Event Loop) |
| Validation | Pydantic V2 (Strict Schema) |
| Linting | Ruff (SOTA 2026) |
| Testing | Pytest + `pytest-asyncio` |
| Audio/VAD | Rust `v2m_engine` (Primary) |
| ML/AI | `faster-whisper`, Google GenAI, Ollama |

---

## Commands (File-Scoped)

**Performance Rule**: Always prefer file-scoped commands over full-project builds to reduce feedback latency.

```bash
# Lint & Fix single file
ruff check src/v2m/path/to/file.py --fix

# Format single file
ruff format src/v2m/path/to/file.py

# Test single file
pytest tests/unit/path/to/test_file.py -v

# Run Daemon (Dev Mode)
python -m v2m.main --daemon
```

---

## Project Structure

```
src/v2m/
├── domain/          # Pure Entities & Protocols. ZERO external deps.
├── application/     # Use Cases, Command Handlers. Orchestration.
├── infrastructure/  # Adapters: Audio, LLM, Filesystem, Notifications.
│   ├── audio/       # AudioRecorder
│   └── system_monitor.py # Rust-accelerated monitoring
├── core/            # Framework services (DI, Logging, IPC).
│   ├── cqrs/        # Command/Query Buses
│   ├── providers/   # Dependency Injection Providers
│   ├── logging.py   # Structured JSON Logging
│   └── ipc_protocol.py
└── main.py          # Entry point
```

---

## Observability (SOTA 2026)

### 1. Structured Logging
All logs are emitted as JSON via `v2m.core.logging`.
- **Format**: `{"asctime": "...", "name": "v2m", "levelname": "INFO", "message": "..."}`
- **Usage**:
  ```python
  from v2m.core.logging import logger
  logger.info("process_started", extra={"job_id": 123})
  ```

### 2. System Monitor
Real-time resource tracking via `v2m.infrastructure.system_monitor`.
- **Layer 1**: Rust `v2m_engine` (No GIL, instant RAM/CPU/Temp metrics).
- **Layer 2**: `psutil`/`torch` fallback.
- **Optimization**: Static info is cached; GPU check uses memoized `torch` reference.

---

## Code Standards

### Hexagonal Architecture
- **Dependency Rule**: `domain` -> `application` -> `infrastructure`. Never the reverse.
- **Protocols**: Define interfaces in `domain` or `core/interfaces.py`.

### Async Hygiene
- **Blocking I/O**: 🚫 Forbidden in `async def`. Use `asyncio.to_thread`.
- **Files**: Use `aiofiles`.
- **Sleep**: `await asyncio.sleep()`.

---

## Boundaries

### ✅ Always
- Run `ruff check` on modified files.
- Use `logger.info` with structured `extra={}` data.
- Verify `v2m_engine` integration when touching audio logic.

### ⚠️ Ask First
- Adding new `pip` dependencies.
- Modifying `config.toml` structure.
- Changing IPC protocol headers.

### 🚫 Never
- Commit secrets (API keys).
- Use `print()` (Use `logger`).
- Hardcode absolute paths (Use `v2m.utils.paths`).

---

## Git Workflow
- **Commit**: `scope: description` (e.g., `infra/monitor: fix gpu cache`).
- **PRs**: Atomic changes. Verify tests pass.
