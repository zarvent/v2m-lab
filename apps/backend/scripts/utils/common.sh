#!/bin/bash

# Shared utilities for BASH scripts.
# State-of-the-Art 2026 Scripting Standards

# 1. Path Discovery (Nested Monorepo Support)
# current dir: apps/backend/scripts/utils
COMMON_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Repo Root: /home/zarvent/developer/v2m-lab (3 levels up from scripts/utils)
REPO_ROOT="$( cd "${COMMON_SCRIPT_DIR}/../../.." &> /dev/null && pwd )"

# Backend Dir: /home/zarvent/developer/v2m-lab/apps/backend (2 levels up from scripts/utils)
BACKEND_DIR="$( cd "${COMMON_SCRIPT_DIR}/../.." &> /dev/null && pwd )"

# Compatibility aliases
PROJECT_ROOT="${REPO_ROOT}"
PROJECT_DIR="${BACKEND_DIR}"

# 2. XDG_RUNTIME_DIR compliance and secure runtime directory discovery
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
        if [ ! -O "$runtime_dir" ]; then
            echo "ERROR: Runtime directory $runtime_dir is owned by another user." >&2
            exit 1
        fi
    else
        mkdir -p "$runtime_dir" 2>/dev/null
        chmod 700 "$runtime_dir" 2>/dev/null
    fi

    echo "$runtime_dir"
}

# 3. Virtual Environment Management
activate_venv() {
    local venv_path="${BACKEND_DIR}/venv"
    if [ -f "${venv_path}/bin/activate" ]; then
        source "${venv_path}/bin/activate"
    elif [ -f "${REPO_ROOT}/venv/bin/activate" ]; then
        # Fallback to root venv if backend one is missing
        source "${REPO_ROOT}/venv/bin/activate"
    else
        return 1
    fi
}
