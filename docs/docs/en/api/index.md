---
title: Python API Reference
description: Technical documentation index for the Voice2Machine backend.
status: stable
last_update: 2026-01-23
language: US English
---

# Python API - Index

This section provides auto-generated documentation of Python classes and functions from the Voice2Machine backend.

!!! info "Generated with mkdocstrings"
This documentation is automatically extracted from source code docstrings. For the most up-to-date version, always check the code at `apps/daemon/backend/src/v2m/`.

---

## Main Modules

### [Interfaces](interfaces.md)

Protocols and contracts that define the expected behavior of adapters.

### [Domain](domain.md)

Domain models, ports, and error types.

### [Services](services.md)

Application services including the main Orchestrator.

---

## Quick Navigation

| Class/Function         | Description                     |
| ---------------------- | ------------------------------- |
| `Orchestrator`         | Central workflow coordinator    |
| `TranscriptionService` | Port for transcription services |
| `AudioRecorder`        | Interface for audio capture     |
| `LLMProvider`          | Base interface for AI providers |
