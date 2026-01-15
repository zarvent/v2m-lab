#!/bin/bash
# scripts/development/start_daemon.sh

# Obtener la ruta absoluta del directorio del proyecto (apps/backend)
# Asume que este script está en apps/backend/scripts/development/daemon/
PROJECT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

echo "📂 Directorio del proyecto: $PROJECT_ROOT"
cd "$PROJECT_ROOT"

# Verificar entorno virtual
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ Error: No se encuentra el entorno virtual en $PROJECT_ROOT/venv"
    exit 1
fi

echo "🔌 Activando entorno virtual..."
source venv/bin/activate

echo "🚀 Iniciando Demonio Voice2Machine..."
# Usamos exec para que el proceso python reemplace al shell y reciba las señales (Ctrl+C) directamente
exec python -m v2m.main --daemon
