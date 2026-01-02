#!/bin/bash

# This file is part of voice2machine.
#
# voice2machine is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# voice2machine is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with voice2machine.  If not, see <https://www.gnu.org/licenses/>.
# Script de limpieza para eliminar procesos zombie de v2m
# Uso: ./scripts/cleanup_v2m.sh [--force]

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FORCE=false
if [[ "${1:-}" == "--force" ]]; then
    FORCE=true
fi

echo -e "${YELLOW}🧹 V2M Cleanup Script${NC}"
echo "======================================"

# 1. Buscar procesos v2m
echo -e "\n${YELLOW}[1/4]${NC} Buscando procesos v2m..."
PIDS=$(pgrep -f "v2m" || true)

if [[ -z "$PIDS" ]]; then
    echo -e "${GREEN}✅ No se encontraron procesos v2m corriendo${NC}"
else
    echo -e "${RED}⚠️  Procesos v2m encontrados:${NC}"
    ps aux | grep "v2m" | grep -v grep | grep -v "cleanup_v2m.sh"

    if [[ "$FORCE" == "true" ]]; then
        echo -e "\n${YELLOW}Matando procesos...${NC}"
        pkill -9 -f "v2m" || true
        echo -e "${GREEN}✅ Procesos eliminados${NC}"
    else
        echo -e "\n${YELLOW}Usa --force para eliminarlos automáticamente${NC}"
        read -p "¿Matar estos procesos? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            pkill -9 -f "v2m" || true
            echo -e "${GREEN}✅ Procesos eliminados${NC}"
        fi
    fi
fi

# 2. Limpiar socket huérfano
echo -e "\n${YELLOW}[2/4]${NC} Verificando socket Unix..."
if [[ -S /tmp/v2m.sock ]]; then
    echo -e "${YELLOW}Socket encontrado, eliminando...${NC}"
    rm -f /tmp/v2m.sock
    echo -e "${GREEN}✅ Socket eliminado${NC}"
else
    echo -e "${GREEN}✅ No hay socket huérfano${NC}"
fi

# 3. Limpiar PID file
echo -e "\n${YELLOW}[3/4]${NC} Verificando PID file..."
if [[ -f /tmp/v2m_daemon.pid ]]; then
    echo -e "${YELLOW}PID file encontrado, eliminando...${NC}"
    rm -f /tmp/v2m_daemon.pid
    echo -e "${GREEN}✅ PID file eliminado${NC}"
else
    echo -e "${GREEN}✅ No hay PID file huérfano${NC}"
fi

# 4. Verificar VRAM
echo -e "\n${YELLOW}[4/4]${NC} Verificando uso de VRAM..."
if command -v nvidia-smi &> /dev/null; then
    VRAM_USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
    VRAM_FREE=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits)

    echo -e "VRAM Usada: ${VRAM_USED}MiB"
    echo -e "VRAM Libre: ${VRAM_FREE}MiB"

    if [[ $VRAM_USED -lt 500 ]]; then
        echo -e "${GREEN}✅ VRAM limpia (< 500MiB)${NC}"
    else
        echo -e "${YELLOW}⚠️  VRAM en uso (${VRAM_USED}MiB) - puede ser normal si el daemon está corriendo${NC}"
    fi
else
    echo -e "${YELLOW}nvidia-smi no disponible, saltando...${NC}"
fi

echo -e "\n${GREEN}======================================"
echo -e "✅ Limpieza completada${NC}"
