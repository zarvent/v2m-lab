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
# v2m-daemon.sh - script para gestionar el servicio voice2machine
#
# DESCRIPCIÓN
#   este script te permite controlar el servicio de v2m que se ejecuta
#   en segundo plano puedes iniciarlo detenerlo reiniciarlo y
#   verificar si todo está funcionando bien
#
# USO
#   ./scripts/v2m-daemon.sh [start|stop|restart|status|logs]
#
# COMANDOS
#   start    - inicia el servicio en segundo plano
#   stop     - detiene el servicio de forma segura
#   restart  - reinicia el servicio primero lo detiene y luego lo inicia
#   status   - te muestra el estado actual y prueba la conexión
#   logs     - te muestra los registros del servicio
#
# ARCHIVOS
#   /tmp/v2m_daemon.log  - archivo donde se guardan los registros
#   /tmp/v2m_daemon.pid  - archivo que guarda el identificador del proceso
#
# VARIABLES DE ENTORNO
#   LD_LIBRARY_PATH - se configura sola para que funcione con cuda
#   PYTHONPATH      - se configura para incluir el código fuente
#
# DEPENDENCIAS
#   - python 3.12+ con entorno virtual en ./venv
#   - librerías de nvidia en el entorno virtual opcional para gpu
#
# EJEMPLOS
#   # iniciar el servicio
#   ./scripts/v2m-daemon.sh start
#
#   # ver cómo está todo y probar la conexión
#   ./scripts/v2m-daemon.sh status
#
#   # ver qué está pasando en tiempo real
#   ./scripts/v2m-daemon.sh logs
#
# NOTAS
#   - el servicio usa un socket unix para comunicarse
#   - los registros se limpian solos automáticamente
#   - si no tienes tarjeta gráfica nvidia usará el procesador automáticamente
#
# AUTOR
#   equipo voice2machine
#
# DESDE
#   v1.0.0
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$( dirname "${SCRIPT_DIR}" )/apps/backend"
VENV_PYTHON="${PROJECT_DIR}/venv/bin/python"
LOG_FILE="/tmp/v2m_daemon.log"
PID_FILE="/tmp/v2m_daemon.pid"

start_daemon() {
    if [ -f "${PID_FILE}" ]; then
        PID=$(cat "${PID_FILE}")
        if ps -p "${PID}" > /dev/null 2>&1; then
            echo "❌ el servicio ya está corriendo (pid: ${PID})"
            return 1
        else
            echo "⚠️  encontré un archivo pid pero el proceso no existe así que voy a limpiarlo"
            rm -f "${PID_FILE}"
        fi
    fi

    echo "🚀 iniciando el servicio de v2m..."

    cd "${PROJECT_DIR}"
    export PYTHONPATH="${PROJECT_DIR}/src"

    # --- configurar ld_library_path para cuda y cudnn ---
    # buscamos las librerías de nvidia en el entorno virtual que son
    # necesarias para que whisper funcione con la tarjeta gráfica
    VENV_LIB="${PROJECT_DIR}/venv/lib/python3.12/site-packages/nvidia"
    CUDA_PATHS=""

    if [ -d "${VENV_LIB}" ]; then
        # paquetes de nvidia que contienen las librerías necesarias
        NVIDIA_PACKAGES=(
            "cuda_runtime"
            "cudnn"
            "cublas"
            "cufft"
            "curand"
            "cusolver"
            "cusparse"
            "nvjitlink"
        )

        for pkg in "${NVIDIA_PACKAGES[@]}"; do
            lib_path="${VENV_LIB}/${pkg}/lib"
            if [ -d "$lib_path" ]; then
                if [ -z "${CUDA_PATHS}" ]; then
                    CUDA_PATHS="$lib_path"
                else
                    CUDA_PATHS="${CUDA_PATHS}:${lib_path}"
                fi
            fi
        done
    fi

    # agregamos las rutas a la variable de entorno
    if [ -n "${CUDA_PATHS}" ]; then
        export LD_LIBRARY_PATH="${CUDA_PATHS}:${LD_LIBRARY_PATH:-}"
        echo "🔧 configuré las librerías de nvidia para usar la tarjeta gráfica"
    else
        echo "⚠️  no encontré las librerías de nvidia así que es posible que no pueda usar la tarjeta gráfica"
    fi

    "${VENV_PYTHON}" -m v2m.main --daemon > "${LOG_FILE}" 2>&1 &

    DAEMON_PID=$!
    echo "${DAEMON_PID}" > "${PID_FILE}"

    # esperamos un momento para asegurarnos de que arrancó bien
    sleep 2

    if ps -p "${DAEMON_PID}" > /dev/null 2>&1; then
        echo "✅ el servicio arrancó correctamente (pid: ${DAEMON_PID})"
        echo "📋 puedes ver los registros en: ${LOG_FILE}"
    else
        echo "❌ hubo un problema al iniciar el servicio revisa los registros"
        tail -20 "${LOG_FILE}"
        rm -f "${PID_FILE}"
        return 1
    fi
}

