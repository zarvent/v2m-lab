# Gestión del Ciclo de Vida del Demonio

Esta guía detalla los procedimientos para iniciar, detener y reiniciar el servicio central (Daemon) de Voice2Machine. Está dividida en secciones según el nivel de complejidad y control requerido.

---

## 🐣 Para Juniors: Procedimientos Estándar

El "Happy Path" para el desarrollo diario. Si solo necesitas que el backend funcione para probar el frontend o grabar audio, sigue estos pasos.

### 1. Iniciar el Demonio
El demonio debe correr en su propia terminal para que puedas ver los logs en tiempo real.

```bash
# 1. Asegúrate de estar en el directorio del backend
cd apps/backend

# 2. Activa el entorno virtual (¡Crucial!)
source venv/bin/activate

# 3. Inicia el proceso
python -m v2m.main --daemon
```

Verás mensajes como `uvloop habilitado` y `entorno gpu configurado`. Cuando veas `grabación y streaming iniciados` (o similar al interactuar), está listo.

### 2. Reiniciar (Soft Restart)
Si cambiaste código en Python (archivos `.py`) o la configuración (`config.toml`), necesitas reiniciar.

1. Ve a la terminal donde corre el demonio.
2. Presiona `Ctrl + C` **una sola vez**.
3. Espera a que aparezca el mensaje `Shutdown complete`.
4. Ejecuta nuevamente: `python -m v2m.main --daemon`

> **Nota:** No cierres la terminal bruscamente. Permitir el cierre ordenado libera el micrófono y la memoria de la GPU.

---

## 👴 Para Seniors: Arquitectura y Depuración

Detalles de bajo nivel sobre cómo el demonio maneja los recursos, señales y el entorno de ejecución (SOTA 2026).

### Arquitectura de Ejecución
El demonio no es un script simple; es un orquestador asíncrono que maneja recursos críticos de hardware.

1.  **Bootstrapping de Entorno (`v2m.utils.env`)**: Antes de cargar `torch` o `faster-whisper`, el proceso inyecta dinámicamente las librerías `cuDNN` y `Cublas` en el espacio de memoria usando `ctypes` y `RTLD_GLOBAL`. Esto evita conflictos con drivers del sistema.
2.  **Event Loop (`uvloop`)**: Se instala `uvloop` (basado en `libuv`) reemplazando al loop estándar de `asyncio` para reducir la latencia en I/O y manejo de señales.
3.  **Gestión de Señales**: El contenedor de inyección de dependencias intercepta `SIGINT` (KeyboardInterrupt) y `SIGTERM`.

### Procedimiento de "Hard Reset" (Kill & Clean)
Si el demonio se congela (ej. deadlock en hilos de CTranslate2 o buffer de audio corrupto), un `Ctrl+C` podría no ser suficiente.

#### 1. Matar el proceso
Busca y termina cualquier instancia huérfana:

```bash
# Opción A: Pkill (Más rápido)
pkill -f "v2m.main --daemon"

# Opción B: Htop (Quirúrgico)
htop -p $(pgrep -f v2m)
```

#### 2. Limpieza de Recursos (Cleanup)
Si el proceso murió mal, verifica lo siguiente:

*   **Socket IPC**: Asegúrate de que no quedó un socket Unix basura (ver [Especificación IPC](referencia_api_ipc.md)).
    ```bash
    ls -l /run/user/$(id -u)/v2m/v2m.sock
    # Si existe y no hay proceso, bórralo (aunque el demonio intenta hacerlo al arrancar).
    rm /run/user/$(id -u)/v2m/v2m.sock
    ```
*   **Memoria VRAM (GPU)**: Si `nvidia-smi` muestra memoria ocupada pero no hay proceso Python, la GPU puede estar en un estado inconsistente (zombie contexts).
    ```bash
    nvidia-smi
    # Si ves procesos 'python' sin PID padre claro, mata los PIDs específicos.
    kill -9 <PID>
    ```

### Logs y Diagnóstico
Si el demonio falla al iniciar, revisa los logs estructurados. Por defecto van a `stdout`, pero en producción pueden rotar a archivo.

```bash
# Ver logs detallados (si están configurados a archivo)
tail -f .gemini/tmp/cf7d35eaf46bfbf614ff17afb4f62eaa1296a9b1dd13ec5220d7166abc761b8b/v2m_debug.log
```

> **Debug de Audio:** Si el VAD corta mucho o no detecta audio, busca en los logs: `"transcripción final vacía (posiblemente filtrado por VAD o silencio)"`. Esto indica que el `threshold` en `config.toml` es muy agresivo para el nivel de ganancia actual.
