# ADR-004: Hexagonal Architecture (Ports and Adapters)

## Status

Accepted

## Date

2024-03-01

## Context

Voice2Machine started as a monolithic script of ~200 lines. As functionality grew, we faced typical problems of coupled code:

1. **Difficult testing**: Mocks of GPU, audio, external APIs
2. **Cascade changes**: Modifying Whisper required touching 5+ files
3. **Vendor lock-in**: Switching from Ollama to Gemini required massive refactor
4. **Diffuse responsibilities**: Unclear where to put new logic

### Requirements:

- Framework-agnostic business core
- Interchangeable adapters (e.g., swap Whisper for another ASR)
- Testability without real hardware
- Clear boundaries between layers

## Decision

**Adopt Hexagonal Architecture (Ports & Adapters)** as the structural pattern.

### Folder structure:

```
src/v2m/
├── core/           # Configuration, logging, base interfaces
├── domain/         # Models, ports (interfaces), errors
├── services/       # Orchestrator, coordination
└── infrastructure/ # Adapters (Whisper, Audio, LLM)
```

### Port implementation:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class TranscriptionService(Protocol):
    async def transcribe(self, audio: bytes) -> str: ...
```

Adapters implement ports:

```python
class WhisperAdapter:
    async def transcribe(self, audio: bytes) -> str:
        # Concrete implementation with faster-whisper
```

## Consequences

### Positive

- ✅ **Isolated testing**: Unit tests without GPU or network
- ✅ **Flexibility**: Switching Gemini for Ollama is editing 1 file
- ✅ **Onboarding**: Predictable and documented structure
- ✅ **Type safety**: `Protocol` + mypy detects incompatibilities at compile time

### Negative

- ⚠️ **More files**: ~20 files vs ~5 from original script
- ⚠️ **Indirection**: Must navigate between layers to understand complete flow
- ⚠️ **Initial overhead**: More complex setup for simple features

## Alternatives Considered

### Clean Architecture (Uncle Bob)

- **Rejected**: Too many layers (Entities, Use Cases, Interface Adapters, Frameworks) for the scope.

### MVC/MVP

- **Rejected**: UI-oriented, doesn't apply well to a backend daemon.

### Simple Modules

- **Rejected**: In practice, we returned to original coupling.

## References

- [Alistair Cockburn - Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Netflix - Ready for changes with Hexagonal Architecture](https://netflixtechblog.com/ready-for-changes-with-hexagonal-architecture-b315ec967749)
