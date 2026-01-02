# scripts de utilidad

colección de scripts para mantenimiento pruebas benchmarks y gestión del servicio v2m

contenido principal

**gestión del servicio**
- `install_service.py` instala v2m como un servicio systemd de usuario
- `v2m-daemon.sh` wrapper para iniciar el daemon
- `v2m-toggle.sh` script para alternar grabación (usado por atajos de teclado)

**diagnóstico y pruebas**
- `check_cuda.py` verifica si la gpu nvidia es detectada correctamente
- `diagnose_audio.py` herramienta interactiva para probar micrófonos y niveles de audio
- `benchmark_latency.py` mide el rendimiento del sistema (cold start inferencia vad)
- `test_whisper_gpu.py` descarga y prueba el modelo whisper en gpu
- `verify_daemon.py` test de integración completo del sistema

**mantenimiento**
- `cleanup.py` herramienta para limpiar archivos temporales cache y logs antiguos

uso
la mayoría de estos scripts deben ejecutarse desde la raíz del repositorio
ejemplo
```bash
python3 scripts/check_cuda.py
```
