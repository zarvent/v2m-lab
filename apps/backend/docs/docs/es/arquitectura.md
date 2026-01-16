# Arquitectura del Sistema

Voice2Machine implementa una **Arquitectura Hexagonal (Ports & Adapters)** estricta. Esta decisión de diseño es fundamental para cumplir con nuestros requisitos de **privacidad local-first**, **baja latencia** y **testabilidad**.

## 🏗️ Diagrama de Componentes

```mermaid
graph TD
    subgraph Frontend ["🖥️ Frontend (Tauri)"]
        React["React 19 GUI"]
        Rust["Rust Core"]
    end

    subgraph Backend ["🐍 Backend (Python)"]
        Daemon["Daemon Loop (Main)"]

        subgraph Hexagon ["Hexagon (Core Logic)"]
            App["Application Layer<br>(Use Cases / Handlers)"]
            Domain["Domain Layer<br>(Entities / Protocols)"]
        end

        subgraph Infra ["Infrastructure Layer (Adapters)"]
            Whisper["Whisper Adapter<br>(Faster-Whisper)"]
            Audio["Audio Engine<br>(Rust Ext: v2m_engine)"]
            LLM["LLM Providers<br>(Ollama/Gemini/Local)"]
            System["System Monitor<br>(NVML/Psutil)"]
        end
    end

    React <-->|Events| Rust
    Rust <-->|Unix Socket (IPC)| Daemon
    Daemon --> App
    App --> Domain
    Whisper -.->|Implements| Domain
    Audio -.->|Implements| Domain
    LLM -.->|Implements| Domain
    System -.->|Implements| Domain

    style Frontend fill:#e3f2fd,stroke:#1565c0
    style Backend fill:#e8f5e9,stroke:#2e7d32
    style Hexagon fill:#fff3e0,stroke:#ef6c00
    style Infra fill:#f3e5f5,stroke:#7b1fa2
```

---

## 🧱 Capas del Sistema

### 1. Dominio (`v2m/domain/`)
**Responsabilidad**: Definir las "reglas del juego". No conoce detalles de implementación.
*   **Entidades**: Modelos de datos puros y validación (Pydantic). Ej: `Transcription`, `AudioChunk`, `SystemStats`.
*   **Interfaces (Protocolos)**: Contratos que la infraestructura debe cumplir. Utilizamos `typing.Protocol` para chequeo estático y dinámico (`@runtime_checkable`).
    *   `TranscriptionService`
    *   `LLMService`
    *   `AudioSource`

### 2. Aplicación (`v2m/application/`)
**Responsabilidad**: Orquestar los casos de uso. Conecta los puertos con los adaptadores.
*   **Handlers**: Clases que ejecutan una acción específica.
    *   `TranscribeAudioHandler`: Recibe audio -> Llama a `TranscriptionService` -> Guarda en Historial -> Emite Evento.
*   **Eventos**: Definición de eventos del sistema (`TranscriptionCompleted`, `ErrorOccurred`).

### 3. Infraestructura (`v2m/infrastructure/`)
**Responsabilidad**: Implementar los detalles técnicos "sucios".
*   **Adaptadores de Audio**: `AudioRecorder` que usa `v2m_engine` (Rust) para grabar WAVs.
*   **Adaptadores de IA**: `WhisperTranscriptionService`, `GeminiLLMService`, `OllamaLLMService`.
*   **Monitor**: `SystemMonitor` para leer métricas de hardware.

### 4. Core (`v2m/core/`)
**Responsabilidad**: Servicios transversales y "pegamento".
*   **Dependency Injection**: `Container` que cablea la aplicación al inicio.
*   **IPC Protocol**: Manejo del socket Unix y serialización de mensajes.
*   **Logging**: Configuración de logs estructurados.

---

## 🔄 Flujo de Control (IPC)

El backend opera como un demonio reactivo.

1.  **Main Loop**: `v2m.main` inicia el `Container` y el servidor `AsyncUnixServer`.
2.  **Recepción de Comando**: Llega un `START_RECORDING` por el socket.
3.  **Despacho**: El `Daemon` busca el handler correspondiente en la capa de Aplicación.
4.  **Ejecución**:
    *   La capa de Aplicación pide al `AudioRecorder` (Infraestructura) que empiece a capturar.
    *   El `AudioRecorder` delega al thread de Rust.
5.  **Respuesta**: Se envía un `{"status": "success"}` al frontend.

---

## 🛡️ Principios de Diseño SOTA 2026

*   **Inmutabilidad**: Las entidades del dominio son inmutables (`frozen=True`) para evitar efectos secundarios.
*   **Async First**: Todo el I/O es asíncrono. Las tareas de CPU intensivas (NumPy, Inferencia) se ejecutan en `ThreadPools` o procesos separados para no bloquear el `asyncio.loop`.
*   **Tipado Estricto**: 100% de cobertura de tipos (Mypy/Pyright compliant).
