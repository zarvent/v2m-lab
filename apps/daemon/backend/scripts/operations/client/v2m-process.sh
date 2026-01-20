#!/bin/bash

#
# v2m-process.sh - script para procesar el texto del portapapeles
#
# DESCRIPCIÓN
#   este script lee lo que tengas copiado en el portapapeles y se lo envía
#   a v2m para procesarlo con inteligencia artificial es ideal para usarlo
#   con un atajo de teclado
#
# USO
#   ./scripts/v2m-process.sh
#
# CÓMO FUNCIONA
#   1 lee el contenido del portapapeles
#   2 envía el texto al sistema principal
#   3 copia el resultado procesado al portapapeles
#   4 te avisa si todo salió bien o si hubo un error
#
# DEPENDENCIAS
#   - xclip para leer el portapapeles
#   - notify-send para mostrar notificaciones
#   - entorno virtual de python en ./venv
#
# INTEGRACIÓN CON ATAJOS DE TECLADO
#   en gnome
#   gsettings set org.gnome.settings-daemon.plugins.media-keys \
#     custom-keybindings "['/org/gnome/.../custom0/']"
#   gsettings set ... command "$HOME/v2m/scripts/v2m-process.sh"
#
# NOTAS
#   - necesitas una sesión gráfica para usar el portapapeles
#   - te avisará si el portapapeles está vacío
#
# AUTOR
#   equipo voice2machine
#
# DESDE
#   v1.0.0
#

# --- CONFIGURACIÓN ---
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$( cd "$( dirname "${SCRIPT_DIR}" )/.." &> /dev/null && pwd )"
NOTIFY_EXPIRE_TIME=3000

# --- RUTAS DERIVADAS ---
VENV_PATH="${PROJECT_DIR}/venv"
MAIN_SCRIPT="${PROJECT_DIR}/src/v2m/main.py"

# --- FUNCIÓN PRINCIPAL ---
run_orchestrator() {
    local text_to_process=$1

    # OPTIMIZATION: Use lightweight IPC client
    local CLIENT_SCRIPT="${SCRIPT_DIR}/../utils/send_command.py"
    if [ -f "$CLIENT_SCRIPT" ]; then
        # send_command.py handles json wrapping if arg is not json
        python3 "$CLIENT_SCRIPT" "PROCESS_TEXT" "$text_to_process"
        return $?
    fi

    # Legacy/Fallback method
    if [ ! -f "${VENV_PATH}/bin/activate" ]; then
        notify-send --expire-time=${NOTIFY_EXPIRE_TIME} "❌ error de v2m" "no encontré el entorno virtual en ${VENV_PATH}"
        exit 1
    fi

    source "${VENV_PATH}/bin/activate"
    export PYTHONPATH="${PROJECT_DIR}/src"
    # Note: Sending via main.py "process" args might behave differently than IPC command
    # Assuming intention is to send to daemon
    python3 -m v2m.client "PROCESS_TEXT" "$text_to_process"
}

# --- LÓGICA PRINCIPAL ---
clipboard_content=$(xclip -o -selection clipboard)
if [ -n "${clipboard_content}" ]; then
    run_orchestrator "${clipboard_content}"
else
    notify-send --expire-time=${NOTIFY_EXPIRE_TIME} "❌ error" "el portapapeles está vacío"
    exit 1
fi
