#!/bin/bash
# notify.sh - Rich Desktop Notifications for V2M
# SOTA 2026: dunstify support, replaceable notifications, sound feedback

# Notification ID for replacement (dunstify only)
readonly V2M_NOTIFY_ID=91827

# ─────────────────────────────────────────────────────────────────────────────
# CORE NOTIFICATION FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

v2m_notify() {
    local urgency="${1:-normal}"  # low, normal, critical
    local title="$2"
    local body="${3:-}"
    local icon="${4:-audio-input-microphone}"

    # Try dunstify first (supports replace, actions)
    if command -v dunstify &>/dev/null; then
        dunstify \
            --replace="$V2M_NOTIFY_ID" \
            --urgency="$urgency" \
            --icon="$icon" \
            --appname="v2m" \
            --timeout=2000 \
            "$title" "$body" &
        return 0
    fi

    # Fallback to notify-send
    if command -v notify-send &>/dev/null; then
        notify-send \
            --urgency="$urgency" \
            --icon="$icon" \
            --app-name="v2m" \
            --expire-time=2000 \
            "$title" "$body" &
        return 0
    fi

    # No notification system - silent fail
    return 1
}

# ─────────────────────────────────────────────────────────────────────────────
# SEMANTIC NOTIFICATION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

v2m_notify_recording() {
    v2m_notify "normal" "🔴 Grabando" "Habla ahora..." "audio-input-microphone"
    # Optional sound feedback
    command -v canberra-gtk-play &>/dev/null && \
        canberra-gtk-play -i message-new-instant &>/dev/null &
}

v2m_notify_processing() {
    v2m_notify "low" "⏳ Procesando" "Transcribiendo audio..." "audio-x-generic"
}

v2m_notify_success() {
    local text="${1:-Texto copiado}"
    # Truncate long text for notification
    [[ ${#text} -gt 80 ]] && text="${text:0:77}..."
    v2m_notify "low" "✅ Copiado" "$text" "edit-copy"
    command -v canberra-gtk-play &>/dev/null && \
        canberra-gtk-play -i complete &>/dev/null &
}

v2m_notify_error() {
    local msg="${1:-Error desconocido}"
    v2m_notify "critical" "❌ Error" "$msg" "dialog-error"
    command -v canberra-gtk-play &>/dev/null && \
        canberra-gtk-play -i dialog-error &>/dev/null &
}

v2m_notify_no_voice() {
    v2m_notify "normal" "🔇 Sin voz" "No se detectó audio" "audio-volume-muted"
}

v2m_notify_daemon_required() {
    v2m_notify "critical" "⚠️ Daemon requerido" "Ejecuta: v2m-daemon.sh start" "system-run"
}
