# Audio Infrastructure

Este submódulo maneja todo lo relacionado con la captura y procesamiento de audio a bajo nivel.

## Contenido

- `recorder.py` - Clase `AudioRecorder` que gestiona la captura de audio usando `sounddevice` con buffers pre-allocados para alto rendimiento
- `recording_worker.py` - Script para ejecutar la grabación en un proceso aislado si es necesario (para evitar problemas de GIL o bloqueos)

## Características

- Soporte para grabación en hilo de fondo
- Acceso directo a buffers numpy para eficiencia (zero-copy)
- Manejo robusto de errores de dispositivos de audio
