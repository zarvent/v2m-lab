#!/bin/bash
# scripts/development/stop_daemon.sh

echo "🛑 Buscando procesos de Voice2Machine..."

# Buscar PID del proceso que corre "v2m.main --daemon"
PID=$(pgrep -f "v2m.main --daemon")

if [ -z "$PID" ]; then
    echo "⚠️ No se encontró el demonio en ejecución."
    
    # Limpieza de seguridad: verificar socket huérfano
    SOCKET_PATH="/run/user/$(id -u)/v2m/v2m.sock"
    if [ -S "$SOCKET_PATH" ]; then
        echo "🧹 Limpiando socket huérfano: $SOCKET_PATH"
        rm "$SOCKET_PATH"
    fi
    exit 0
fi

echo "found PID: $PID. Enviando señal de terminación (SIGINT)..."
kill -SIGINT "$PID"

# Esperar hasta 5 segundos para que cierre
for i in {1..5}; do
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "✅ Demonio detenido correctamente."
        exit 0
    fi
    echo "⏳ Esperando cierre..."
    sleep 1
done

# Si sigue vivo, forzar cierre
echo "⚠️ El proceso no respondió. Forzando cierre (SIGKILL)..."
kill -SIGKILL "$PID"
echo "💀 Demonio eliminado."
