# Architecture Decision Records (ADRs)

An Architecture Decision Record (ADR) is a document that captures an important architectural decision, along with its context and consequences.

## Index of Decisions

| ADR                                      | Title                                            | Status   | Date    |
| ---------------------------------------- | ------------------------------------------------ | -------- | ------- |
| [ADR-001](001-fastapi-migration.md)      | Migration from Unix Sockets IPC to FastAPI REST  | Accepted | 2025-01 |
| [ADR-002](002-orchestrator-pattern.md)   | Replacement of CQRS/CommandBus with Orchestrator | Accepted | 2025-01 |
| [ADR-003](003-faster-whisper.md)         | Selection of faster-whisper over whisper.cpp     | Accepted | 2024-06 |
| [ADR-004](004-hexagonal-architecture.md) | Hexagonal Architecture (Ports and Adapters)      | Accepted | 2024-03 |
| [ADR-005](005-rust-audio-engine.md)      | Rust Audio Engine (v2m_engine)                   | Accepted | 2025-01 |
| [ADR-006](006-local-first.md)            | Local-first: Processing Without Cloud            | Accepted | 2024-03 |

## When to Write an ADR?

Write an ADR when you make a significant decision that affects the project's structure, dependencies, interfaces, or technology.

See [ADR Template](template.md) for the format.
