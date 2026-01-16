# Arquitectura del Frontend

La arquitectura del frontend de Voice2Machine sigue un patrón de **visión desacoplada** y **Reactividad Extrema**. La lógica pesada de procesamiento de audio y transcripción reside en el Daemon de Python, mientras que el frontend actúa como un orquestador visual ligero y gestor de estado.

!!! abstract "Filosofía State of the Art 2026"
    El diseño prioriza la **latencia cero** en la interfaz. La UI nunca debe bloquearse esperando al backend. Todas las operaciones pesadas son asíncronas y notifican su progreso mediante eventos, permitiendo que la interfaz se mantenga a 60/120 FPS constantes incluso durante cargas intensas de inferencia.

---

## 🏗️ Estructura de Directorios

El código fuente se organiza siguiendo una estructura fractal por dominio técnico y funcional:

```
apps/frontend/src/
├── components/      # Componentes de React
│   ├── settings/    # Módulos del panel de configuración
│   ├── studio/      # Componentes del editor y grabadora
│   └── ...          # Componentes compartidos (Sidebar, Toast, etc.)
├── hooks/           # Custom Hooks reutilizables (Lógica de UI)
├── stores/          # Estado global (Zustand) - La "Base de Datos" del frontend
├── schemas/         # Definiciones de validación (Zod)
├── types/           # Definiciones de TypeScript e Interfaces IPC
├── utils/           # Utilidades puras (formato, clases, tiempo)
├── App.tsx          # Componente raíz y Layout principal
└── main.tsx         # Punto de entrada y montaje de React
```

---

## 🌉 Puente IPC y Comunicación (Tauri Bridge)

El frontend se comunica con el sistema operativo y el daemon de Python a través del puente seguro de Tauri. No existe comunicación directa HTTP/WebSocket insegura; todo pasa por el bus de mensajes de Rust.

### Flujo de Datos

1.  **React (Vista)**: El usuario interactúa (ej. clic en "Grabar").
2.  **Action (Zustand)**: El store `backendStore` invoca un comando Tauri (`invoke("start_recording")`).
3.  **Rust (Core)**:
    - Valida el comando.
    - Envía la instrucción al Daemon Python vía Socket Unix.
    - Devuelve una promesa inmediata al frontend ("Comando recibido").
4.  **Daemon (Python)**:
    - Ejecuta la lógica.
    - Emite eventos de estado (`recording`, `transcribing`) conforme avanza.
5.  **Event Listeners**: El frontend escucha eventos `v2m://state-update` y actualiza el store reactivamente.

### Payload de Estado (DaemonState)

El contrato de comunicación se define estrictamente en `src/types/ipc.ts`:

```typescript
export interface DaemonState {
  state: "idle" | "recording" | "transcribing" | "processing" | "paused";
  transcription?: string;  // Texto parcial o final
  refined_text?: string;   // Texto post-procesado por LLM
  message?: string;        // Mensajes de error o info
  telemetry?: TelemetryData; // Datos de CPU/GPU/RAM
}
```

---

## 🧠 Gestión de Estado (Zustand)

Hemos adoptado un enfoque de **Stores Primero**. Los componentes de React **nunca** deben invocar `invoke()` directamente ni gestionar lógica de negocio compleja.

### 1. BackendStore (`backendStore.ts`)
Actúa como el **gemelo digital** del daemon.
- **Responsabilidad**: Mantener sincronizado el estado de la UI con la realidad del backend.
- **Datos**: Historial de transcripciones, estado de conexión, errores del sistema.

### 2. TelemetryStore (`telemetryStore.ts`)
Canal de alta frecuencia optimizado.
- **Responsabilidad**: Visualizar el consumo de recursos sin provocar re-renderizados en el resto de la app.
- **Optimización**: Utiliza comparación profunda (`isTelemetryEqual`) con umbrales (ej. cambio > 1%) para evitar actualizaciones de estado innecesarias (ruido).

### 3. UiStore (`uiStore.ts`)
Estado efímero de la interfaz.
- **Responsabilidad**: Controlar qué vista está activa (Studio, Settings), qué modales están abiertos y la gestión de notificaciones (Toasts).

---

## 📝 Validación y Seguridad (Zod)

La configuración de la aplicación es crítica. Un valor incorrecto podría crashear el motor de inferencia.
Por ello, utilizamos **Zod** para validar estrictamente cualquier configuración antes de guardarla o enviarla al backend.

- **Esquemas**: Definidos en `src/schemas/config.ts`.
- **Sincronización**: Los esquemas de Zod deben coincidir exactamente con los modelos Pydantic del backend (`v2m/config.py`).
