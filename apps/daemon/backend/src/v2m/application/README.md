# application

The application layer orchestrates business logic by coordinating domain entities and infrastructure interfaces. This is where system use cases reside.

## Content

- `commands.py` - Definitions of available commands (e.g., `StartRecordingCommand`)
- `command_handlers.py` - Logic implementations for each command
- `llm_service.py` - Abstract interface for language model services
- `transcription_service.py` - Abstract interface for transcription services

## Responsibility

This layer translates user intentions (commands) into concrete actions by coordinating necessary services, but without knowing implementation details (e.g., it knows it must "transcribe" but doesn't know it uses Whisper).
