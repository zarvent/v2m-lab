#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# notify.sh - V2M Desktop Notifications (SOTA 2026)
# ═══════════════════════════════════════════════════════════════════════════════
#
# ZERO DUPLICATES: Uses gdbus with persistent notification ID
# AUTO-DISMISS: 10 seconds
# SINGLE NOTIFICATION: Only one v2m notification at any time
#
# ═══════════════════════════════════════════════════════════════════════════════

readonly V2M_TIMEOUT_MS=10000
readonly V2M_NOTIFY_ID_FILE="${XDG_RUNTIME_DIR:-/tmp}/v2m/notify_id"

# ─────────────────────────────────────────────────────────────────────────────
# GET/SET NOTIFICATION ID (persistent across calls)
# ─────────────────────────────────────────────────────────────────────────────

_v2m_get_notify_id() {
    [[ -f "$V2M_NOTIFY_ID_FILE" ]] && cat "$V2M_NOTIFY_ID_FILE" 2>/dev/null || echo "0"
}

_v2m_set_notify_id() {
    mkdir -p "$(dirname "$V2M_NOTIFY_ID_FILE")" 2>/dev/null
    echo "$1" > "$V2M_NOTIFY_ID_FILE"
}

# ─────────────────────────────────────────────────────────────────────────────
# CORE: Send notification via gdbus (ONLY method - no duplicates)
# ─────────────────────────────────────────────────────────────────────────────

v2m_notify() {
    local urgency="${1:-normal}"
    local title="$2"
    local body="${3:-}"
    local icon="${4:-audio-input-microphone}"

    local current_id
    current_id=$(_v2m_get_notify_id)

    # Map urgency to byte value
    local urgency_byte=1
    case "$urgency" in
        low) urgency_byte=0 ;;
        critical) urgency_byte=2 ;;
    esac

    # Send via gdbus - replaces_id parameter does the magic
    local result
    result=$(gdbus call \
        --session \
        --dest=org.freedesktop.Notifications \
        --object-path=/org/freedesktop/Notifications \
        --method=org.freedesktop.Notifications.Notify \
        "v2m" \
        "$current_id" \
        "$icon" \
        "$title" \
        "$body" \
        '[]' \
        "{'urgency': <byte $urgency_byte>}" \
        "$V2M_TIMEOUT_MS" 2>/dev/null)

    # Extract new ID from "(uint32 N,)" and persist
    if [[ "$result" =~ \(uint32\ ([0-9]+) ]]; then
        _v2m_set_notify_id "${BASH_REMATCH[1]}"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# CLOSE notification explicitly
# ─────────────────────────────────────────────────────────────────────────────

v2m_notify_close() {
    local current_id
    current_id=$(_v2m_get_notify_id)

    [[ "$current_id" -gt 0 ]] && gdbus call \
        --session \
        --dest=org.freedesktop.Notifications \
        --object-path=/org/freedesktop/Notifications \
        --method=org.freedesktop.Notifications.CloseNotification \
        "$current_id" &>/dev/null

    _v2m_set_notify_id "0"
}

# ─────────────────────────────────────────────────────────────────────────────
# SOUND (async, non-blocking)
# ─────────────────────────────────────────────────────────────────────────────

_v2m_sound() {
    command -v canberra-gtk-play &>/dev/null && \
        canberra-gtk-play -i "$1" &>/dev/null &
}

# ─────────────────────────────────────────────────────────────────────────────
# SEMANTIC HELPERS
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
    [[ ${#text} -gt 80 ]] && text="${text:0:77}..."
    v2m_notify "low" "✅ Copiado" "$text" "edit-copy"
    _v2m_sound "complete"
}

v2m_notify_error() {
    v2m_notify "critical" "❌ Error" "${1:-Error desconocido}" "dialog-error"
    _v2m_sound "dialog-error"
}

v2m_notify_no_voice() {
    v2m_notify "normal" "🔇 Sin voz" "Habla más fuerte" "audio-volume-muted"
}

v2m_notify_daemon_required() {
    v2m_notify "critical" "⚠️ Daemon" "Ejecuta start_daemon.sh" "system-run"
}
