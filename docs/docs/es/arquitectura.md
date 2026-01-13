# 🧩 Arquitectura del Sistema

!!! abstract "Filosofía Técnica"
    **Voice2Machine** implementa una **Arquitectura Hexagonal (Ports & Adapters)** estricta, priorizando el desacoplamiento, la testabilidad y la independencia tecnológica. El sistema se adhiere a estándares SOTA 2026 como tipos estáticos en Python (Protocol) y separación Frontend/Backend mediante IPC binario.

---

## 🏗️ Diagrama de Alto Nivel

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

## 📦 Componentes del Backend

### 1. Core (El Hexágono)
Ubicado en `apps/backend/src/v2m/core/` y `domain/`.
*   **Puertos (Interfaces)**: Definidos usando `typing.Protocol` + `@runtime_checkable` para chequeo estructural en tiempo de ejecución.
*   **CQRS**: Toda acción es un `Command` (DTO Pydantic) procesado por un `CommandHandler` vía un `CommandBus`.

### 2. Application
Ubicado en `apps/backend/src/v2m/application/`.
*   Orquesta la lógica de negocio pura.
*   Ejemplo: `TranscribeAudioHandler` recibe el audio, invoca al puerto `TranscriptionService`, y notifica eventos.

### 3. Infrastructure
Ubicado en `apps/backend/src/v2m/infrastructure/`.
*   **WhisperAdapter**: Implementación concreta usando `faster-whisper`. Gestiona la carga diferida (lazy loading) para ahorrar VRAM.
*   **SystemMonitor**: Servicio crítico que monitorea uso de GPU/CPU en tiempo real para telemetría.
*   **ProviderRegistry**: Patrón Factory para instanciar dinámicamente proveedores LLM (Gemini/Ollama) según configuración.

---

## ⚡ Comunicación Frontend-Backend (IPC)

Voice2Machine evita HTTP/REST para maximizar rendimiento local. Utiliza **Unix Domain Sockets** con un protocolo personalizado:

1.  **Header**: 4 bytes (Big Endian) indicando longitud.
2.  **Payload**: JSON utf-8.
3.  **Persistencia**: La conexión se mantiene viva (Keep-Alive), eliminando el *handshake overhead*.

---

## 🦀 Extensiones Nativas (Rust)

Para tareas críticas donde el GIL de Python es un cuello de botella, utilizamos extensiones nativas compiladas en Rust (`v2m_engine`):
*   **Audio I/O**: Escritura de WAVs directa a disco (Zero-copy).
*   **VAD**: Detección de voz de ultra-baja latencia.

---

## 🛡️ Principios de Diseño 2026

1.  **Local-First & Privacy-By-Design**: Ningún dato sale de la máquina a menos que se configure explícitamente un proveedor de nube.
2.  **Resiliencia**: El Daemon implementa recuperación automática de errores y reinicio de subsistemas (ej. si el driver de audio crashea).
3.  **Observabilidad**: Logging estructurado (OpenTelemetry standard) y métricas en tiempo real expuestas al frontend.
