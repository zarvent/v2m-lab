# Voice2Machine (V2M) - Instructions for Agents

> **Context**: You are working on a Hexagonal Architecture project (Python Backend + Tauri Frontend).
> **Objective**: Maintain "State of the Art 2026" code quality standards. High cohesion, low coupling, zero technical debt.

---

## 📚 Documentation Governance (SOTA 2026)

### Docs as Code
*   **Source of Truth**: Technical documentation lives in `docs/docs/es/`. `mkdocs.yml` defines the site structure.
*   **Sync**: Any PR that changes functionality (code) **MUST** include the corresponding update in the documentation.
*   **README**: `README.md` (English) and `LEEME.md` (Spanish) must stay synchronized and point to the detailed documentation.

### Quality Standards
1.  **Accessibility (WCAG 2.1 AA)**:
    *   Use descriptive `alt text` for all images.
    *   Maintain strict heading hierarchy (H1 > H2 > H3).
    *   Use code blocks with language specification.
2.  **Structure**:
    *   **Exploration**: What it is and why use it.
    *   **Procedures**: Step-by-step guides (How-to).
    *   **Reference**: APIs, Configuration, Commands.
    *   **Concepts**: Architecture, design decisions (ADRs).
3.  **Language**:
    *   Detailed documentation (`docs/`): **Native Latin American Spanish**.
    *   Code comments: **Native Latin American Spanish**.
    *   Commits: English (Conventional Commits).

---

## 🧠 Core Philosophy

1.  **Local-First**: Privacy is supreme. Audio never leaves the machine.
2.  **Modular**: The Daemon is the core. GUI and Scripts are just clients.
3.  **Hexagonal**: Dependencies point inwards. `Domain` knows nothing about `Infrastructure`.

---

## 🛠️ Tools and Commands

### Documentation
*   **Serve locally**: `mkdocs serve`

### Backend (Python 3.12+)
*   **Core**: `asyncio`, `uvloop`, `pydantic` (v2).
*   **ML/AI**: `faster-whisper` (Local ASR), `google-genai` (Gemini).
*   **Run**: `python -m v2m.main --daemon`
*   **Test**: `pytest tests/` (Unit: `tests/unit`, Integration: `tests/integration`)
*   **Lint**: `ruff check src/ --fix` (Strict rules enabled)
*   **Format**: `ruff format src/`

### Frontend (Tauri 2 + React 19)
*   **Stack**: Vite 7.x, TypeScript 5.8.x, Tailwind CSS 4.1.x, Zustand, Zod.
*   **Dev**: `npm run dev` (Web), `npm run tauri dev` (Desktop).
*   **Build**: `npm run tauri build`.
*   **Check**: `tsc --noEmit`, `npx eslint .`.
*   **Test**: `npm test` (Vitest).

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
└── infrastructure/ # Concrete Implementations (Whisper, Gemini, SoundDevice)
```

### Backend Rules
1.  **Interfaces in Domain/Application**: Use `typing.Protocol` with `@runtime_checkable`.
2.  **No "God Classes"**: Divide responsibilities (e.g., `AudioRecorder` vs `TranscriptionService`).
3.  **Type Hints**: 100% coverage required.
4.  **AsyncIO**: Core is async. Offload blocking CPU/GPU tasks to executors.

### Frontend Rules
1.  **Store-First**: Components call Zustand stores, not `invoke` directly.
2.  **Local State**: Use `v2m://state-update` events with polling fallback.
3.  **Styling**: Tailwind CSS 4.0 standards.

---

## 🧪 Testing Strategy

1.  **Unit Tests**: Mock all infrastructure. Test logic in `application/`.
2.  **Integration Tests**: Test real infrastructure (GPU, Audio) in isolated scripts or `tests/integration/`.
3.  **Frontend Tests**: Vitest + Testing Library. Focus on user flows.
4.  **Golden Rule**: If you fix a bug, add a test that reproduces it.

---

## 🚨 Common Errors

- **Hardcoded Paths**: NEVER use absolute paths. Use `v2m.utils.paths`.
- **Blocking the Loop**: Do not use `time.sleep()`. Use `await asyncio.sleep()`.
- **Secrets**: No API keys in code. Use `GeminiConfig` masked in UI.
- **Git Commits**: Use Conventional Commits (`feat:`, `fix:`, `refactor:`).

---

## 🤖 AI Context
When generating code:
- **Python**: Pydantic V2, robust `ApplicationError` hierarchy.
- **Frontend**: Functional components, Hooks, Zod validation.
- **Hardware**: Assume **CUDA 12** context for GPU operations.
- **Language**: All documentation and comments must be in Native Latin American Spanish.