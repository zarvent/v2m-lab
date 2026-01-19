#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# notify.sh - SOTA 2026 Desktop Notifications for V2M
# ═══════════════════════════════════════════════════════════════════════════════
#
# Features:
#   • Notification replacement (no duplicates) via dunstify or gdbus
#   • 10-second auto-dismiss
#   • Sound feedback (optional)
#   • State-based icons
#   • Graceful fallbacks
#
# ═══════════════════════════════════════════════════════════════════════════════

# Unique notification ID for replacement (consistent across calls)
readonly V2M_NOTIFY_ID=918273645

# Default timeout in milliseconds (10 seconds)
readonly V2M_NOTIFY_TIMEOUT=10000

# ─────────────────────────────────────────────────────────────────────────────
# NOTIFICATION ENGINE DETECTION
# ─────────────────────────────────────────────────────────────────────────────

# Detect best available notification method (cached for performance)
_v2m_detect_notifier() {
    if [[ -n "${_V2M_NOTIFIER:-}" ]]; then
        echo "$_V2M_NOTIFIER"
        return
    fi

    if command -v dunstify &>/dev/null; then
        _V2M_NOTIFIER="dunstify"
    elif command -v gdbus &>/dev/null; then
        _V2M_NOTIFIER="gdbus"
    elif command -v notify-send &>/dev/null; then
        _V2M_NOTIFIER="notify-send"
    else
        _V2M_NOTIFIER="none"
    fi

    export _V2M_NOTIFIER
    echo "$_V2M_NOTIFIER"
}

# ─────────────────────────────────────────────────────────────────────────────
# CORE NOTIFICATION FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

v2m_notify() {
    local urgency="${1:-normal}"  # low, normal, critical
    local title="$2"
    local body="${3:-}"
    local icon="${4:-audio-input-microphone}"
    local timeout="${5:-$V2M_NOTIFY_TIMEOUT}"

    local notifier
    notifier=$(_v2m_detect_notifier)

    case "$notifier" in
        dunstify)
            # dunstify: Best option - supports replace, timeout, actions
            dunstify \
                --replace="$V2M_NOTIFY_ID" \
                --urgency="$urgency" \
                --icon="$icon" \
                --appname="Voice2Machine" \
                --timeout="$timeout" \
                "$title" "$body" &>/dev/null &
            ;;

        gdbus)
            # gdbus: D-Bus direct call - supports replace via replaces_id
            # See: https://specifications.freedesktop.org/notification-spec/latest/
            gdbus call \
                --session \
                --dest=org.freedesktop.Notifications \
                --object-path=/org/freedesktop/Notifications \
                --method=org.freedesktop.Notifications.Notify \
                "Voice2Machine" \
                "$V2M_NOTIFY_ID" \
                "$icon" \
                "$title" \
                "$body" \
                '[]' \
                '{"urgency": <byte 1>}' \
                "$timeout" &>/dev/null &
            ;;

        notify-send)
            # notify-send: Basic fallback (no replace support, but we close first)
            # Close any existing v2m notification by sending empty one
            notify-send \
                --urgency="$urgency" \
                --icon="$icon" \
                --app-name="Voice2Machine" \
                --expire-time="$timeout" \
                --hint=string:x-dunst-stack-tag:v2m \
                "$title" "$body" &>/dev/null &
            ;;

        *)
            # No notification system available
            return 1
            ;;
    esac

    return 0
}

# ─────────────────────────────────────────────────────────────────────────────
# CLOSE/DISMISS NOTIFICATION
# ─────────────────────────────────────────────────────────────────────────────

v2m_notify_close() {
    local notifier
    notifier=$(_v2m_detect_notifier)

    case "$notifier" in
        dunstify)
            dunstify --close="$V2M_NOTIFY_ID" &>/dev/null &
            ;;
        gdbus)
            gdbus call \
                --session \
                --dest=org.freedesktop.Notifications \
                --object-path=/org/freedesktop/Notifications \
                --method=org.freedesktop.Notifications.CloseNotification \
                "$V2M_NOTIFY_ID" &>/dev/null &
            ;;
        *)
            # notify-send doesn't support closing
            ;;
    esac
}

# ─────────────────────────────────────────────────────────────────────────────
# SOUND FEEDBACK (async, non-blocking)
# ─────────────────────────────────────────────────────────────────────────────

_v2m_play_sound() {
    local sound_id="$1"

    # Try canberra first (GNOME/GTK standard)
    if command -v canberra-gtk-play &>/dev/null; then
        canberra-gtk-play -i "$sound_id" &>/dev/null &
        return
    fi

    # Fallback to paplay with freedesktop sounds
    if command -v paplay &>/dev/null; then
        local sound_file="/usr/share/sounds/freedesktop/stereo/${sound_id}.oga"
        [[ -f "$sound_file" ]] && paplay "$sound_file" &>/dev/null &
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# SEMANTIC NOTIFICATION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

v2m_notify_recording() {
    v2m_notify "normal" "🔴 Grabando" "Habla ahora..." "audio-input-microphone" "$V2M_NOTIFY_TIMEOUT"
    _v2m_play_sound "message-new-instant"
}

v2m_notify_processing() {
    v2m_notify "low" "⏳ Procesando" "Transcribiendo..." "audio-x-generic" "$V2M_NOTIFY_TIMEOUT"
}

v2m_notify_success() {
    local text="${1:-Texto copiado al portapapeles}"

    # Truncate long text with ellipsis
    if [[ ${#text} -gt 100 ]]; then
        text="${text:0:97}..."
    fi

    v2m_notify "low" "✅ Copiado" "$text" "edit-copy" "$V2M_NOTIFY_TIMEOUT"
    _v2m_play_sound "complete"
}

v2m_notify_error() {
    local msg="${1:-Error desconocido}"
    v2m_notify "critical" "❌ Error" "$msg" "dialog-error" "$V2M_NOTIFY_TIMEOUT"
    _v2m_play_sound "dialog-error"
}

v2m_notify_no_voice() {
    v2m_notify "normal" "🔇 Sin voz detectada" "Intenta hablar más fuerte o más cerca del micrófono" "audio-volume-muted" "$V2M_NOTIFY_TIMEOUT"
}

v2m_notify_daemon_required() {
    v2m_notify "critical" "⚠️ Daemon no iniciado" "Ejecuta: scripts/development/daemon/start_daemon.sh" "system-run" "$V2M_NOTIFY_TIMEOUT"
    _v2m_play_sound "dialog-warning"
}

# ─────────────────────────────────────────────────────────────────────────────
# PROGRESS/DURATION NOTIFICATION (for long recordings)
# ─────────────────────────────────────────────────────────────────────────────

v2m_notify_recording_duration() {
    local seconds="${1:-0}"
    local formatted

    if [[ $seconds -lt 60 ]]; then
        formatted="${seconds}s"
    else
        formatted="$((seconds / 60))m $((seconds % 60))s"
    fi

    v2m_notify "normal" "🔴 Grabando" "$formatted" "audio-input-microphone" "$V2M_NOTIFY_TIMEOUT"
}
