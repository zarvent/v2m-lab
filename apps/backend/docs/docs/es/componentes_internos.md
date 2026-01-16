# Componentes Internos del Backend

Este documento detalla la implementación interna de los servicios clave del backend de Voice2Machine, explicando cómo interactúan los adaptadores de infraestructura con las extensiones nativas de Rust.

## 🧠 Motor de Transcripción (`WhisperTranscriptionService`)

Es el componente más complejo del sistema, encargado de orquestar la captura de audio, el filtrado de voz y la inferencia del modelo Whisper.

### Arquitectura de Streaming
Para lograr una experiencia de usuario fluida, la transcripción no ocurre en un solo bloque monolítico.

1.  **AudioRecorder (Rust/Python)**: Captura chunks de audio crudo (PCM float32) desde el micrófono.
2.  **StreamingTranscriber**: Mantiene un buffer circular de audio.
3.  **VAD (Voice Activity Detection)**: Antes de enviar audio a Whisper, el motor de Rust analiza si hay voz humana. Si es silencio, se descarta para ahorrar GPU.
4.  **Inferencia**: Cuando se detecta suficiente audio con voz, se envía a `PersistentWhisperWorker`.

### `PersistentWhisperWorker`
La carga del modelo Whisper (especialmente `large-v3`) es costosa (2-5 segundos). Este worker mantiene el modelo cargado en VRAM en un hilo separado, recibiendo trabajos a través de una cola thread-safe.

*   **Lazy Loading**: El modelo solo se carga en la primera petición.
*   **Keep-Warm**: Se mantiene activo durante la sesión, pero puede liberarse si se necesita la VRAM para otras tareas (configurable).

---

## 🦀 Extensión Nativa (`v2m_engine`)

Para superar las limitaciones del GIL de Python en tareas de tiempo real, utilizamos una extensión escrita en Rust.

### `AudioEngine`
Maneja la E/S de audio de bajo nivel.
*   **Zero-Copy Recording**: Escribe los buffers de audio directamente a disco (WAV) sin pasar por objetos Python, reduciendo la latencia y el uso de CPU.
*   **Safety**: Garantiza que no haya *race conditions* al acceder al dispositivo de audio.

### `VoiceActivityDetector`
Implementación de VAD basada en `webrtc-vad` o `silero` (según compilación), ejecutada en Rust.
*   Latencia < 1ms por chunk.
*   Decide si un frame de audio debe ser procesado o descartado.

---

## 📊 Monitor de Sistema (`SystemMonitor`)

Provee telemetría en tiempo real para el frontend.

*   **GPU (NVIDIA)**: Utiliza `nvml-wrapper` (Rust binding) o `pynvml` para leer uso de VRAM, temperatura y % de carga. Prioriza la implementación Rust para evitar bloquear el Main Thread de Python.
*   **CPU/RAM**: Utiliza `psutil` para métricas del sistema operativo.

---

## 🔌 Inyección de Dependencias (`Container`)

El backend utiliza un contenedor de DI (`v2m.core.di.container`) para ensamblar la aplicación.

```python
# Ejemplo simplificado
container = Container()
container.transcription_service = providers.Singleton(
    WhisperTranscriptionService,
    worker=container.whisper_worker
)
```

Esto permite sustituir implementaciones reales por Mocks durante los tests (ej. `MockTranscriptionService` que devuelve texto fijo sin cargar Whisper).
