#!/bin/bash
# scripts/development/restart_daemon.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🔄 Reiniciando Voice2Machine..."

# 1. Apagar (Stop)
"$SCRIPT_DIR/stop_daemon.sh"

# Pequeña pausa para asegurar liberación de puertos/recursos GPU
sleep 2

# 2. Encender (Start)
"$SCRIPT_DIR/start_daemon.sh"