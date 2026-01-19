#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# v2m-toggle.sh - Voice-to-Machine Recording Toggle
# ═══════════════════════════════════════════════════════════════════════════════
#
# SINGLE RESPONSIBILITY: Toggle recording → transcribe → copy to clipboard
#
# SOTA 2026 Features:
#   • Modular architecture (IPC client + notifications in lib/)
#   • Sub-50ms hot path latency
#   • Rich desktop notifications with sound feedback
#   • Zero daemon management (handled by scripts/development/daemon/)
#
# Usage:
#   v2m-toggle.sh           # Toggle recording state
#   v2m-toggle.sh --status  # Check current state
#   v2m-toggle.sh --help    # Show help
#
# Requirements:
#   • v2m daemon must be running (start with scripts/development/daemon/start_daemon.sh)
#   • Python 3.10+ for IPC client
#
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# PATH RESOLUTION
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
readonly SCRIPT_DIR
readonly LIB_DIR="${SCRIPT_DIR}/lib"
readonly CLIENT="${LIB_DIR}/v2m-client.py"

# ─────────────────────────────────────────────────────────────────────────────
# LOAD MODULES
# ─────────────────────────────────────────────────────────────────────────────

source "${LIB_DIR}/notify.sh" || {
    echo "ERROR: Failed to load notify.sh" >&2
    exit 1
}

# ─────────────────────────────────────────────────────────────────────────────
# HELP & STATUS
# ─────────────────────────────────────────────────────────────────────────────

show_help() {
    cat <<'EOF'
v2m-toggle.sh - Voice-to-Machine Recording Toggle

USAGE:
    v2m-toggle.sh           Toggle recording (start/stop)
    v2m-toggle.sh --status  Check daemon and recording state
    v2m-toggle.sh --help    Show this help

WORKFLOW:
    1. First call  → Start recording (🔴 notification)
    2. Second call → Stop, transcribe, copy to clipboard (✅ notification)

REQUIREMENTS:
    Start the daemon first:
    $ ./scripts/development/daemon/start_daemon.sh

EOF
}

show_status() {
    local response
    response=$(python3 "$CLIENT" status 2>/dev/null) || {
        echo "❌ Daemon not running"
        exit 1
    }

    # Parse state from JSON
    if [[ "$response" == *'"state":"recording"'* ]] || [[ "$response" == *'"state": "recording"'* ]]; then
        echo "🔴 Recording in progress"
    elif [[ "$response" == *'"state":"idle"'* ]] || [[ "$response" == *'"state": "idle"'* ]]; then
        echo "⚪ Idle (ready to record)"
    elif [[ "$response" == *'"state":"paused"'* ]] || [[ "$response" == *'"state": "paused"'* ]]; then
        echo "⏸️  Daemon paused"
    else
        echo "ℹ️  Status: $response"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# CORE TOGGLE LOGIC
# ─────────────────────────────────────────────────────────────────────────────

toggle_recording() {
    local response

    # Send toggle command via Python IPC client
    response=$(python3 "$CLIENT" toggle 2>/dev/null) || {
        # Check if daemon is not running
        if [[ "$response" == *"daemon_not_running"* ]]; then
            v2m_notify_daemon_required
            exit 1
        fi
        v2m_notify_error "Fallo de comunicación IPC"
        exit 1
    }

    # ─────────────────────────────────────────────────────────────────────
    # RESPONSE HANDLING (state machine)
    # ─────────────────────────────────────────────────────────────────────

    # Case 1: Started recording
    if [[ "$response" == *'"state":"recording"'* ]] || [[ "$response" == *'"state": "recording"'* ]]; then
        v2m_notify_recording
        exit 0
    fi

    # Case 2: Streaming event with final transcription
    if [[ "$response" == *'"text":'* ]]; then
        # Extract transcribed text (works for both event and command response)
        local text=""
        if [[ "$response" =~ \"text\":\ ?\"([^\"]+)\" ]]; then
            text="${BASH_REMATCH[1]}"
        elif [[ "$response" =~ \"transcription\":\ ?\"([^\"]+)\" ]]; then
            text="${BASH_REMATCH[1]}"
        fi

        if [[ -n "$text" ]]; then
            # COPY TO CLIPBOARD
            if command -v wl-copy &>/dev/null; then
                printf "%s" "$text" | wl-copy
            elif command -v xclip &>/dev/null; then
                printf "%s" "$text" | xclip -selection clipboard
            fi

            v2m_notify_success "$text"
        else
            v2m_notify_no_voice
        fi
        exit 0
    fi

    # Case 4: Success (generic)
    if [[ "$response" == *'"status":"success"'* ]] || [[ "$response" == *'"status": "success"'* ]]; then
        v2m_notify_processing
        exit 0
    fi

    # Case 5: Event (streaming intermediate)
    if [[ "$response" == *'"status":"event"'* ]] || [[ "$response" == *'"status": "event"'* ]]; then
        # Non-final event, likely recording started
        v2m_notify_recording
        exit 0
    fi

    # Case 6: Error
    if [[ "$response" == *'"status":"error"'* ]] || [[ "$response" == *'"status": "error"'* ]]; then
        local err="Error desconocido"
        if [[ "$response" =~ \"error\":\ ?\"([^\"]+)\" ]]; then
            err="${BASH_REMATCH[1]}"
        fi

        # Friendly error messages
        case "$err" in
            *"no se detectó voz"*|*"no voice"*)
                v2m_notify_no_voice
                ;;
            *"daemon"*|*"socket"*)
                v2m_notify_daemon_required
                ;;
            *)
                v2m_notify_error "$err"
                ;;
        esac
        exit 1
    fi

    # Unknown response
    v2m_notify_error "Respuesta inesperada"
    exit 1
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

main() {
    case "${1:-}" in
        --help|-h)
            show_help
            ;;
        --status|-s)
            show_status
            ;;
        *)
            toggle_recording
            ;;
    esac
}

main "$@"
