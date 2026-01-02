#!/bin/bash

# This file is part of voice2machine.
#
# voice2machine is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# voice2machine is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with voice2machine.  If not, see <https://www.gnu.org/licenses/>.
#
# v2m-toggle.sh - script para activar o desactivar la grabación
#
# DESCRIPCIÓN
#   este es el script principal para controlar la grabación por voz
#   sirve para iniciar y detener la grabación y está pensado para
#   usarse con un atajo de teclado
#
# USO
#   ./scripts/v2m-toggle.sh
#
# CÓMO FUNCIONA
#   primera vez que lo ejecutas
#     1 verifica si el servicio está corriendo y lo inicia si es necesario
#     2 comienza a grabar el audio
#     3 crea un archivo temporal para recordar que está grabando
#
#   segunda vez que lo ejecutas
#     1 se da cuenta de que ya está grabando
#     2 detiene la grabación
#     3 transcribe el audio a texto
#     4 copia el texto al portapapeles
#     5 elimina el archivo temporal
#
# CONFIGURACIÓN EN GNOME
#   # crear un atajo personalizado
#   KEYBINDING_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/whisper0/"
#   gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings \
#     "['$KEYBINDING_PATH']"
#   gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KEYBINDING_PATH \
#     name 'v2m toggle'
#   gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KEYBINDING_PATH \
#     command '$HOME/v2m/scripts/v2m-toggle.sh'
#   gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KEYBINDING_PATH \
#     binding '<Control><Shift>space'
#
# DEPENDENCIAS
#   - v2m-daemon.sh para controlar el servicio

#   - notify-send para mostrar notificaciones en el escritorio
#   - entorno virtual de python en ./venv
#
# ARCHIVOS
#   /tmp/v2m_recording.pid - indica que se está grabando
#
# NOTAS
#   - el servicio arranca solo si no está activo
#   - verás notificaciones sobre lo que está pasando
#
# AUTOR
#   equipo voice2machine
#
# DESDE
#   v1.0.0
#

# --- CONFIGURACIÓN ---
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$( dirname "${SCRIPT_DIR}" )/apps/backend"
NOTIFY_EXPIRE_TIME=3000

# --- LOAD COMMON UTILS ---
source "${SCRIPT_DIR}/common.sh"
RUNTIME_DIR=$(get_runtime_dir)

# --- RUTAS DERIVADAS ---
VENV_PATH="${PROJECT_DIR}/venv"
MAIN_SCRIPT="${PROJECT_DIR}/src/v2m/main.py"
RECORDING_FLAG="${RUNTIME_DIR}/v2m_recording.pid"
DAEMON_SCRIPT="${SCRIPT_DIR}/v2m-daemon.sh"

# --- FUNCIÓN PRINCIPAL ---
# --- FUNCIÓN PRINCIPAL ---
ensure_daemon() {
    "${DAEMON_SCRIPT}" status > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        if command -v notify-send > /dev/null 2>&1; then
            notify-send --expire-time=${NOTIFY_EXPIRE_TIME} "🎙️ v2m" "iniciando el servicio en segundo plano"
        fi

        "${DAEMON_SCRIPT}" start
        if [ $? -ne 0 ]; then
            if command -v notify-send > /dev/null 2>&1; then
                notify-send --expire-time=${NOTIFY_EXPIRE_TIME} "❌ error de v2m" "no pude iniciar el servicio"
            fi
            exit 1
        fi
        # Esperar un momento a que el daemon esté listo
        sleep 2
    fi
}

run_client() {
    local command=$1
    local payload="${2:-}"

    if [ ! -f "${VENV_PATH}/bin/activate" ]; then
        if command -v notify-send > /dev/null 2>&1; then
            notify-send --expire-time=${NOTIFY_EXPIRE_TIME} "❌ error de v2m" "no encontré el entorno virtual en ${VENV_PATH}"
        fi
        exit 1
    fi

    source "${VENV_PATH}/bin/activate"
    export PYTHONPATH="${PROJECT_DIR}/src"
    # URGENT FIX: Usar módulo cliente para output parseable y evitar desincronización
    python3 -m v2m.client "${command}" ${payload}
}

# --- LÓGICA DE CONMUTACIÓN ---
ensure_daemon

# Consultar estado real al daemon (IPC) en lugar de confiar en archivo PID
STATUS_OUTPUT=$(run_client "GET_STATUS")

if [[ "$STATUS_OUTPUT" == *"STATUS: recording"* ]]; then
    # Si está grabando, detener
    run_client "STOP_RECORDING"
elif [[ "$STATUS_OUTPUT" == *"STATUS: idle"* ]] || [[ "$STATUS_OUTPUT" == *"STATUS: paused"* ]]; then
    # Si está inactivo o pausado, iniciar
    run_client "START_RECORDING"
else
    # Estado desconocido o error, intentar iniciar por defecto
    if command -v notify-send > /dev/null 2>&1; then
        notify-send --expire-time=${NOTIFY_EXPIRE_TIME} "⚠️ estado desconocido" "intentando grabar..."
    fi
    run_client "START_RECORDING"
fi
