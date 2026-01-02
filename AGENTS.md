# Voice2Machine (V2M) - Agent Instructions

> **Context**: You are working in a Hexagonal Architecture project (Python Backend + Tauri Frontend).
> **Goal**: Maintain 2026 Code Quality Standards. High cohesion, low coupling, zero technical debt.

---

## 🧠 Core Philosophy

1.  **Local-First**: Privacy is paramount. Audio never leaves the machine.
2.  **Modular**: The Daemon is the core. The GUI and Scripts are just clients.
3.  **Hexagonal**: Dependencies point inward. The `Domain` knows nothing about `Infrastructure`.

---

## 🛠️ Toolchain & Commands

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

## 🏗️ Architecture Guidelines

### Directory Structure
```
apps/backend/src/v2m/
├── core/           # DI Container, Event Bus
├── domain/         # Entities, Ports (Interfaces), Errors
├── application/    # Command Handlers (Use Cases)
└── infrastructure/ # Concrete Implementations (Whisper, SoundDevice)
```

### Rules
1.  **Interfaces defined in Domain**: `infrastructure` implements them. `application` uses them.
2.  **No "God Classes"**: Split responsibilities (e.g., `AudioRecorder` vs `TranscriptionService`).
3.  **Type Hints**: 100% coverage required. Use `typing.Protocol` for interfaces.
4.  **AsyncIO**: The core is async. Do not block the event loop with heavy computation (offload to threads/processes if needed, though `faster-whisper` handles this well).

---

## 🧪 Testing Strategy

1.  **Unit Tests**: Mock all infrastructure. Test logic in `application/`.
2.  **Integration Tests**: Test real infrastructure (GPU, Audio) in isolated scripts or `tests/integration/`.
3.  **Golden Rule**: If you fix a bug, add a test case that reproduces it.

---

## 🚨 Common Pitfalls

- **Hardcoded Paths**: NEVER use absolute paths like `/home/user`. Use `pathlib` relative to project root or config.
- **Blocking the Loop**: Don't use `time.sleep()`. Use `await asyncio.sleep()`.
- **Git Commits**: Use Conventional Commits (`feat:`, `fix:`, `refactor:`).

---

## 🤖 AI Context
When generating code:
- Prefer **Pydantic V2** for data validation.
- Use **Rust-like** error handling in Python where possible (explicit returns/raises).
- assume **CUDA 12** context for GPU operations.
