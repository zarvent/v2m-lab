# Voice2Machine Backend (Python 3.12+)

AI agent instructions for the core daemon and backend services in `apps/backend/`.

This is the "Brain" of Voice2Machine. It follows a **Hexagonal Architecture** (Ports & Adapters) with a strict "local-first" privacy model. The core is asynchronous and optimized for low-latency GPU/CPU inference.

## Development Setup

### Installation

```bash
# From apps/backend/
pip install -r requirements.txt
pip install -e .
```

### Fast Commands (File-Scoped)

Prioritize these over full-project runs.

- **Lint (Single File)**: `ruff check src/v2m/path/to/file.py --fix`
- **Format (Single File)**: `ruff format src/v2m/path/to/file.py`
- **Test (Single File)**: `pytest tests/unit/path/to/test_file.py`
- **Type Check**: Use `ruff` (integrated) or your LSP. Ensure 100% type hint coverage.

### Run Daemon

- `python -m v2m.main --daemon`

## Tech Stack

- **Language**: Python 3.12+ (Asyncio-native)
- **Data Validation**: [Pydantic V2](https://docs.pydantic.dev/latest/)
- **Linting/Formatting**: [Ruff](https://docs.astral.sh/ruff/) (SOTA 2026 standard)
- **Testing**: Pytest with `pytest-asyncio`
- **Inference**: Faster-Whisper, Google GenAI (Gemini)
- **Architecture**: Hexagonal (Domain, Application, Infrastructure)

## Project Structure

- `src/v2m/domain/`: **Core Entities & Protocols**. Must have ZERO external dependencies (except Pydantic).
- `src/v2m/application/`: **Use Cases**. Handlers for commands and queries. Orchestrates domain logic.
- `src/v2m/infrastructure/`: **Adapters**. Concrete implementations for Whisper, SoundDevice, LLM clients, and File System.
- `src/v2m/core/`: **System Plumbing**. Dependency Injection container, Event Bus, and Logging.
- `src/v2m/main.py`: Entry point for the CLI and Daemon.

## Code Standards

### 1. Hexagonal Boundaries

- **Inward pointing**: Domain knows nothing about Infrastructure.
- **Protocols over Classes**: Use `typing.Protocol` in `domain/` for interfaces. Implement them in `infrastructure/`.

### 2. Async Non-Blocking

- **Never** use `time.sleep()`. Use `await asyncio.sleep()`.
- **CPU/GPU Intensive Tasks**: Offload to `asyncio.to_thread` or a dedicated executor to keep the event loop responsive.

### 3. Concrete Example: Pydantic & Domain

```python
# src/v2m/domain/entities.py
from pydantic import BaseModel, ConfigDict

class Transcription(BaseModel):
    model_config = ConfigDict(frozen=True) # Immutability by default
    text: str
    confidence: float
    language: str
```

## Testing Guidelines

- **Unit Tests**: Test `application/` and `domain/` logic. Mock ALL infrastructure (Adapters).
- **Behavioral**: Tests should verify "What the system does", not "How it does it".
- **Coverage**: Target >80% for domain logic.

## Git & PR Standards

- **Commit Format**: `[scope]: behavior description` (e.g., `infra/whisper: fix VAD sensitivity`).
- **PR Check**: All ruff checks must pass. No blocking calls in async handlers.

## Boundaries

### Always do

- Read `src/v2m/domain/` protocols before implementing a new adapter.
- Use `logger.info` or `logger.debug` for trace-level info.
- Verify `ruff` passes for every modified file.

### Ask first

- Adding new heavy dependencies to `pyproject.toml`.
- Modifying the Core Event Bus or DI container.
- Changing `config.toml` structure.

### Never do

- **Hardcode Paths**: Use `v2m.utils.paths` or secure runtime directory helpers.
- **Commit Secrets**: Never include API keys or tokens in code or configs.
- **Block the Loop**: Avoid synchronous I/O in the main application flow.

## Common Pitfalls

- **Pydantic V1 vs V2**: Use V2 features exclusively.
- **Circular Imports**: Watch out for cross-layer imports. Always import from `domain/` into `application/`, never vice-versa.
- **CUDA Context**: Assume CUDA 12. Use `torch.cuda.is_available()` where applicable but prefer high-level abstractions from Faster-Whisper.
