---
title: Changelog
description: Change log for the Voice2Machine project.
ai_context: "Versions, Change History, SemVer"
depends_on: []
status: stable
---

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-01-23

### Added

- **Feature-Based Architecture**: Total restructuring into self-contained modules in `features/` (audio, llm, transcription).
- **Orchestration via Workflows**: Introduction of `RecordingWorkflow` and `LLMWorkflow` to decouple business logic from the monolithic legacy Orchestrator.
- **Strict Protocols**: Implementation of `typing.Protocol` for all internal services, allowing easy swapping of providers.
- **Modular API**: Package structure in `api/` with separate routes and schemas.

### Changed

- **Elimination of Orchestrator**: `services/orchestrator.py` has been decomposed and removed.
- **Infrastructure Refactoring**: The `infrastructure/` folder has been integrated into each corresponding `feature`.
- **Core and Domain**: Simplified and moved to `shared/` and local interfaces.

### Removed

- **Legacy Audio Tests**: Removal of obsolete tests for the Rust extension.
- **System Monitor**: System telemetry removed for core simplification.

## [0.2.0] - 2025-01-20

### Added

- **FastAPI REST API**: New HTTP API replacing the Unix Sockets-based IPC system
- **WebSocket streaming**: `/ws/events` endpoint for real-time provisional transcription
- **Swagger documentation**: Interactive UI at `/docs` for testing endpoints
- **Orchestrator pattern**: New coordination pattern that simplifies workflow
- **Rust audio engine**: Native `v2m_engine` extension for low-latency audio capture
- **MkDocs documentation system**: Structured documentation with Material theme

### Changed

- **Simplified architecture**: From CQRS/CommandBus to more direct Orchestrator pattern
- **Communication**: From binary Unix Domain Sockets to standard HTTP REST
- **State model**: Centralized management in `DaemonState` with lazy initialization
- Updated README.md with new architecture

### Removed

- `daemon.py`: Replaced by `api.py` (FastAPI)
- `client.py`: No longer needed, use `curl` or any HTTP client
- Binary IPC protocol: Replaced by standard JSON

### Fixed

- Startup latency: Server starts in ~100ms, model loads in background
- Memory leaks in WebSocket connections

## [Unreleased]

### Planned

- Support for multiple simultaneous transcription languages
- Web dashboard for real-time monitoring
- Integration with more LLM providers

## [0.1.0] - 2024-03-20

### Added

- Initial Voice2Machine system version
- Local transcription support with Whisper (faster-whisper)
- Basic LLM integration (Ollama/Gemini)
- Unix Domain Sockets-based IPC system
- Hexagonal architecture with ports and adapters
- TOML-based configuration
