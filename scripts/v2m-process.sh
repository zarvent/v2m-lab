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
PROJECT_DIR="$( dirname "${SCRIPT_DIR}" )/apps/backend"
NOTIFY_EXPIRE_TIME=3000

# --- RUTAS DERIVADAS ---
VENV_PATH="${PROJECT_DIR}/venv"
MAIN_SCRIPT="${PROJECT_DIR}/src/v2m/main.py"

# --- FUNCIÓN PRINCIPAL ---
run_orchestrator() {
    local text_to_process=$1

    if [ ! -f "${VENV_PATH}/bin/activate" ]; then
        notify-send --expire-time=${NOTIFY_EXPIRE_TIME} "❌ error de v2m" "no encontré el entorno virtual en ${VENV_PATH}"
        exit 1
    fi

    source "${VENV_PATH}/bin/activate"
    export PYTHONPATH="${PROJECT_DIR}/src"
    echo "${text_to_process}" | python3 "${MAIN_SCRIPT}" "process"
}

# --- LÓGICA PRINCIPAL ---
clipboard_content=$(xclip -o -selection clipboard)
if [ -n "${clipboard_content}" ]; then
    run_orchestrator "${clipboard_content}"
else
    notify-send --expire-time=${NOTIFY_EXPIRE_TIME} "❌ error" "el portapapeles está vacío"
    exit 1
fi
