#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# v2m-process.sh - Procesa texto del portapapeles con LLM
# ═══════════════════════════════════════════════════════════════════════════════
#
# DESCRIPCIÓN:
#   Lee el contenido del portapapeles, lo envía al LLM para limpieza/formato,
#   y copia el resultado de vuelta al portapapeles.
#
# USO:
#   ./v2m-process.sh        # Procesa texto del clipboard
#   ./v2m-process.sh --help # Muestra ayuda
#
# ATAJOS DE TECLADO (GNOME):
#   Configurar con: Settings → Keyboard → Custom Shortcuts
#
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

readonly V2M_PORT="${V2M_PORT:-8765}"
readonly V2M_URL="http://127.0.0.1:${V2M_PORT}"
readonly NOTIFY_EXPIRE_TIME=3000

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

notify() {
    notify-send --expire-time="${NOTIFY_EXPIRE_TIME}" "$1" "$2" 2>/dev/null || true
}

get_clipboard() {
    if command -v wl-paste &>/dev/null; then
        wl-paste 2>/dev/null || echo ""
    elif command -v xclip &>/dev/null; then
        xclip -o -selection clipboard 2>/dev/null || echo ""
    else
        echo ""
    fi
}

show_help() {
    cat <<EOF
v2m-process.sh - Procesa texto del portapapeles con LLM

USAGE:
    v2m-process.sh          Procesa el texto copiado
    v2m-process.sh --help   Muestra esta ayuda

WORKFLOW:
    1. Lee contenido del portapapeles
    2. Envía al LLM para limpieza (puntuación, formato)
    3. Copia resultado al portapapeles
    4. Notifica el resultado

REQUIREMENTS:
    - V2M daemon corriendo: ./scripts/operations/daemon/start_daemon.sh
    - xclip o wl-clipboard instalado

ENVIRONMENT:
    V2M_PORT    Server port (default: 8765)

EOF
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOGIC
# ─────────────────────────────────────────────────────────────────────────────

process_clipboard() {
    # 1. Obtener texto del portapapeles
    local text
    text=$(get_clipboard)

    if [[ -z "$text" ]]; then
        notify "❌ V2M" "El portapapeles está vacío"
        exit 1
    fi

    notify "⏳ V2M" "Procesando con LLM..."

    # 2. Enviar al servidor via HTTP POST
    # Escapar el texto para JSON
    local json_text
    json_text=$(printf '%s' "$text" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')

    local response
    response=$(curl -s -X POST "${V2M_URL}/llm/process" \
        -H "Content-Type: application/json" \
        -d "{\"text\": ${json_text}}" 2>/dev/null) || {
        notify "❌ V2M" "No se pudo conectar al servidor"
        exit 1
    }

    # 3. Extraer texto procesado de la respuesta
    local processed_text
    if [[ "$response" =~ \"text\":\ ?\"([^\"]+)\" ]]; then
        processed_text="${BASH_REMATCH[1]}"
        # Unescape basic JSON escapes
        processed_text=$(printf '%s' "$processed_text" | sed 's/\\n/\n/g; s/\\t/\t/g; s/\\"/"/g')
    else
        notify "❌ V2M" "Error procesando respuesta"
        exit 1
    fi

    # 4. Resultado ya está en el clipboard (el servidor lo copia)
    notify "✅ LLM" "${processed_text:0:50}..."
    echo "✅ Procesado y copiado al portapapeles"
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

main() {
    case "${1:-}" in
        --help|-h)
            show_help
            ;;
        *)
            process_clipboard
            ;;
    esac
}

main "$@"
