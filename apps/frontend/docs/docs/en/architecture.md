# Frontend Architecture

The architecture of the Voice2Machine frontend follows a **decoupled view** pattern. The heavy lifting of audio processing and transcription resides in the Python Daemon, while the frontend acts as a visual orchestrator and state manager.

## 🌉 IPC Bridge and Communication

The communication flow is hierarchical and secure to ensure a Non-blocking UI:

1.  **React (View Layer)**: Invokes a Tauri command (e.g., `start_recording`).
2.  **Rust (Security Layer)**: Intercepts the call, validates parameters, and communicates with the Daemon via a **Unix Socket**.
3.  **Daemon (Core Layer)**: Processes the request (Whisper/LLM Inference) and returns the response to the socket.
4.  **Rust**: Receives the response and resolves it to the original promise in React.

### Automatic State Management

The application uses a `BackendInitializer` component that synchronizes the backend state with the frontend using two mechanisms:

- **Events (Push)**: Listens for `v2m://state-update` events emitted by Rust when the daemon changes state (e.g., "Recording").
- **Polling (Fallback)**: If no recent events are received, it performs a periodic `get_status` to ensure connection.

## 🧠 State Management (Zustand)

We have adopted a **Stores First** approach. React components should not call `invoke()` directly. Instead, they interact with Zustand stores located in `src/stores/`.

- **`backendStore.ts`**: Source of truth for daemon state (current transcription, recording mode, errors, connection).
- **`uiStore.ts`**: Manages volatile visual state (active navigation, open modals).
- **`telemetryStore.ts`**: Stores performance data (CPU, RAM, VRAM) received via telemetry.

## 📝 Zod Validation

Application configuration (mapped from the backend's `config.toml`) is rigorously validated in the frontend using **Zod**. This ensures that invalid configurations are never sent to the transcription engine, preventing catastrophic failures.

The main schema resides in [src/schemas/config.ts](../../src/schemas/config.ts).
