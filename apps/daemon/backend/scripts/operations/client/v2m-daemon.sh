#!/bin/bash

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
# Source common utils from ../utils/ (one level up from service/)
source "${SCRIPT_DIR}/../../shared/common.sh"

PROJECT_DIR="${BACKEND_DIR}"
VENV_PYTHON="${PROJECT_DIR}/venv/bin/python"

RUNTIME_DIR=$(get_runtime_dir)
LOG_FILE="${RUNTIME_DIR}/v2m_daemon.log"
PID_FILE="${RUNTIME_DIR}/v2m_daemon.pid"

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

    # 1. Try to find site-packages dir directly
    VENV_LIB_BASE="${PROJECT_DIR}/venv/lib"
    # Find the first python3.x dir (usually only one)
    PYTHON_LIB_DIR=$(find "$VENV_LIB_BASE" -maxdepth 1 -name "python3.*" -type d | head -n 1)

    if [ -n "$PYTHON_LIB_DIR" ]; then
        VENV_LIB="${PYTHON_LIB_DIR}/site-packages/nvidia"
        CUDA_PATHS=""

        if [ -d "${VENV_LIB}" ]; then
            for lib_path in "${VENV_LIB}"/*/lib; do
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
            # Force usage of discrete GPU (RTX 3060) instead of iGPU
            # "Performance is Design": Avoid overhead of device scanning
            export CUDA_VISIBLE_DEVICES=0
            echo "🔧 configuré las librerías de nvidia para usar la tarjeta gráfica (GPU 0)"
        else
            echo "⚠️  no encontré las librerías de nvidia"
        fi
    fi

    "${VENV_PYTHON}" -m v2m.main --daemon > "${LOG_FILE}" 2>&1 &

    DAEMON_PID=$!
    echo "${DAEMON_PID}" > "${PID_FILE}"

    # Wait for socket to be created (max ~30s for model loading)
    SOCKET_PATH="${RUNTIME_DIR}/v2m.sock"
    WAIT_TIMEOUT=60
    WAITED=0
    while [ ! -S "${SOCKET_PATH}" ] && [ "${WAITED}" -lt "${WAIT_TIMEOUT}" ]; do
        # Check if process died during startup
        if ! ps -p "${DAEMON_PID}" > /dev/null 2>&1; then
            echo "❌ el proceso murió durante el arranque"
            tail -20 "${LOG_FILE}"
            rm -f "${PID_FILE}"
            return 1
        fi
        sleep 0.5
        WAITED=$((WAITED + 1))
    done

    if [ ! -S "${SOCKET_PATH}" ]; then
        echo "⚠️  el socket no apareció después de ${WAIT_TIMEOUT}s"
    fi

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
