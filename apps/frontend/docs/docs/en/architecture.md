# Frontend Architecture

The Voice2Machine frontend architecture follows a **decoupled vision** and **Extreme Reactivity** pattern. Heavy audio processing and transcription logic reside in the Python Daemon, while the frontend acts as a lightweight visual orchestrator and state manager.

!!! abstract "State of the Art 2026 Philosophy"
The design prioritizes **zero latency** in the interface. The UI must never block waiting for the backend. All heavy operations are asynchronous and notify their progress via events, allowing the interface to maintain constant 60/120 FPS even during intense inference loads.

---

## 🏗️ Directory Structure

The source code is organized following a fractal structure by technical and functional domain:

```
apps/frontend/src/
├── components/      # React Components
│   ├── settings/    # Configuration panel modules
│   ├── studio/      # Editor and recorder components
│   └── ...          # Shared components (Sidebar, Toast, etc.)
├── hooks/           # Reusable Custom Hooks (UI Logic)
├── stores/          # Global state (Zustand) - The frontend "Database"
├── schemas/         # Validation definitions (Zod)
├── types/           # TypeScript definitions and IPC Interfaces
├── utils/           # Pure utilities (formatting, classes, time)
├── App.tsx          # Root component and Main Layout
└── main.tsx         # Entry point and React mounting
```

---

## Bridge IPC and Communication (Tauri Bridge)

The frontend communicates with the operating system and the Python daemon through the secure Tauri bridge. There is no insecure direct HTTP/WebSocket communication; everything passes through the Rust message bus.

### Data Flow

1.  **React (View)**: The user interacts (e.g., clicks "Record").
2.  **Action (Zustand)**: The `backendStore` invokes a Tauri command (`invoke("start_recording")`).
3.  **Rust (Core)**:
    - Validates the command.
    - Sends the instruction to the Python Daemon via Unix Socket.
    - Returns an immediate promise to the frontend ("Command received").
4.  **Daemon (Python)**:
    - Executes the logic.
    - Emits state events (`recording`, `transcribing`) as it progresses.
5.  **Event Listeners**: The frontend listens for `v2m://state-update` events and updates the store reactively.

### State Payload (DaemonState)

The communication contract is strictly defined in `src/types/ipc.ts`:

```typescript
export interface DaemonState {
  state: "idle" | "recording" | "transcribing" | "processing" | "paused";
  transcription?: string; // Partial or final text
  refined_text?: string; // LLM post-processed text
  message?: string; // Error or info messages
  telemetry?: TelemetryData; // CPU/GPU/RAM data
}
```

---

## 🧠 State Management (Zustand)

We have adopted a **Stores First** approach. React components **must never** call `invoke()` directly or manage complex business logic.

### 1. BackendStore (`backendStore.ts`)

Acts as the **digital twin** of the daemon.

- **Responsibility**: Keep UI state synchronized with backend reality.
- **Data**: Transcription history, connection status, system errors.

### 2. TelemetryStore (`telemetryStore.ts`)

Optimized high-frequency channel.

- **Responsibility**: Visualize resource consumption without triggering re-renders in the rest of the app.
- **Optimization**: Uses deep comparison (`isTelemetryEqual`) with thresholds (e.g., change > 1%) to avoid unnecessary state updates (noise).

### 3. UiStore (`uiStore.ts`)

Ephemeral interface state.

- **Responsibility**: Control which view is active (Studio, Settings), which modals are open, and notification management (Toasts).

---

## 📝 Validation and Security (Zod)

Application configuration is critical. An incorrect value could crash the inference engine.
Therefore, we use **Zod** to strictly validate any configuration before saving it or sending it to the backend.

- **Schemas**: Defined in `src/schemas/config.ts`.
- **Synchronization**: Zod schemas must exactly match the backend's Pydantic models (`v2m/config.py`).
