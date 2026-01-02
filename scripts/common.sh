#!/bin/bash

# This file is part of voice2machine.
# Shared utilities for BASH scripts.

# Determine the absolute path to the project root
COMMON_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "${COMMON_SCRIPT_DIR}" )"

# XDG_RUNTIME_DIR compliance and secure runtime directory discovery
get_runtime_dir() {
    local app_name="v2m"
    local runtime_dir

    if [ -n "${XDG_RUNTIME_DIR:-}" ]; then
        runtime_dir="${XDG_RUNTIME_DIR}/${app_name}"
    else
        runtime_dir="/tmp/${app_name}_$(id -u)"
    fi

    # Security verification: If directory exists, it MUST be owned by the current user
    if [ -d "$runtime_dir" ]; then
        local owner_uid=$(stat -c '%u' "$runtime_dir")
        local current_uid=$(id -u)
        if [ "$owner_uid" != "$current_uid" ]; then
            echo "ERROR: Runtime directory $runtime_dir is owned by another user ($owner_uid)." >&2
            exit 1
        fi
    else
        mkdir -p "$runtime_dir" 2>/dev/null
        chmod 700 "$runtime_dir" 2>/dev/null
    fi

    echo "$runtime_dir"
}

# Source virtual environment if present
activate_venv() {
    local venv_path="${PROJECT_ROOT}/apps/backend/venv"
    if [ -f "${venv_path}/bin/activate" ]; then
        source "${venv_path}/bin/activate"
    elif [ -f "${PROJECT_ROOT}/venv/bin/activate" ]; then
        source "${PROJECT_ROOT}/venv/bin/activate"
    fi
}
