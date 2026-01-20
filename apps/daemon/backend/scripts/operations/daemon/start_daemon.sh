#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# start_daemon.sh - Inicia el servidor V2M (FastAPI + Uvicorn)
# ═══════════════════════════════════════════════════════════════════════════════
#
# SOTA 2026: Servidor HTTP REST reemplaza sockets Unix manuales.
# Un Junior puede probar con: curl -X POST http://localhost:8765/toggle
#
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

# Obtener la ruta absoluta del directorio del proyecto (apps/backend)
PROJECT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

echo "📂 Directorio del proyecto: $PROJECT_ROOT"
cd "$PROJECT_ROOT"

# Verificar entorno virtual
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ Error: No se encuentra el entorno virtual en $PROJECT_ROOT/venv"
    echo "   Ejecuta: python -m venv venv && pip install -e ."
    exit 1
fi

echo "🔌 Activando entorno virtual..."
source venv/bin/activate

# Asegurar que el código en src/ sea visible
export PYTHONPATH="src:${PYTHONPATH:-}"

# Puerto configurable (default: 8765)
PORT="${V2M_PORT:-8765}"

echo "🚀 Iniciando V2M Server en http://127.0.0.1:${PORT}"
echo "📚 Documentación: http://127.0.0.1:${PORT}/docs"
echo ""
echo "   Comandos rápidos:"
echo "   curl -X POST http://localhost:${PORT}/toggle   # Toggle grabación"
echo "   curl http://localhost:${PORT}/status           # Ver estado"
echo ""

# Usamos exec para que el proceso python reemplace al shell y reciba señales (Ctrl+C)
exec python3 -m v2m.main --port "$PORT"

