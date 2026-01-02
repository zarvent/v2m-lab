# CLIPBOARD FIX - 2025-11-19

## PROBLEMA DETECTADO / DETECTED PROBLEM

El portapapeles no funcionaba cuando se ejecutaba desde el daemon debido a:

1. **PYPERCLIP** dependía de variables de entorno (`DISPLAY` o `WAYLAND_DISPLAY`) que no estaban disponibles en procesos daemon
2. **PYPERCLIP** no manejaba correctamente la naturaleza asíncrona de **xclip**

## SOLUCIÓN IMPLEMENTADA / IMPLEMENTED SOLUTION

### Cambios en `src/v2m/infrastructure/linux_adapters.py`:

1. **Eliminada dependencia de PYPERCLIP**: Reemplazado con llamadas directas a `xclip` (X11) o `wl-clipboard` (Wayland)
2. **Detección automática de backend**: El adaptador detecta si el sistema usa X11 o Wayland
3. **Captura de variables de entorno**: Se capturan `DISPLAY` o `WAYLAND_DISPLAY` del entorno al inicializar
4. **Manejo correcto de xclip**: `xclip` necesita quedarse en background para servir el contenido del clipboard, por lo que usamos `Popen()` sin `wait()`
5. **Sleep mínimo**: Agregado `time.sleep(0.05)` después de escribir para dar tiempo a xclip de procesar

### Arquitectura del Fix:

```python
LinuxClipboardAdapter:
  ├── __init__() -> Detecta backend (X11/Wayland)
  ├── _detect_environment() -> Captura DISPLAY/WAYLAND_DISPLAY
  ├── _get_clipboard_commands() -> Retorna comandos según backend
  ├── copy(text) -> Lanza xclip/wl-copy en background
  └── paste() -> Lee de xclip/wl-paste
```

### Detalles Técnicos:

**xclip** con `-selection clipboard` (sin `-in`) se queda corriendo en background esperando que otras aplicaciones soliciten el contenido del portapapeles. Esto es por diseño de X11.

**NUNCA usar `subprocess.run()` con timeout** para copiar al clipboard, porque el proceso nunca termina por sí solo.

**CORRECTO**:
```python
process = subprocess.Popen(
    ["xclip", "-selection", "clipboard"],
    stdin=subprocess.PIPE,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.PIPE
)
process.stdin.write(text.encode("utf-8"))
process.stdin.close()
time.sleep(0.05)  # Dar tiempo a procesar
# NO hacer wait()
```

## TESTING

Ejecutar:
```bash
./venv/bin/python scripts/test_clipboard.py
```

Resultado esperado: `✅ SUCCESS`

## INICIO DEL DAEMON / DAEMON STARTUP

### Opción 1: Manual (para desarrollo)

```bash
cd /home/zarvent/v2m
export PYTHONPATH=/home/zarvent/v2m/src
./venv/bin/python -m v2m.main --daemon > /tmp/v2m_daemon.log 2>&1 &
```

### Opción 2: Systemd (para producción)

```bash
cd /home/zarvent/v2m
./venv/bin/python scripts/install_service.py
```

Esto instalará un servicio de usuario que:
- Se inicia automáticamente al login
- Captura variables de entorno del `.env`
- Configura PYTHONPATH correctamente
- Redirige logs a systemd journal

### Verificar daemon:

```bash
# Ver si está corriendo
ps aux | grep "v2m.main --daemon"

# Ver logs
tail -f /tmp/v2m_daemon.log

# Ping test
export PYTHONPATH=/home/zarvent/v2m/src
./venv/bin/python -c "import asyncio; from v2m.client import send_command; print(asyncio.run(send_command('PING')))"
```

## DEPENDENCIAS ELIMINADAS

- ~~pyperclip~~ (removido de `requirements.txt`)

## DEPENDENCIAS DEL SISTEMA REQUERIDAS

- **xclip** (para X11) o **wl-clipboard** (para Wayland)

Instalar si no está disponible:
```bash
sudo apt install xclip  # Para X11
sudo apt install wl-clipboard  # Para Wayland
```

---

## AUDITORÍA TÉCNICA / TECHNICAL AUDIT

### DECISIÓN CRÍTICA
Reemplazar PYPERCLIP con subprocess directo a xclip/wl-clipboard porque:
1. **Control total del entorno**: Podemos pasar explícitamente `DISPLAY` capturado durante la inicialización
2. **Manejo correcto del lifecycle**: PYPERCLIP ocultaba el hecho de que xclip se queda en background
3. **Sin overhead**: Una dependencia menos, ejecución más rápida
4. **Debugging más fácil**: Los logs muestran exactamente qué comando se ejecuta y con qué env vars

### DEUDA TÉCNICA POTENCIAL
1. **Procesos zombie de xclip**: Si el sistema hace muchas copias sin limpiar, pueden acumularse procesos xclip en background. Mitigación: El OS los limpia cuando ya no son necesarios, pero podríamos implementar un reaper si se vuelve problema.
2. **Race condition en lecturas inmediatas**: El `sleep(0.05)` es una solución pragmática pero no 100% garantizada. Si hay problemas, incrementar a 0.1s.
3. **Wayland no testeado**: La lógica de wl-copy es similar pero no ha sido testeada en este PR. Requiere testing en sistema Wayland real.
