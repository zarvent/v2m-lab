# Architecture Decision Records (ADRs)

Un Registro de Decisiones de Arquitectura (ADR) es un documento que captura una decisión de arquitectura importante, junto con su contexto y consecuencias.

## Índice de Decisiones

| ADR                                      | Título                                         | Estado   | Fecha   |
| ---------------------------------------- | ---------------------------------------------- | -------- | ------- |
| [ADR-001](001-fastapi-migration.md)      | Migración de IPC Unix Sockets a FastAPI REST   | Aceptada | 2025-01 |
| [ADR-002](002-orchestrator-pattern.md)   | Reemplazo de CQRS/CommandBus por Orchestrator  | Aceptada | 2025-01 |
| [ADR-003](003-faster-whisper.md)         | Selección de faster-whisper sobre whisper.cpp  | Aceptada | 2024-06 |
| [ADR-004](004-hexagonal-architecture.md) | Arquitectura Hexagonal (Puertos y Adaptadores) | Aceptada | 2024-03 |
| [ADR-005](005-rust-audio-engine.md)      | Motor de Audio en Rust (v2m_engine)            | Aceptada | 2025-01 |
| [ADR-006](006-local-first.md)            | Local-first: Procesamiento sin Cloud           | Aceptada | 2024-03 |

## ¿Cuándo escribir un ADR?

Escribe un ADR cuando tomes una decisión significativa que afecte a la estructura, dependencias, interfaces o tecnología del proyecto.

Ver [Plantilla de ADR](template.md) para el formato.
