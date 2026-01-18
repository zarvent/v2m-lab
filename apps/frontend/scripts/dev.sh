#!/bin/bash
# apps/frontend/scripts/dev.sh - V2M Super Dev Entrypoint
# 2026 SOTA Workflow Optimization

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
FRONTEND_DIR="$( cd "${SCRIPT_DIR}/.." &> /dev/null && pwd )"
REPO_ROOT="$( cd "${FRONTEND_DIR}/.." &> /dev/null && pwd )"
BACKEND_DIR="${REPO_ROOT}/apps/backend"
BACKEND_DAEMON_SCRIPT="${BACKEND_DIR}/scripts/service/v2m-daemon.sh"

echo "🚀 Starting V2M Monorepo Dev Environment..."

# 1. Ensure Backend Daemon is running
if [[ -f "$BACKEND_DAEMON_SCRIPT" ]]; then
    echo "🎙️ Checking backend daemon..."
    if ! bash "$BACKEND_DAEMON_SCRIPT" status &>/dev/null; then
        echo "   -> Starting backend daemon..."
        bash "$BACKEND_DAEMON_SCRIPT" start
    else
        echo "   -> Backend already running."
    fi
else
    echo "⚠️ Warning: Backend daemon script not found at $BACKEND_DAEMON_SCRIPT"
fi

# 2. Run Frontend in Dev Mode (Tauri)
echo "🖼️ Starting Tauri frontend..."
cd "$FRONTEND_DIR"

if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm not found."
    exit 1
fi

# Use pnpm or npm depending on what's available/used
if [[ -f "pnpm-lock.yaml" ]] && command -v pnpm &> /dev/null; then
    exec pnpm tauri dev
else
    exec npm run tauri dev
fi
