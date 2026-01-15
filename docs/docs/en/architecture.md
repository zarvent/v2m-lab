# 🧩 System Architecture

!!! abstract "Technical Philosophy"
    **Voice2Machine** implements a strict **Hexagonal Architecture (Ports & Adapters)**, prioritizing decoupling, testability, and technological independence. The system adheres to SOTA 2026 standards like static typing in Python (Protocol) and Frontend/Backend separation via binary IPC.

---

## 🏗️ High-Level Diagram

```mermaid
graph TD
    subgraph Frontend ["🖥️ Frontend (Tauri)"]
        React["React 19 GUI"]
        Rust["Rust Core"]
    end

    subgraph Backend ["🐍 Backend (Python)"]
        Daemon["Daemon Loop"]

        subgraph Hexagon ["Hexagon (Core)"]
            App["Application<br>(Use Cases)"]
            Domain["Domain<br>(Interfaces/Models)"]
        end

        subgraph Infra ["Infrastructure (Adapters)"]
            Whisper["Whisper Adapter"]
            Audio["Audio Engine<br>(Rust Ext)"]
            LLM["LLM Providers<br>(Ollama/Gemini)"]
        end
    end

    React <-->|Events| Rust
    Rust <-->|Unix Socket (IPC)| Daemon
    Daemon --> App
    App --> Domain
    Whisper -.->|Implements| Domain
    Audio -.->|Implements| Domain
    LLM -.->|Implements| Domain

    style Frontend fill:#e3f2fd,stroke:#1565c0
    style Backend fill:#e8f5e9,stroke:#2e7d32
    style Hexagon fill:#fff3e0,stroke:#ef6c00
    style Infra fill:#f3e5f5,stroke:#7b1fa2
```

---

## 📦 Backend Components

### 1. Core (The Hexagon)
Located in `apps/backend/src/v2m/core/` and `domain/`.
*   **Ports (Interfaces)**: Defined using `typing.Protocol` + `@runtime_checkable` for structural checking at runtime.
*   **CQRS**: Every action is a `Command` (Pydantic DTO) processed by a `CommandHandler` via a `CommandBus`.

### 2. Application
Located in `apps/backend/src/v2m/application/`.
*   Orchestrates pure business logic.
*   Example: `TranscribeAudioHandler` receives audio, invokes the `TranscriptionService` port, and notifies events.

### 3. Infrastructure
Located in `apps/backend/src/v2m/infrastructure/`.
*   **WhisperAdapter**: Concrete implementation using `faster-whisper`. Manages lazy loading to save VRAM.
*   **SystemMonitor**: Critical service that monitors GPU/CPU usage in real-time for telemetry.
*   **ProviderRegistry**: Factory pattern to dynamically instantiate LLM providers (Gemini/Ollama) based on configuration.

---

## ⚡ Frontend-Backend Communication (IPC)

Voice2Machine avoids HTTP/REST to maximize local performance. It uses **Unix Domain Sockets** with a custom protocol:

1.  **Header**: 4 bytes (Big Endian) indicating length.
2.  **Payload**: JSON utf-8.
3.  **Persistence**: The connection is kept alive (Keep-Alive), eliminating *handshake overhead*.

---

## 🦀 Native Extensions (Rust)

For critical tasks where Python's GIL is a bottleneck, we use native extensions compiled in Rust (`v2m_engine`):
*   **Audio I/O**: Direct WAV writing to disk (Zero-copy).
*   **VAD**: Ultra-low latency voice detection.

---

## 🛡️ Design Principles 2026

1.  **Local-First & Privacy-By-Design**: No data leaves the machine unless a cloud provider is explicitly configured.
2.  **Resilience**: The Daemon implements automatic error recovery and subsystem restart (e.g., if the audio driver crashes).
3.  **Observability**: Structured logging (OpenTelemetry standard) and real-time metrics exposed to the frontend.
