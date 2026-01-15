# Glossary

This glossary defines technical and domain terms used in Voice2Machine.

## General Terms

### Local-First
Design philosophy where data (audio, text) is processed and stored exclusively on the user's device, without relying on the cloud.

### Daemon
Background process (written in Python) that manages recording, transcription, and communication with the frontend.

### IPC (Inter-Process Communication)
Mechanism used for communication between the Daemon (Python) and the Frontend (Tauri/Rust). We use Unix sockets with a framed message protocol (size header + JSON payload).

## Technical Components

### Whisper
Automatic Speech Recognition (ASR) model developed by OpenAI. Voice2Machine uses `faster-whisper`, an implementation optimized with CTranslate2.

### BackendProvider
Frontend component (React Context) that manages the connection to the Daemon and distributes state to the UI.

### TelemetryContext
React sub-context optimized for high-frequency updates (GPU metrics, audio levels) to avoid unnecessary re-renders of the main UI.

### CommandBus
Design pattern (CQRS) used in the backend to decouple user intent (Command) from its execution (Handler).
