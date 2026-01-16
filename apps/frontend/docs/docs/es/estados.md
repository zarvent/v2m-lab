# Gestión de Estado y Datos

El frontend de Voice2Machine utiliza **Zustand** para gestionar el estado global. La arquitectura se divide en tres stores principales para separar preocupaciones y optimizar el rendimiento.

---

## 🏗️ Stores Globales

### 1. BackendStore (`src/stores/backendStore.ts`)

Es la "fuente de verdad" del estado del sistema. Gestiona la lógica de negocio y la comunicación con el daemon.

**Estados Clave:**
- `status`: Estado actual de la máquina de estados (`idle` | `recording` | `transcribing` | `paused`).
- `transcription`: Texto acumulado de la sesión actual.
- `isConnected`: Booleano que indica si el puente IPC está activo.
- `history`: Lista persistente de transcripciones pasadas.

**Acciones Principales:**
- `startRecording(mode)`: Inicia la captura de audio.
- `stopRecording()`: Detiene la captura y solicita la transcripción final.
- `processText()`: Envía el texto actual al LLM para refinamiento.

### 2. TelemetryStore (`src/stores/telemetryStore.ts`)

Store especializado de alta frecuencia.

**Problema:** Los datos de CPU/GPU llegan cada 100ms. Si se almacenaran en el store principal, provocarían re-renders masivos en toda la UI.
**Solución:** Este store vive aislado. Solo los componentes que visualizan gráficas (ej. Sidebar) se suscriben a él.

**Optimización `isTelemetryEqual`:**
Antes de actualizar el estado, se comparan los valores nuevos con los anteriores usando una tolerancia (epsilon). Si el cambio es insignificante (ej. CPU pasa de 10.1% a 10.2%), **no** se dispara la actualización, ahorrando ciclos de renderizado.

### 3. UiStore (`src/stores/uiStore.ts`)

Gestiona el estado puramente visual y efímero.

- `activeView`: La pantalla que ve el usuario (`studio`, `settings`, etc.).
- `modals`: Diccionario de visibilidad de ventanas modales.

---

## 🔌 Tipos IPC (`src/types/ipc.ts`)

El contrato de datos entre Rust y TypeScript es estricto.

### DaemonState

Es el payload que el backend envía cada vez que ocurre algo importante.

```typescript
export interface DaemonState {
  // Estado actual del motor
  state: "idle" | "recording" | "transcribing" | "processing" | "paused" | "restarting" | "disconnected";

  // Texto en tiempo real (parcial) o final
  transcription?: string;

  // Resultado del procesamiento de LLM
  refined_text?: string;

  // Mensajes de error o informativos
  message?: string;

  // Snapshot de recursos (opcional, suele ir en evento separado)
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
  gpu?: { // Opcional (solo si NVIDIA/AMD detectada)
    name: string;
    vram_used_mb: number;
    vram_total_mb: number;
    temp_c: number;
  };
}
```
