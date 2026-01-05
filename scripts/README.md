# 🛠️ Scripts de Utilidad (Ops & Mantenimiento)

Colección curada de herramientas para el ciclo de vida de **Voice2Machine**.
Desde la instalación hasta el diagnóstico profundo.

## 🚀 Scripts Principales (Uso Diario)

| Script          | Propósito                                                                      |
| :-------------- | :----------------------------------------------------------------------------- |
| `v2m-daemon.sh` | **El Servicio**. Inicia/Detiene el backend en segundo plano.                   |
| `v2m-toggle.sh` | **El Gatillo**. Alterna (Inicio/Fin) grabación. Ideal para atajos de teclado.  |
| `v2m-llm.sh`    | **La IA**. Toma el portapapeles, lo refina con Gemini/Local y lo pega de vuelta.|

## 🩺 Diagnóstico y Benchmarks

Si algo falla, ejecuta esto antes de abrir un issue.

- **`check_cuda.py`**: ¿Es tu GPU visible para PyTorch/CUDA?
- **`diagnose_audio.py`**: Vúmetro de consola. Verifica si tu micrófono capta sonido.
- **`benchmark_latency.py`**: Mide milisegundos exactos de "Cold Start" vs "Warm Start".
- **`test_whisper_gpu.py`**: Descarga un modelo "tiny" y transcribe un audio de prueba.
- **`verify_daemon.py`**: Test de integración E2E. Simula un cliente conectando al socket.

## 🧹 Mantenimiento

- **`cleanup.py`**: Elimina logs, archivos temporales (`/tmp/v2m_*`) y caché corrupta.
- **`install.sh`**: El script de instalación "mágico" idempotente.
