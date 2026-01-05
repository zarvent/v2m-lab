# Voice2Machine (V2M) - Instructions for Agents

> **Context**: You are working on a Hexagonal Architecture project (Python Backend + Tauri Frontend).
> **Objective**: Maintain "State of the Art 2026" code quality standards. High cohesion, low coupling, zero technical debt.

---

## 🧠 Core Philosophy

1.  **Local-First**: Privacy is supreme. Audio never leaves the machine.
2.  **Modular**: The Daemon is the core. GUI and Scripts are just clients.
3.  **Hexagonal**: Dependencies point inwards. `Domain` knows nothing about `Infrastructure`.

---

## 🛠️ Tools and Commands

### Backend (Python 3.12+)
*   **Run**: `python -m v2m.main --daemon`
*   **Test**: `pytest tests/` (Unit: `tests/unit`, Integration: `tests/integration`)
*   **Lint**: `ruff check src/ --fix` (Strict rules enabled)
*   **Format**: `ruff format src/`

### Frontend (Tauri 2 + React 19)
*   **Dev**: `npm run tauri dev`
*   **Build**: `npm run tauri build`
*   **Check**: `tsc --noEmit`

### Scripts
*   **Install**: `./scripts/install.sh` (Idempotent)
*   **Verify**: `python scripts/verify_daemon.py`

---

## 🏗️ Architecture Guides

### Directory Structure
```
apps/backend/src/v2m/
├── core/           # DI Container, Event Bus (CQRS)
├── domain/         # Entities, Ports (Protocols), Errors
├── application/    # Command Handlers (Use Cases)
└── infrastructure/ # Concrete Implementations (Whisper, SoundDevice)
```

### Rules
1.  **Interfaces in Domain/Application**: Use `typing.Protocol` with `@runtime_checkable` instead of `abc.ABC` for structural decoupling.
2.  **No "God Classes"**: Divide responsibilities (e.g., `AudioRecorder` vs `TranscriptionService`).
3.  **Type Hints**: 100% coverage required.
4.  **AsyncIO**: The core is asynchronous. Do not block the event loop (use `asyncio.to_thread` or dedicated executors for CPU/GPU intensive tasks).

---

## 🧪 Testing Strategy

1.  **Unit Tests**: Mock all infrastructure. Test logic in `application/`.
2.  **Integration Tests**: Test real infrastructure (GPU, Audio) in isolated scripts or `tests/integration/`.
3.  **Golden Rule**: If you fix a bug, add a test that reproduces it.

---

## 🚨 Common Errors

- **Hardcoded Paths**: NEVER use absolute paths like `/home/user`. Use `v2m.utils.paths.get_secure_runtime_dir`.
- **Blocking the Loop**: Do not use `time.sleep()`. Use `await asyncio.sleep()`.
- **Git Commits**: Use Conventional Commits (`feat:`, `fix:`, `refactor:`).

---

## 🤖 AI Context
When generating code:
- Prefer **Pydantic V2** for data validation.
- Use robust error handling (`ApplicationError` hierarchy).
- Assume a **CUDA 12** context for GPU operations.
- **Language**: All documentation and comments must be in Native Latin American Spanish.
