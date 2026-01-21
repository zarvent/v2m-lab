# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