stop_daemon() {
    if [ ! -f "${PID_FILE}" ]; then
        echo "⚠️  no encontré el archivo pid así que buscaré el proceso manualmente"
        PID=$(ps aux | grep "python.*v2m.main --daemon" | grep -v grep | awk '{print $2}' | head -1)
        if [ -z "${PID}" ]; then
            echo "❌ el servicio no está corriendo"
            return 1
        fi
    else
        PID=$(cat "${PID_FILE}")
    fi

    echo "🛑 deteniendo el servicio (pid: ${PID})..."
    kill -TERM "${PID}" 2>/dev/null

    # esperamos hasta 5 segundos para que termine ordenadamente
    for i in {1..10}; do
        if ! ps -p "${PID}" > /dev/null 2>&1; then
            echo "✅ servicio detenido correctamente"
            rm -f "${PID_FILE}"
            return 0
        fi
        sleep 0.5
    done

    # si no terminó lo forzamos
    echo "⚠️  el servicio no respondió así que lo voy a forzar"
    kill -9 "${PID}" 2>/dev/null
    rm -f "${PID_FILE}"
    echo "✅ servicio detenido forzadamente"
}

status_daemon() {
    if [ -f "${PID_FILE}" ]; then
        PID=$(cat "${PID_FILE}")
        if ps -p "${PID}" > /dev/null 2>&1; then
            echo "✅ el servicio está corriendo (pid: ${PID})"

            # mostramos información del proceso
            ps -p "${PID}" -o pid,ppid,user,%cpu,%mem,etime,cmd

            # prueba de conexión
            echo ""
            echo "🔍 probando la conexión..."
            cd "${PROJECT_DIR}"
            export PYTHONPATH="${PROJECT_DIR}/src"
            PING_RESULT=$("${VENV_PYTHON}" -c "import asyncio; from v2m.client import send_command; print(asyncio.run(send_command('PING')))" 2>&1)

            if echo "${PING_RESULT}" | grep -q "PONG"; then
                echo "✅ el servicio responde correctamente"
            else
                echo "⚠️  el servicio no responde al ping"
                echo "${PING_RESULT}"
            fi

            return 0
        else
            echo "❌ existe el archivo pid pero el proceso no está corriendo"
            rm -f "${PID_FILE}"
            return 1
        fi
    else
        echo "❌ el servicio no está corriendo no encontré el archivo pid"
        return 1
    fi
}

show_logs() {
    if [ ! -f "${LOG_FILE}" ]; then
        echo "❌ no encontré el archivo de registros: ${LOG_FILE}"
        return 1
    fi

    if command -v less > /dev/null 2>&1; then
        less +G "${LOG_FILE}"
    else
        tail -50 "${LOG_FILE}"
    fi
}

# --- PRINCIPAL ---
case "${1:-}" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        stop_daemon
        sleep 1
        start_daemon
        ;;
    status)
        status_daemon
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "uso: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "COMANDOS:"
        echo "  start    - inicia el servicio"
        echo "  stop     - detiene el servicio"
        echo "  restart  - reinicia el servicio"
        echo "  status   - muestra el estado del servicio"
        echo "  logs     - muestra los registros del servicio"
        exit 1
        ;;
esac
