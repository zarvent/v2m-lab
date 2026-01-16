# State and Data Management

The Voice2Machine frontend uses **Zustand** to manage global state. The architecture is divided into three main stores to separate concerns and optimize performance.

---

## 🏗️ Global Stores

### 1. BackendStore (`src/stores/backendStore.ts`)

The "source of truth" for system state. Manages business logic and communication with the daemon.

**Key States:**

- `status`: Current state machine status (`idle` | `recording` | `transcribing` | `paused`).
- `transcription`: Accumulated text for the current session.
- `isConnected`: Boolean indicating if the IPC bridge is active.
- `history`: Persistent list of past transcriptions.

**Main Actions:**

- `startRecording(mode)`: Starts audio capture.
- `stopRecording()`: Stops capture and requests final transcription.
- `processText()`: Sends current text to LLM for refinement.

### 2. TelemetryStore (`src/stores/telemetryStore.ts`)

Specialized high-frequency store.

**Problem:** CPU/GPU data arrives every 100ms. If stored in the main store, it would cause massive re-renders across the UI.
**Solution:** This store lives in isolation. Only components that visualize graphs (e.g., Sidebar) subscribe to it.

**`isTelemetryEqual` Optimization:**
Before updating state, new values are compared with previous ones using a tolerance (epsilon). If the change is insignificant (e.g., CPU goes from 10.1% to 10.2%), the update is **not** triggered, saving rendering cycles.

### 3. UiStore (`src/stores/uiStore.ts`)

Manages purely visual and ephemeral state.

- `activeView`: The screen the user sees (`studio`, `settings`, etc.).
- `modals`: Visibility dictionary for modal windows.

---

## 🔌 IPC Types (`src/types/ipc.ts`)

The data contract between Rust and TypeScript is strict.

### DaemonState

The payload sent by the backend whenever something important happens.

```typescript
export interface DaemonState {
  // Current engine state
  state:
    | "idle"
    | "recording"
    | "transcribing"
    | "processing"
    | "paused"
    | "restarting"
    | "disconnected";

  // Real-time (partial) or final text
  transcription?: string;

  // LLM processing result
  refined_text?: string;

  // Error or informational messages
  message?: string;

  // Resource snapshot (optional, usually in a separate event)
  telemetry?: TelemetryData;
}
```

### TelemetryData

```typescript
export interface TelemetryData {
  cpu: {
    percent: number; // 0-100
  };
  ram: {
    used_gb: number;
    total_gb: number;
    percent: number;
  };
  gpu?: {
    // Optional (only if NVIDIA/AMD detected)
    name: string;
    vram_used_mb: number;
    vram_total_mb: number;
    temp_c: number;
  };
}
```
