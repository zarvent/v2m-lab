# Voice2Machine Backend

AI agent instructions for the core daemon and backend services.

**Architecture**: Hexagonal (Ports & Adapters) + 4-Phase Performance Pipeline
**Language**: Python 3.12+ (Asyncio-native, uvloop)
**Privacy**: Local-first, no telemetry

---

## Commands (File-Scoped)

Prioritize these over full-project runs.

```bash
# Lint single file
ruff check src/v2m/path/to/file.py --fix

# Format single file
ruff format src/v2m/path/to/file.py

# Type check (via LSP or)
# ruff integrates type checking

# Test single file
venv/bin/pytest tests/unit/path/to/test_file.py -v

# Run daemon
python -m v2m.main --daemon
```

> **Full builds only on explicit request.**

---

## Tech Stack

| Component | Version/Tool |
|-----------|--------------|
| Language | Python 3.12+ with `asyncio` |
| Event Loop | `uvloop` (installed on daemon startup) |
| Validation | Pydantic V2 |
| Linting | Ruff (SOTA 2026) |
| Testing | Pytest + `pytest-asyncio` |
| Serialization | `orjson` (3-10x faster than stdlib) |
| Audio | Rust `v2m_engine` (primary), `sounddevice` (fallback) |
| ML | `faster-whisper`, Google GenAI (Gemini) |

---

## Project Structure

```
src/v2m/
├── domain/          # Entities & Protocols. ZERO external deps (except Pydantic)
├── application/     # Handlers, use cases. Orchestrates domain logic
├── infrastructure/  # Adapters: Whisper, Audio, LLM, FileSystem
│   ├── audio/       # AudioRecorder (Rust/Python hybrid)
│   ├── persistent_model.py      # Whisper "always warm" worker
│   └── streaming_transcriber.py # Real-time inference loop
├── core/            # DI container, IPC protocol, logging
│   ├── di/container.py
│   ├── ipc_protocol.py
│   └── client_session.py
└── main.py          # Entry point
```

---

## Performance Architecture (4 Phases)

### Phase 1: Rust-Python Bridge
- Audio capture via `v2m_engine` (lock-free ring buffer, GIL-free)
- `RustAudioStream` implements `AsyncIterator`
- `wait_for_data()` is awaitable—no polling

### Phase 2: Persistent Model Worker
- `PersistentWhisperWorker` keeps model in VRAM ("always warm")
- GPU ops isolated in dedicated `ThreadPoolExecutor`
- Memory pressure detection via `psutil` (>90% triggers unload)

### Phase 3: Streaming Inference
- `StreamingTranscriber` emits provisional text every 500ms
- `ClientSessionManager` handles event push to clients
- Protocol: `status="event"` (provisional) → `status="success"` (final)

### Phase 4: Async Hygiene
- `uvloop.install()` on daemon startup
- `orjson` for fast IPC serialization
- No sync I/O in hot paths

---

## Code Standards

### Hexagonal Boundaries
- **Inward pointing**: Domain knows nothing about Infrastructure
- **Protocols over Classes**: Use `typing.Protocol` in `domain/`

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
await loop.run_in_executor(self._executor, func)
```

### Concrete Example: Domain Entity
```python
# src/v2m/domain/entities.py
from pydantic import BaseModel, ConfigDict

class Transcription(BaseModel):
    model_config = ConfigDict(frozen=True)  # Immutable
    text: str
    confidence: float
    language: str
```

### Concrete Example: Async Handler
```python
# src/v2m/application/command_handlers.py
async def handle(self, command: StopRecordingCommand) -> str | None:
    # Async service call—no blocking
    transcription = await self.transcription_service.stop_and_transcribe()
    self.clipboard_service.copy(transcription)
    return transcription
```

---

## Testing Guidelines

- **Unit Tests**: Mock ALL infrastructure adapters
- **Behavioral**: Verify "what the system does", not implementation details
- **Coverage**: Target >80% for domain/application logic
- **Async Tests**: Use `@pytest.mark.asyncio` decorator

```bash
# Run all unit tests
venv/bin/pytest tests/unit/ -v

# Run with coverage
venv/bin/pytest tests/unit/ --cov=src/v2m --cov-report=term-missing
```

---

## Git & PR Standards

- **Commit**: `[scope]: behavior` (e.g., `infra/whisper: fix VAD sensitivity`)
- **PR Check**: `ruff check` + `ruff format` must pass
- **Diff**: Small, focused changes with brief summaries

---

## Boundaries

### ✅ Always do
- Read `domain/` protocols before implementing adapters
- Verify `ruff` passes on every modified file
- Use `logger.info/debug` for trace-level info
- Run single-file tests before committing

### ⚠️ Ask first
- Adding dependencies to `pyproject.toml`
- Modifying DI container or Event Bus
- Changing `config.toml` schema
- Full project builds

### 🚫 Never do
- **Commit secrets**: No API keys, tokens, or credentials in code
- **Hardcode paths**: Use `v2m.utils.paths` or `get_secure_runtime_dir()`
- **Block the loop**: No sync I/O in async handlers
- **Delete node_modules/venv**: Ask first
- **Push to main**: Always use PRs

---

## Security Considerations

- **No telemetry**: All processing is local
- **Secrets**: Use environment variables (`GEMINI_API_KEY`)
- **IPC**: Unix socket with 1MB payload limit (DoS protection)
- **Config**: Validate with Pydantic before use

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Pydantic V1 syntax | Use V2 exclusively (`model_config`, `ConfigDict`) |
| Circular imports | Import from `domain/` into `application/`, never vice-versa |
| CUDA context | Prefer `faster-whisper` abstractions over raw PyTorch |
| Sync in async | Offload blocking calls to `asyncio.to_thread` |
| MagicMock for async | Use `AsyncMock` for async methods |
