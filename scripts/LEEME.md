# 🛠️ Scripts de Utilidad (Ops & Maint)

Colección curada de herramientas para el ciclo de vida de **Voice2Machine**.
Desde la instalación hasta el diagnóstico profundo.

## 🚀 Scripts Core (Uso Diario)

| Script          | Propósito                                                                     |
| :-------------- | :---------------------------------------------------------------------------- |
| `v2m-daemon.sh` | **El Servicio**. Inicia/Detiene el backend en segundo plano.                  |
| `v2m-toggle.sh` | **El Gatillo**. Conmuta (Start/Stop) la grabación. Mapear a atajo de teclado. |
| `v2m-llm.sh`    | **La IA**. Toma el portapapeles, lo refina con Gemini y lo pega de vuelta.    |

## 🩺 Diagnóstico y Benchmarks

Si algo falla, ejecuta esto antes de abrir un issue.

- **`check_cuda.py`**: ¿Tu GPU está visible para PyTorch?
- **`diagnose_audio.py`**: Vúmetro en consola. Verifica si tu micro está captando sonido.
- **`benchmark_latency.py`**: Mide milisegundos exactos de "Cold Start" vs "Warm Start".
- **`test_whisper_gpu.py`**: Descarga un modelo "tiny" y transcribe un audio de prueba.
- **`verify_daemon.py`**: Test de integración end-to-end. Simula un cliente conectándose al socket.

## 🧹 Mantenimiento

- **`cleanup.py`**: Borra logs, archivos temporales (`/tmp/v2m_*`) y caché de modelos corruptos.
- **`install.sh`**: El script "mágico" de instalación idempotente.
