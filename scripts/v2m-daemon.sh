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
# v2m-daemon.sh - Gestor de servicios del demonio Voice2Machine
#
# DESCRIPCIÓN
#   Script de control principal para el demonio backend.
#   Proporciona una interfaz unificada para el ciclo de vida del servicio:
#   arranque, parada, reinicio y monitoreo de estado.
#
# USO
#   ./scripts/v2m-daemon.sh [start|stop|restart|status|logs]
#
# COMANDOS
#   start    - Inicia el demonio en segundo plano (background).
#   stop     - Envía señal de terminación (SIGTERM) para un cierre limpio.
#   restart  - Ciclo completo de parada y arranque.
#   status   - Verifica si el proceso está activo y responde a PING.
#   logs     - Muestra la cola de registros del servicio.
#
# ARCHIVOS
#   XDG_RUNTIME_DIR/v2m/v2m_daemon.log  - Salida estándar y de error.
#   XDG_RUNTIME_DIR/v2m/v2m_daemon.pid  - ID del proceso para control.
#
# VARIABLES DE ENTORNO
#   LD_LIBRARY_PATH - Se auto-configura para inyectar librerías CUDA/cuDNN.
#   PYTHONPATH      - Se ajusta para incluir el código fuente del backend.
#
# DEPENDENCIAS
#   - Python 3.12+ (en entorno virtual ./venv).
#   - Librerías NVIDIA en el venv (opcional, para aceleración GPU).
#
# AUTOR
#   Equipo Voice2Machine
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$( dirname "${SCRIPT_DIR}" )/apps/backend"
VENV_PYTHON="${PROJECT_DIR}/venv/bin/python"

# --- CARGAR UTILIDADES COMUNES ---
source "${SCRIPT_DIR}/common.sh"
RUNTIME_DIR=$(get_runtime_dir)
LOG_FILE="${RUNTIME_DIR}/v2m_daemon.log"
PID_FILE="${RUNTIME_DIR}/v2m_daemon.pid"

start_daemon() {
    if [ -f "${PID_FILE}" ]; then
        PID=$(cat "${PID_FILE}")
        if ps -p "${PID}" > /dev/null 2>&1; then
            echo "❌ El servicio ya está corriendo (PID: ${PID})"
            return 1
        else
            echo "⚠️  Archivo PID huérfano detectado. Limpiando..."
            rm -f "${PID_FILE}"
        fi
    fi

    echo "🚀 Iniciando servicio Voice2Machine..."

    cd "${PROJECT_DIR}"
    export PYTHONPATH="${PROJECT_DIR}/src"

    # --- Configuración Dinámica de LD_LIBRARY_PATH (CUDA/cuDNN) ---
    # Whisper requiere acceso a las librerías compartidas de NVIDIA.
    # Si están instaladas en el venv (pip install nvidia-*), las agregamos al path.
    PYTHON_VERSION=$("${VENV_PYTHON}" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "3.12")
    VENV_LIB="${PROJECT_DIR}/venv/lib/python${PYTHON_VERSION}/site-packages/nvidia"
    CUDA_PATHS=""

    if [ -d "${VENV_LIB}" ]; then
        # Lista de paquetes NVIDIA requeridos para inferencia
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

    # Inyección de rutas de librerías
    if [ -n "${CUDA_PATHS}" ]; then
        export LD_LIBRARY_PATH="${CUDA_PATHS}:${LD_LIBRARY_PATH:-}"
        echo "🔧 Entorno configurado para aceleración GPU (NVIDIA)"
    else
        echo "⚠️  Librerías NVIDIA no detectadas. Se usará CPU (más lento)."
    fi

    # Ejecución del módulo principal en modo demonio
    "${VENV_PYTHON}" -m v2m.main --daemon > "${LOG_FILE}" 2>&1 &

    DAEMON_PID=$!
    echo "${DAEMON_PID}" > "${PID_FILE}"

    # Espera breve para verificar arranque exitoso
    sleep 2

    if ps -p "${DAEMON_PID}" > /dev/null 2>&1; then
        echo "✅ Servicio iniciado correctamente (PID: ${DAEMON_PID})"
        echo "📋 Registros disponibles en: ${LOG_FILE}"
    else
        echo "❌ Fallo al iniciar el servicio. Revisando últimos logs:"
        tail -20 "${LOG_FILE}"
        rm -f "${PID_FILE}"
        return 1
    fi
}

stop_daemon() {
    if [ ! -f "${PID_FILE}" ]; then
        echo "⚠️  Archivo PID no encontrado. Buscando proceso por nombre..."
        PID=$(ps aux | grep "python.*v2m.main --daemon" | grep -v grep | awk '{print $2}' | head -1)
        if [ -z "${PID}" ]; then
            echo "❌ El servicio no parece estar corriendo."
            return 1
        fi
    else
        PID=$(cat "${PID_FILE}")
    fi

    echo "🛑 Deteniendo servicio (PID: ${PID})..."
    kill -TERM "${PID}" 2>/dev/null

    # Espera activa (polling) para terminación limpia
    for i in {1..10}; do
        if ! ps -p "${PID}" > /dev/null 2>&1; then
            echo "✅ Servicio detenido correctamente"
            rm -f "${PID_FILE}"
            return 0
        fi
        sleep 0.5
    done

    # Terminación forzada si el proceso se cuelga
    echo "⚠️  El servicio no respondió a SIGTERM. Forzando cierre (SIGKILL)..."
    kill -9 "${PID}" 2>/dev/null
    rm -f "${PID_FILE}"
    echo "✅ Servicio detenido forzadamente"
}

status_daemon() {
    if [ -f "${PID_FILE}" ]; then
        PID=$(cat "${PID_FILE}")
        if ps -p "${PID}" > /dev/null 2>&1; then
            echo "✅ El servicio está ACTIVO (PID: ${PID})"

            # Información detallada del proceso
            ps -p "${PID}" -o pid,ppid,user,%cpu,%mem,etime,cmd

            # Verificación de conectividad IPC (Ping)
            echo ""
            echo "🔍 Verificando conectividad IPC..."
            cd "${PROJECT_DIR}"
            export PYTHONPATH="${PROJECT_DIR}/src"
            PING_RESULT=$("${VENV_PYTHON}" -c "import asyncio; from v2m.client import send_command; print(asyncio.run(send_command('PING')))" 2>&1)

            if echo "${PING_RESULT}" | grep -q "PONG"; then
                echo "✅ El servicio responde a comandos IPC."
            else
                echo "⚠️  ADVERTENCIA: El proceso existe pero no responde (Posible bloqueo)."
                echo "Respuesta: ${PING_RESULT}"
            fi

            return 0
        else
            echo "❌ Archivo PID existe pero el proceso murió."
            rm -f "${PID_FILE}"
            return 1
        fi
    else
        echo "❌ El servicio está DETENIDO."
        return 1
    fi
}

show_logs() {
    if [ ! -f "${LOG_FILE}" ]; then
        echo "❌ No se encontró el archivo de registros: ${LOG_FILE}"
        return 1
    fi

    if command -v less > /dev/null 2>&1; then
        less +G "${LOG_FILE}"
    else
        tail -50 "${LOG_FILE}"
    fi
}

# --- PUNTO DE ENTRADA ---
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
        echo "Uso: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
