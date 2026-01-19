#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# notify.sh - Robust Notifications with Deduplication (SOTA 2026)
# ═══════════════════════════════════════════════════════════════════════════════

readonly V2M_TIMEOUT_MS=10000
readonly V2M_NOTIFY_ID_FILE="${XDG_RUNTIME_DIR:-/tmp}/v2m/notify_id"
readonly V2M_STACK_TAG="v2m_status"

# ─────────────────────────────────────────────────────────────────────────────
# NOTIFICATION ID MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

_v2m_get_id() {
    [[ -f "$V2M_NOTIFY_ID_FILE" ]] && cat "$V2M_NOTIFY_ID_FILE" || echo "0"
}

_v2m_set_id() {
    mkdir -p "$(dirname "$V2M_NOTIFY_ID_FILE")" 2>/dev/null
    echo "$1" > "$V2M_NOTIFY_ID_FILE"
}

# ─────────────────────────────────────────────────────────────────────────────
# NOTIFY VIA GDBUS (Synchronous to ensure ID capture)
# ─────────────────────────────────────────────────────────────────────────────

v2m_notify() {
    local urgency="${1:-normal}"
    local title="$2"
    local body="${3:-}"
    local icon="${4:-audio-input-microphone}"

    local current_id
    current_id=$(_v2m_get_id)

    # Map urgency
    local u_byte=1
    case "$urgency" in
        low) u_byte=0 ;;
        critical) u_byte=2 ;;
    esac

    # Construct GVariant hint dictionary
    # Includes BOTH 'replaces_id' logic (via ID param) AND 'x-dunst-stack-tag'
    local hints="{'urgency': <byte $u_byte>, 'x-dunst-stack-tag': <'$V2M_STACK_TAG'>, 'x-canonical-private-synchronous': <'$V2M_STACK_TAG'>}"

    # GDBUS Call
    local result
    result=$(gdbus call \
        --session \
        --dest=org.freedesktop.Notifications \
        --object-path=/org/freedesktop/Notifications \
        --method=org.freedesktop.Notifications.Notify \
        "Voice2Machine" \
        "$current_id" \
        "$icon" \
        "$title" \
        "$body" \
        '[]' \
        "$hints" \
        "$V2M_TIMEOUT_MS" 2>/dev/null)

    # Persist the returned ID for next replacement
    if [[ "$result" =~ \(uint32\ ([0-9]+) ]]; then
        _v2m_set_id "${BASH_REMATCH[1]}"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# SOUND FEEDBACK
# ─────────────────────────────────────────────────────────────────────────────

_v2m_sound() {
    command -v canberra-gtk-play &>/dev/null && \
        canberra-gtk-play -i "$1" &>/dev/null &
}

# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC HELPERS
# ─────────────────────────────────────────────────────────────────────────────

v2m_notify_recording() {
    v2m_notify "normal" "🔴 Grabando" "Habla ahora..." "audio-input-microphone"
    _v2m_sound "message-new-instant"
}

v2m_notify_processing() {
    v2m_notify "low" "⏳ Procesando" "Transcribiendo..." "audio-x-generic"
}

v2m_notify_success() {
    local text="${1:-Texto copiado}"
    [[ ${#text} -gt 100 ]] && text="${text:0:97}..."
    v2m_notify "low" "✅ Copiado" "$text" "edit-copy"
    _v2m_sound "complete"
}

v2m_notify_error() {
    v2m_notify "critical" "❌ Error" "${1:-Fallo}" "dialog-error"
    _v2m_sound "dialog-error"
}

v2m_notify_no_voice() {
    v2m_notify "normal" "🔇 Sin voz" "No se detectó audio" "audio-volume-muted"
}

v2m_notify_daemon_required() {
    v2m_notify "critical" "⚠️ Daemon" "Requiere v2m-daemon" "system-run"
}
