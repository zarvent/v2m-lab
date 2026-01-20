# Hexagonal Architecture

Voice2Machine Backend implements a pure **Hexagonal Architecture** to separate technical decisions from business rules.

## 🧱 System Layers

### 1. Domain (`domain/`)

It is the heart of the system. It defines the data models (Entities) and the rules that do not change, regardless of whether the audio comes from a physical microphone or a file.

- **Entities**: Immutable Pydantic classes (`Transcription`, `AudioChunk`).
- **Ports (Protocols)**: Structural definitions using `typing.Protocol` that the system needs to function (e.g., `TranscriptionService`).

### 2. Application (`application/`)

Coordinates the flow of data between the domain and infrastructure. It contains the "Use Cases".

- **Handlers**: Orchestrate the logic. For example, receiving audio, sending it to the transcription service, and then saving it to the history.

### 3. Infrastructure (`infrastructure/`)

Contains "Adapters" or detailed technical implementations.

- **WhisperAdapter**: Implements the transcription protocol using Faster-Whisper.
- **GeminiAdapter**: Implements the refinement protocol using the Google API.
- **FileSystemAdapter**: Local data persistence.

## 🧠 Dependency Injection

The system uses a centralized dependency container in `core/container.py`. This allows swapping implementations (e.g., using an audio simulator for tests) without touching the application logic.

## 📡 Event Bus

Internal communication between services is performed using asynchronous events. This decouples data producers (Audio capture) from consumers (User interface/Logs).
