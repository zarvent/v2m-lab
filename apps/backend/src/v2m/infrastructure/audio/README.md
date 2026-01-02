# audio infrastructure

este submódulo maneja todo lo relacionado con la captura y procesamiento de audio a bajo nivel

contenido
- `recorder.py` clase `AudioRecorder` que gestiona la captura de audio usando `sounddevice` con buffers pre-allocados para alto rendimiento
- `recording_worker.py` script para ejecutar la grabación en un proceso aislado si es necesario (para evitar problemas de gil o bloqueos)

características
- soporte para grabación en hilo de fondo
- acceso directo a buffers numpy para eficiencia (zero-copy)
- manejo robusto de errores de dispositivos de audio
