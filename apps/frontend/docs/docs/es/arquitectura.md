# Arquitectura del Frontend

La arquitectura del frontend de Voice2Machine sigue un patrón de **visión desacoplada**. La lógica pesada de procesamiento de audio y transcripción reside en el Daemon de Python, mientras que el frontend actúa como un orquestador visual y gestor de estado.

## 🌉 Puente IPC y Comunicación

El flujo de comunicación es jerárquico y seguro para garantizar que la interfaz nunca se bloquee (Non-blocking UI):

1.  **React (Capa de Vista)**: Invoca un comando de Tauri (ej. `start_recording`).
2.  **Rust (Capa de Seguridad)**: Intercepta la llamada, valida los parámetros y se comunica con el Daemon mediante un **Socket Unix**.
3.  **Daemon (Capa de Core)**: Procesa la solicitud (Inferencia de Whisper/LLM) y devuelve la respuesta al socket.
4.  **Rust**: Recibe la respuesta y la resuelve hacia la promesa original en React.

### Gestión Automática de Estado

La aplicación utiliza un componente `BackendInitializer` que se encarga de sincronizar el estado del backend con el frontend mediante dos mecanismos:

- **Eventos (Push)**: Escucha eventos `v2m://state-update` emitidos por Rust cuando el daemon cambia de estado (ej. "Grabando").
- **Polling (Fallback)**: Si no hay eventos recientes, realiza un `get_status` periódico para asegurar la conexión.

## 🧠 Gestión de Estado (Zustand)

Hemos adoptado un enfoque de **Stores Primero**. Los componentes de React no deberían llamar a `invoke()` directamente. En su lugar, interactúan con las stores de Zustand localizadas en `src/stores/`.

- **`backendStore.ts`**: Fuente de verdad para el estado del daemon (transcripción actual, modo de grabación, errores, conexión).
- **`uiStore.ts`**: Gestiona el estado visual volátil (navegación activa, modales abiertos).
- **`telemetryStore.ts`**: Almacena datos de rendimiento (CPU, RAM, VRAM) recibidos mediante telemetría.

## 📝 Validación con Zod

La configuración de la aplicación (mapeada desde el `config.toml` del backend) se valida rigurosamente en el frontend usando **Zod**. Esto garantiza que nunca se envíe una configuración inválida al motor de transcripción, evitando fallos catastróficos.

El esquema principal reside en [src/schemas/config.ts](../../src/schemas/config.ts).
