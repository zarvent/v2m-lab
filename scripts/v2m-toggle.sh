#!/bin/bash

# Este archivo es parte de voice2machine.
#
# voice2machine es software libre: puedes redistribuirlo y/o modificarlo
# bajo los términos de la Licencia Pública General GNU publicada por
# la Free Software Foundation, ya sea la versión 3 de la Licencia, o
# (a tu elección) cualquier versión posterior.
#
# voice2machine se distribuye con la esperanza de que sea útil,
# pero SIN NINGUNA GARANTÍA; ni siquiera la garantía implícita de
# COMERCIABILIDAD o IDONEIDAD PARA UN PROPÓSITO PARTICULAR. Consulta la
# Licencia Pública General GNU para más detalles.
#
# Deberías haber recibido una copia de la Licencia Pública General GNU
# junto con voice2machine. Si no, consulta <https://www.gnu.org/licenses/>.
#
# v2m-toggle.sh - Control de alternancia (Toggle) para grabación
#
# DESCRIPCIÓN
#   Script "Disparador" diseñado para asignarse a un atajo de teclado global.
#   Gestiona inteligentemente el ciclo de grabación:
#   - Si está inactivo -> Inicia grabación.
#   - Si está grabando -> Detiene, transcribe y pega.
#
# USO
#   ./scripts/v2m-toggle.sh
#
# FLUJO DE TRABAJO
#   1. Verifica conectividad con el demonio (auto-start si es necesario).
#   2. Consulta el estado real vía IPC (`GET_STATUS`).
#   3. Ejecuta la acción opuesta al estado actual.
#
# INTEGRACIÓN GNOME (Ejemplo)
#   Para asignar a Ctrl+Shift+Space:
#   ```bash
#   KEYBINDING_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/v2m/"
#   gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "['$KEYBINDING_PATH']"
#   gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KEYBINDING_PATH name 'V2M Toggle'
#   gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KEYBINDING_PATH command '$HOME/v2m/scripts/v2m-toggle.sh'
#   gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KEYBINDING_PATH binding '<Control><Shift>space'
#   ```
#
# DEPENDENCIAS
#   - `v2m-daemon.sh` (Servicio backend).
#   - `notify-send` (Feedback visual).
#   - Python 3 + venv (Cliente IPC).
#
# AUTOR
#   Equipo Voice2Machine
#

# --- CONFIGURACIÓN DE RUTAS ---
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$( dirname "${SCRIPT_DIR}" )/apps/backend"
NOTIFY_EXPIRE_TIME=3000

# --- CARGAR UTILIDADES COMUNES ---
source "${SCRIPT_DIR}/common.sh"
RUNTIME_DIR=$(get_runtime_dir)

# --- DEFINICIONES DE ENTORNO ---
VENV_PATH="${PROJECT_DIR}/venv"
MAIN_SCRIPT="${PROJECT_DIR}/src/v2m/main.py"
DAEMON_SCRIPT="${SCRIPT_DIR}/v2m-daemon.sh"

# --- FUNCIONES AUXILIARES ---

# Garantiza que el demonio esté corriendo antes de enviar comandos
ensure_daemon() {
    "${DAEMON_SCRIPT}" status > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        if command -v notify-send > /dev/null 2>&1; then
            notify-send --expire-time=${NOTIFY_EXPIRE_TIME} "🎙️ V2M" "Iniciando servicio en segundo plano..."
        fi

        "${DAEMON_SCRIPT}" start
        if [ $? -ne 0 ]; then
            if command -v notify-send > /dev/null 2>&1; then
                notify-send --expire-time=${NOTIFY_EXPIRE_TIME} "❌ Error V2M" "Fallo crítico al iniciar servicio."
            fi
            exit 1
        fi
        # Warmup: esperar inicialización del socket
        sleep 2
    fi
}

# Ejecuta un comando IPC usando el cliente Python
run_client() {
    local command=$1
    local payload="${2:-}"

    if [ ! -f "${VENV_PATH}/bin/activate" ]; then
        if command -v notify-send > /dev/null 2>&1; then
            notify-send --expire-time=${NOTIFY_EXPIRE_TIME} "❌ Error V2M" "Entorno virtual no encontrado en ${VENV_PATH}"
        fi
        exit 1
    fi

    source "${VENV_PATH}/bin/activate"
    export PYTHONPATH="${PROJECT_DIR}/src"

    # Invocación directa del módulo cliente para salida parseable
    python3 -m v2m.client "${command}" ${payload}
}

# --- LÓGICA PRINCIPAL ---

# 1. Asegurar backend activo
ensure_daemon

# 2. Consultar estado real al demonio (Single Source of Truth)
# Evitamos chequear archivos PID locales que pueden desincronizarse
STATUS_OUTPUT=$(run_client "GET_STATUS")

# 3. Máquina de estados simple
if [[ "$STATUS_OUTPUT" == *"STATUS: recording"* ]]; then
    # Estado: GRABANDO -> Acción: DETENER
    run_client "STOP_RECORDING"
elif [[ "$STATUS_OUTPUT" == *"STATUS: idle"* ]] || [[ "$STATUS_OUTPUT" == *"STATUS: paused"* ]]; then
    # Estado: INACTIVO/PAUSADO -> Acción: INICIAR
    run_client "START_RECORDING"
else
    # Estado: DESCONOCIDO/ERROR -> Acción: INTENTO DE RECUPERACIÓN
    if command -v notify-send > /dev/null 2>&1; then
        notify-send --expire-time=${NOTIFY_EXPIRE_TIME} "⚠️ Estado desconocido" "Forzando inicio de grabación..."
    fi
    run_client "START_RECORDING"
fi
