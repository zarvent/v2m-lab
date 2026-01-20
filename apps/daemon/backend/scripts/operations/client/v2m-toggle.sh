#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# v2m-toggle.sh - Voice-to-Machine Recording Toggle (SOTA 2026)
# ═══════════════════════════════════════════════════════════════════════════════
#
# SIMPLIFICADO: Usa curl para comunicarse con el servidor FastAPI.
# Un Junior puede entender este script en 30 segundos.
#
# Usage:
#   v2m-toggle.sh           # Toggle recording state
#   v2m-toggle.sh --status  # Check current state
#   v2m-toggle.sh --help    # Show help
#
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

readonly V2M_PORT="${V2M_PORT:-8765}"
readonly V2M_URL="http://127.0.0.1:${V2M_PORT}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
readonly SCRIPT_DIR
readonly LIB_DIR="${SCRIPT_DIR}/lib"

# ─────────────────────────────────────────────────────────────────────────────
# LOAD NOTIFICATION MODULE (optional)
# ─────────────────────────────────────────────────────────────────────────────

if [[ -f "${LIB_DIR}/notify.sh" ]]; then
    source "${LIB_DIR}/notify.sh"
else
    # Fallback: notificaciones simples si el módulo no existe
    v2m_notify_recording() { notify-send "🎙️ V2M" "Grabando..." 2>/dev/null || true; }
    v2m_notify_success() { notify-send "✅ V2M" "${1:-Copiado}" 2>/dev/null || true; }
    v2m_notify_error() { notify-send "❌ V2M" "${1:-Error}" 2>/dev/null || true; }
    v2m_notify_no_voice() { notify-send "🔇 V2M" "No se detectó voz" 2>/dev/null || true; }
    v2m_notify_daemon_required() { notify-send "⚠️ V2M" "Daemon no está corriendo" 2>/dev/null || true; }
fi

# ─────────────────────────────────────────────────────────────────────────────
# HELP & STATUS
# ─────────────────────────────────────────────────────────────────────────────

show_help() {
    cat <<EOF
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
    \$ ./scripts/operations/daemon/start_daemon.sh

ENVIRONMENT:
    V2M_PORT    Server port (default: 8765)

EOF
}

show_status() {
    local response
    response=$(curl -s "${V2M_URL}/status" 2>/dev/null) || {
        echo "❌ Daemon not running at ${V2M_URL}"
        echo "   Start with: ./scripts/operations/daemon/start_daemon.sh"
        exit 1
    }

    # Parse state from JSON using grep/sed (no jq dependency)
    if [[ "$response" == *'"recording":true'* ]] || [[ "$response" == *'"recording": true'* ]]; then
        echo "🔴 Recording in progress"
    else
        echo "⚪ Idle (ready to record)"
    fi

    # Show model status
    if [[ "$response" == *'"model_loaded":true'* ]] || [[ "$response" == *'"model_loaded": true'* ]]; then
        echo "✅ Whisper model loaded"
    else
        echo "⏳ Whisper model not loaded (will load on first use)"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# CORE TOGGLE LOGIC
# ─────────────────────────────────────────────────────────────────────────────

toggle_recording() {
    local response
    local http_code

    # Send toggle command via HTTP POST
    response=$(curl -s -w "\n%{http_code}" -X POST "${V2M_URL}/toggle" 2>/dev/null) || {
        v2m_notify_daemon_required
        echo "❌ Cannot connect to ${V2M_URL}"
        echo "   Start daemon: ./scripts/operations/daemon/start_daemon.sh"
        exit 1
    }

    # Extract HTTP code (last line) and body
    http_code=$(echo "$response" | tail -n1)
    response=$(echo "$response" | sed '$d')

    # Check HTTP status
    if [[ "$http_code" != "200" ]]; then
        v2m_notify_error "HTTP Error: $http_code"
        exit 1
    fi

    # ─────────────────────────────────────────────────────────────────────
    # RESPONSE HANDLING
    # ─────────────────────────────────────────────────────────────────────

    # Case 1: Started recording
    if [[ "$response" == *'"status":"recording"'* ]] || [[ "$response" == *'"status": "recording"'* ]]; then
        v2m_notify_recording
        echo "🎙️ Recording started"
        exit 0
    fi

    # Case 2: Stopped with transcription
    if [[ "$response" == *'"status":"idle"'* ]] || [[ "$response" == *'"status": "idle"'* ]]; then
        # Extract text if present
        local text=""
        if [[ "$response" =~ \"text\":\ ?\"([^\"]+)\" ]]; then
            text="${BASH_REMATCH[1]}"
        fi

        if [[ -n "$text" && "$text" != "null" ]]; then
            v2m_notify_success "$text"
            echo "✅ Transcribed and copied: ${text:0:50}..."
        else
            v2m_notify_no_voice
            echo "🔇 No voice detected"
        fi
        exit 0
    fi

    # Case 3: Error
    if [[ "$response" == *'"status":"error"'* ]] || [[ "$response" == *'"status": "error"'* ]]; then
        local err="Unknown error"
        if [[ "$response" =~ \"message\":\ ?\"([^\"]+)\" ]]; then
            err="${BASH_REMATCH[1]}"
        fi
        v2m_notify_error "$err"
        echo "❌ Error: $err"
        exit 1
    fi

    # Unknown response - show it
    echo "Response: $response"
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
