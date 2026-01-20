# Voice2Machine Backend

AI agent instructions for the core daemon and backend services.

**Architecture**: Modular Monolith + FastAPI REST
**Language**: Python 3.12+ (Asyncio-native, uvloop)
**Privacy**: Local-first, no telemetry

---

## Quick Start

```bash
# Start the server
./scripts/operations/daemon/start_daemon.sh

# Test with curl
curl -X POST http://localhost:8765/toggle  # Toggle recording
curl http://localhost:8765/status          # Get status
curl http://localhost:8765/docs            # API documentation
```

---

## Commands (File-Scoped)

Prioritize these over full-project runs.

```bash
# Lint single file
ruff check src/v2m/path/to/file.py --fix

# Format single file
ruff format src/v2m/path/to/file.py

# Test single file
venv/bin/pytest tests/unit/path/to/test_file.py -v

# Run server
python -m v2m.main              # Start FastAPI server
python -m v2m.main toggle       # Send toggle command
```

> **Full builds only on explicit request.**

---

## Tech Stack

| Component      | Version/Tool                                          |
| -------------- | ----------------------------------------------------- |
| Language       | Python 3.12+ with `asyncio`                           |
| **API Server** | **FastAPI + Uvicorn** (replaces IPC sockets)          |
| Event Loop     | `uvloop` (installed on startup)                       |
| Validation     | Pydantic V2                                           |
| Linting        | Ruff (SOTA 2026)                                      |
| Testing        | Pytest + `pytest-asyncio`                             |
| Audio          | Rust `v2m_engine` (primary), `sounddevice` (fallback) |
| ML             | `faster-whisper`, Google GenAI (Gemini)               |

---

## Project Structure (Simplified)

```
src/v2m/
├── api.py               # FastAPI endpoints (Junior-friendly)
├── main.py              # Entry point (uvicorn runner)
├── config.py            # Pydantic Settings
├── services/
│   └── orchestrator.py  # Business logic (replaces 10 handlers)
├── infrastructure/      # Adapters: Whisper, Audio, LLM
│   ├── audio/recorder.py           # Rust/Python hybrid
│   ├── persistent_model.py         # Whisper "always warm"
│   ├── streaming_transcriber.py    # Real-time inference
│   ├── gemini_llm_service.py       # Gemini backend
│   ├── linux_adapters.py           # Clipboard (X11/Wayland)
│   └── notification_service.py     # D-Bus notifications
├── core/
│   ├── interfaces.py    # Protocols (typing.Protocol)
│   ├── logging.py       # Logger config
│   └── client_session.py # WebSocket event broadcast
└── domain/              # Entities (Pydantic models)
```

**Eliminated (CQRS → Direct Calls):**

- ~~core/cqrs/~~ → `services/orchestrator.py`
- ~~core/di/container.py~~ → Lazy singletons in orchestrator
- ~~daemon.py, client.py~~ → `api.py` (FastAPI)
- ~~ipc_protocol.py~~ → HTTP REST

---

## API Endpoints

| Endpoint         | Method | Description                |
| ---------------- | ------ | -------------------------- |
| `/toggle`        | POST   | Start/stop recording       |
| `/start`         | POST   | Start recording explicitly |
| `/stop`          | POST   | Stop and transcribe        |
| `/llm/process`   | POST   | Process text with LLM      |
| `/llm/translate` | POST   | Translate text             |
| `/status`        | GET    | Daemon state               |
| `/health`        | GET    | Health check               |
| `/ws/events`     | WS     | Streaming events           |
| `/docs`          | GET    | Swagger UI                 |

---

## Performance Architecture

### Phase 1: Rust-Python Bridge

- Audio capture via `v2m_engine` (lock-free ring buffer, GIL-free)
- `wait_for_data()` is awaitable—no polling
- Fallback to `sounddevice` if Rust not compiled

### Phase 2: Persistent Model Worker

- `PersistentWhisperWorker` keeps model in VRAM ("always warm")
- GPU ops isolated in dedicated `ThreadPoolExecutor`
- Memory pressure detection via `psutil` (>90% triggers unload)

### Phase 3: Streaming Inference

- `StreamingTranscriber` emits provisional text every 500ms
- WebSocket broadcast at `/ws/events`
- Events: `transcription_update`, `heartbeat`

### Phase 4: Async Hygiene

- `uvloop.install()` on server startup
- No sync I/O in hot paths
- Lazy service initialization for fast startup

---

## Code Standards

### Junior-Friendly Patterns

```python
# ✅ Direct method calls (easy to trace)
text = await orchestrator.toggle()

# ❌ CQRS indirection (removed)
# bus.dispatch(ToggleRecordingCommand())
```

### Async Non-Blocking

```python
# ❌ NEVER
time.sleep(1)
open("file.txt").read()

# ✅ ALWAYS
await asyncio.sleep(1)
await aiofiles.open("file.txt")

# GPU/CPU intensive → offload to executor
await asyncio.to_thread(heavy_computation)
```

---

## Testing Guidelines

- **Unit Tests**: Mock infrastructure adapters
- **Integration**: Test endpoints with `httpx.AsyncClient`
- **Coverage**: Target >80% for services/orchestrator

```bash
# Run all unit tests
venv/bin/pytest tests/unit/ -v

# Test API endpoints
venv/bin/pytest tests/integration/ -v
```

---

## Git & PR Standards

- **Commit**: `[scope]: behavior` (e.g., `api: add translate endpoint`)
- **PR Check**: `ruff check` + `ruff format` must pass

---

## Boundaries

### ✅ Always do

- Test endpoints with `curl` before committing
- Verify `ruff` passes on every modified file
- Use `logger.info/debug` for trace-level info

### ⚠️ Ask first

- Adding dependencies to `pyproject.toml`
- Changing `config.toml` schema
- Full project builds

### 🚫 Never do

- **Commit secrets**: No API keys in code
- **Block the loop**: No sync I/O in async handlers
- **Push to main**: Always use PRs

---

## Security Considerations

- **No telemetry**: All processing is local
- **Secrets**: Use environment variables (`GEMINI_API_KEY`)
- **Server**: Binds to `127.0.0.1` only (not exposed to network)
- **Config**: Validate with Pydantic before use

---

## 📚 Official Documentation References

| Technology         | Documentation URL                                                                |
| ------------------ | -------------------------------------------------------------------------------- |
| **FastAPI**        | [fastapi.tiangolo.com](https://fastapi.tiangolo.com/)                            |
| **Uvicorn**        | [uvicorn.org](https://www.uvicorn.org/)                                          |
| **Python**         | [docs.python.org/3.12](https://docs.python.org/3.12/)                            |
| **Pydantic**       | [docs.pydantic.dev](https://docs.pydantic.dev/latest/)                           |
| **faster-whisper** | [github.com/SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)   |
| **Google GenAI**   | [ai.google.dev/api/python](https://ai.google.dev/api/python/google/generativeai) |
