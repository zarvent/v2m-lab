#!/bin/bash
# scripts/utils/common.sh

# Función para obtener el directorio de ejecución seguro (XDG_RUNTIME_DIR)
# Compatible con la lógica de python v2m.utils.paths
get_runtime_dir() {
    if [ -n "$XDG_RUNTIME_DIR" ]; then
        echo "$XDG_RUNTIME_DIR/v2m"
    else
        echo "/tmp/v2m_$(id -u)"
    fi
}

# Función de log simple
log_info() {
    echo "[INFO] $1" >&2
}

log_error() {
    echo "[ERROR] $1" >&2
}
