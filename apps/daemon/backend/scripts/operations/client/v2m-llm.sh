#!/bin/bash

#--------------------------------------------------------------------------------
#
# v2m-llm.sh - Script para procesar texto del portapapeles con LLM
#
# DESCRIPCIÓN:
#   Este script lee el contenido del portapapeles y lo envía al daemon
#   de V2M para procesamiento con el LLM configurado (local o Gemini).
#   El backend se determina automáticamente desde config.toml.
#
# USO:
#   ./scripts/v2m-llm.sh
#
# FLUJO DE TRABAJO:
#   1. Lee el contenido del portapapeles con xclip
#   2. Envía el comando PROCESS_TEXT al daemon via IPC
#   3. El daemon procesa con el LLM según config.toml [llm.backend]
#   4. El resultado refinado se copia automáticamente al portapapeles
#
# BACKEND LLM:
#   - Si config.toml tiene [llm] backend = "local" → usa Qwen local
#   - Si config.toml tiene [llm] backend = "gemini" → usa Gemini API
#
# DEPENDENCIAS:
#   - xclip: Para acceso al portapapeles
#   - notify-send: Para notificaciones de escritorio
#   - v2m daemon: Debe estar corriendo (systemctl start v2m-daemon)
#
# INTEGRACIÓN CON ATAJOS DE TECLADO:
#   GNOME (gsettings):
#     gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/ \
#       name 'V2M Process Text'
#     gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/ \
#       command "$HOME/v2m/scripts/v2m-llm.sh"
#     gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/ \
#       binding '<Super><Shift>p'
#
#   KDE Plasma:
#     Configuración del Sistema → Atajos → Atajos personalizados → Editar → Nuevo → Comando Global de Atajo
#
# NOTAS:
#   - Requiere sesión X11 activa para xclip
#   - El daemon debe estar corriendo antes de ejecutar este script
#   - Muestra error si el portapapeles está vacío
#
# AUTOR:
#   Voice2Machine Team
#
# DESDE:
#   v2.0.0
#

set -euo pipefail

# --- Configuración ---
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "${SCRIPT_DIR}/../../shared/common.sh"

RUNTIME_DIR=$(get_runtime_dir)
PROJECT_DIR="${BACKEND_DIR}"
VENV_PATH="${BACKEND_DIR}/venv"
NOTIFY_EXPIRE_TIME=3000

# --- Rutas Derivadas ---
MAIN_SCRIPT="${PROJECT_DIR}/src/v2m/main.py"

# --- Verificaciones Previas ---
if ! command -v xclip &> /dev/null; then
    notify-send --expire-time=${NOTIFY_EXPIRE_TIME} "❌ Error de Dependencia" "xclip no está instalado. Instálalo con: sudo apt install xclip"
    echo "Error: xclip is not installed." >&2
    exit 1
fi

if [ ! -f "${MAIN_SCRIPT}" ]; then
     notify-send --expire-time=${NOTIFY_EXPIRE_TIME} "❌ Error Crítico" "No se encontró el script principal en: ${MAIN_SCRIPT}"
     echo "Error: Main script not found at ${MAIN_SCRIPT}" >&2
     exit 1
fi

# --- Función para notificaciones con auto-dismiss via DBUS ---
# Replica el comportamiento de LinuxNotificationService de Python
# Resuelve el bug de Unity/GNOME que ignora --expire-time de notify-send
auto_dismiss_notify() {
    local title="$1"
    local message="$2"
    local expire_time="${3:-3000}"  # default 3 segundos

    # Enviar notificación via DBUS y capturar el ID
    local notify_output
    notify_output=$(gdbus call --session \
        --dest org.freedesktop.Notifications \
        --object-path /org/freedesktop/Notifications \
        --method org.freedesktop.Notifications.Notify \
        "v2m" 0 "" "$title" "$message" "[]" "{}" "$expire_time" 2>/dev/null)

    # Extraer notification_id de salida: "(uint32 123,)"
    if [[ $notify_output =~ uint32\ ([0-9]+) ]]; then
        local notification_id="${BASH_REMATCH[1]}"

        # Programar cierre automático en background
        (
            sleep $(awk "BEGIN {print $expire_time/1000}")
            gdbus call --session \
                --dest org.freedesktop.Notifications \
                --object-path /org/freedesktop/Notifications \
                --method org.freedesktop.Notifications.CloseNotification \
                "$notification_id" &>/dev/null
        ) &
    else
        # Fallback a notify-send si DBUS falla
        notify-send --expire-time="$expire_time" "$title" "$message" 2>/dev/null || true
    fi
}

# --- Función para enviar comando al daemon ---
send_to_daemon() {
    local text_to_process="$1"

    if [ ! -f "${VENV_PATH}/bin/activate" ]; then
        notify-send --expire-time=${NOTIFY_EXPIRE_TIME} "❌ Error de V2M" "Entorno virtual no encontrado en ${VENV_PATH}"
        echo "Error: Virtual environment not found at ${VENV_PATH}" >&2
        exit 1
    fi

    # Activar entorno y enviar comando PROCESS_TEXT al daemon
    # Usamos subshell para aislar variables de entorno
    (
        activate_venv
        export PYTHONPATH="${PROJECT_ROOT}/apps/backend/src"

        # Usar el cliente IPC para comunicarse con el daemon
        if ! python3 "${PROJECT_ROOT}/apps/backend/src/v2m/main.py" PROCESS_TEXT "${text_to_process}"; then
            echo "Error executing python script" >&2
            exit 1
        fi
    )
}

# --- Lógica Principal ---
# Leer contenido del portapapeles
# '|| true' previene fallo si xclip devuelve error (ej. selección vacía en algunos casos)
clipboard_content=$(xclip -o -selection clipboard 2>/dev/null || true)

if [ -n "${clipboard_content}" ]; then
    # Notificar inicio del procesamiento (se auto-elimina en 1 segundo)
    auto_dismiss_notify "🧠 Procesando..." "Refinando texto con LLM..." 1000

    # Enviar al daemon para procesamiento
    if ! send_to_daemon "${clipboard_content}"; then
        notify-send --expire-time=${NOTIFY_EXPIRE_TIME} "❌ Error" "Falló el procesamiento del texto."
        exit 1
    fi
else
    notify-send --expire-time=${NOTIFY_EXPIRE_TIME} "⚠️ Portapapeles vacío" "Copia texto antes de usar este atajo."
    exit 1
fi
