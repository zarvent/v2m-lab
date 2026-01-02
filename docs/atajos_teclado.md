#!/bin/bash

# ==============================================================================
# v2m-llm.sh - Trigger cliente para procesamiento de texto con V2M Daemon
# ==============================================================================
# Mantiene la licencia GPLv3 del proyecto voice2machine.
#
# DESCRIPCIÓN TÉCNICA:
#   Actúa como puente entre el portapapeles del SO (X11/Wayland) y el
#   núcleo de inferencia (apps/backend).
#   No realiza inferencia per se; delega al daemon via IPC/CLI.
# ==============================================================================

# Modo estricto: detiene ejecución ante errores, variables no definidas o fallos en pipes
set -euo pipefail

# --- Resolución de Rutas (Monorepo Aware) ---
# Obtiene la ruta real del script, resolviendo symlinks
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
# Asumimos estructura: root/scripts/v2m-llm.sh -> root/apps/backend
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="${PROJECT_ROOT}/apps/backend"
VENV_PYTHON="${BACKEND_DIR}/venv/bin/python"
ENTRY_POINT="${BACKEND_DIR}/src/v2m/main.py"

# --- Configuración Visual ---
ICON_SUCCESS="face-wink"
ICON_ERROR="dialog-error"
ICON_WORKING="system-run"
APP_NAME="Voice2Machine"

# --- Funciones Auxiliares ---

notify() {
    local level="$1" # low, normal, critical
    local title="$2"
    local msg="$3"
    local icon="$4"

    if command -v notify-send >/dev/null 2>&1; then
        notify-send -u "$level" -i "$icon" -a "$APP_NAME" "$title" "$msg"
    fi
}

get_clipboard_content() {
    # Detección automática de servidor de visualización
    if [ "${XDG_SESSION_TYPE:-}" == "wayland" ] && command -v wl-paste >/dev/null 2>&1; then
        wl-paste --no-newline
    elif command -v xclip >/dev/null 2>&1; then
        xclip -o -selection clipboard
    else
        notify "critical" "Error de Dependencia" "No se encontró xclip ni wl-paste." "$ICON_ERROR"
        exit 1
    fi
}

# --- Validación de Entorno ---

if [ ! -x "$VENV_PYTHON" ]; then
    notify "critical" "Error de Entorno" "No se encuentra el intérprete Python en:\n$VENV_PYTHON" "$ICON_ERROR"
    exit 1
fi

if [ ! -f "$ENTRY_POINT" ]; then
    notify "critical" "Error de Archivo" "No se encuentra el entry point:\n$ENTRY_POINT" "$ICON_ERROR"
    exit 1
fi

# --- Ejecución Principal ---

# 1. Obtener texto
CONTENT=$(get_clipboard_content)

# 2. Validar contenido
if [ -z "$CONTENT" ] || [[ "$CONTENT" =~ ^[[:space:]]*$ ]]; then
    notify "low" "Portapapeles Vacío" "Copia texto antes de ejecutar." "$ICON_ERROR"
    exit 0
fi

# 3. Notificar inicio (Feedback UX inmediato)
notify "low" "Procesando..." "Enviando al LLM Local/Remoto..." "$ICON_WORKING"

# 4. Invocar Daemon/Backend
# Nota: Pasamos el texto como argumento. Si el texto es GIGANTE (>128KB),
# considerar pasar por archivo temporal o stdin en el futuro.
if ! "$VENV_PYTHON" "$ENTRY_POINT" PROCESS_TEXT "$CONTENT"; then
    notify "critical" "Fallo de Procesamiento" "El backend devolvió un error. Revisa los logs." "$ICON_ERROR"
    exit 1
fi

# El backend (main.py) debería encargarse de poner el resultado en el clipboard
# y enviar la notificación final de éxito.
