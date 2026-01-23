# Voice2Machine (V2M) - Instructions for Agents

> **Context**: You are working on a Hexagonal Architecture project (Python Backend Daemon).
> **Objective**: Maintain "State of the Art 2026" code quality standards. High cohesion, low coupling, zero technical debt.

---

## 📚 Documentation Governance (SOTA 2026)

### Docs as Code

- **Source of Truth**: Technical documentation lives in [docs/docs/es/](docs/docs/es/). [mkdocs.yml](mkdocs.yml) defines the site structure.
- **Detailed Instructions**: Specialized documentation rules for agents are in [docs/AGENTS.md](docs/AGENTS.md).
- **Sync**: Any PR that changes functionality (code) **MUST** include the corresponding update in the documentation.
- **README**: `README.md` (English) and `LEEME.md` (Spanish) must stay synchronized and point to the detailed documentation.

### Quality Standards (Diátaxis)

1.  **Accessibility (WCAG 2.2+)**:
    - Use descriptive `alt text` for all images.
    - Maintain strict heading hierarchy (H1 > H2 > H3).
    - Minimum target size of 24x24px for interactive instructions.
2.  **Structure**:
    - **Tutorials**: Learning-oriented.
    - **How-to Guides**: Task-oriented.
    - **Reference**: Information-oriented (API/CLI).
    - **Explanation**: Understanding-oriented (Concepts/ADRs).
3.  **Language**:
    - Detailed documentation (`docs/`): **Native Latin American Spanish**.
    - Code comments: **Native Latin American Spanish**.
    - Commits: English (Conventional Commits).

---

## 🧠 Core Philosophy

1.  **Local-First**: Privacy is supreme. Audio never leaves the machine.
2.  **Modular**: The Daemon is the core. Any client (CLI, Scripts) connects via IPC.
3.  **Hexagonal**: Dependencies point inwards. `Domain` knows nothing about `Infrastructure`.

---

## 🛠️ Tools and Commands

### Documentation

- **Serve locally**: `mkdocs serve`

### Backend (Python 3.12+)

- **Core**: `asyncio`, `uvloop`, `pydantic` (v2).
- **ML/AI**: `faster-whisper` (Local ASR), `google-genai` (Gemini).
- **Run**: `python -m v2m.main --daemon`
- **Test**: `pytest tests/` (Unit: `tests/unit`, Integration: `tests/integration`)
- **Lint**: `ruff check src/ --fix` (Strict rules enabled)
- **Format**: `ruff format src/`

### Scripts

- **Install**: `./apps/daemon/backend/scripts/setup/install.sh` (Idempotent)
- **Verify**: `python apps/daemon/backend/scripts/diagnostics/health_check.py`

---

## 🏗️ Architecture Guides

### Directory Structure

```
apps/daemon/backend/src/v2m/
├── api/            # FastAPI (app, routes, schemas)
├── shared/         # Foundation (config, errors, interfaces)
├── orchestration/  # Business Workflows (Recording, LLM)
└── features/       # Domain logic and specialized adapters (audio, llm, transcription)
```

### Backend Rules

1.  **Interfaces in Domain/Application**: Use `typing.Protocol` with `@runtime_checkable`.
2.  **No "God Classes"**: Divide responsibilities (e.g., `AudioRecorder` vs `TranscriptionService`).
3.  **Type Hints**: 100% coverage required.
4.  **AsyncIO**: Core is async. Offload blocking CPU/GPU tasks to executors.

---

## 🧪 Testing Strategy

1.  **Unit Tests**: Mock all infrastructure. Test logic in `application/`.
2.  **Integration Tests**: Test real infrastructure (GPU, Audio) in isolated scripts or `tests/integration/`.
3.  **Golden Rule**: If you fix a bug, add a test that reproduces it.

---

## 🚨 Common Errors

- **Hardcoded Paths**: NEVER use absolute paths. Use `v2m.utils.paths`.
- **Blocking the Loop**: Do not use `time.sleep()`. Use `await asyncio.sleep()`.
- **Secrets**: No API keys in code. Use environment variables.
- **Git Commits**: Use Conventional Commits (`feat:`, `fix:`, `refactor:`).

---

## 🤖 AI Context

When generating code:

- **Python**: Pydantic V2, robust `ApplicationError` hierarchy.
- **IPC**: Focus on Unix Socket protocol stability.
- **Hardware**: Assume **CUDA 12** context for GPU operations.
- **Language**: All documentation and comments must be in Native Latin American Spanish.
