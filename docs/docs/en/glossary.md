# Glossary

This glossary defines technical and domain terms used in Voice2Machine.

## General Terms

### Local-First

Design philosophy where data (audio, text) is processed and stored exclusively on the user's device, without relying on the cloud.

### Daemon

Background process (written in Python) that manages recording, transcription, and communication with the frontend.

### REST API

Communication mechanism between the Daemon (Python) and clients (scripts, frontends). We use FastAPI with standard HTTP endpoints and WebSocket for real-time events.

## Technical Components

### Whisper

Speech recognition model (ASR) developed by OpenAI. Voice2Machine uses `faster-whisper`, an optimized implementation with CTranslate2.

### Orchestrator

Central coordination component that manages the complete workflow lifecycle: recording → transcription → post-processing. Replaces the previous CQRS/CommandBus pattern with a simpler direct approach.

### BackendProvider

Frontend component (React Context) that manages connection with the Daemon and distributes state to the UI.

### TelemetryContext

Sub-context in React optimized for high-frequency updates (GPU metrics, audio levels) to avoid unnecessary re-renders of the main UI.

### Hexagonal Architecture

Also known as "Ports and Adapters". Design pattern where the core business logic (the hexagon) is isolated from external concerns (databases, APIs, UI) through well-defined interfaces (ports) and implementations (adapters).
