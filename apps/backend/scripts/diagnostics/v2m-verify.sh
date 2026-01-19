#!/bin/bash

#
# v2m-verify.sh - Script de verificación del entorno V2M
#
# DESCRIPCIÓN:
#   Este script realiza una verificación completa del entorno de
#   Voice2Machine, comprobando todas las dependencias, configuraciones
#   y permisos necesarios para el correcto funcionamiento.
#
# USO:
#   ./scripts/v2m-verify.sh
#
# VERIFICACIONES REALIZADAS:
#   1. Entorno virtual (venv/)
#   2. faster-whisper instalado
#   3. CUDA disponible (PyTorch)
#   4. LD_LIBRARY_PATH configurado
#   5. Script v2m-toggle.sh ejecutable
#   6. Atajo de teclado Ctrl+Shift+Space
#   7. Micrófono detectado (pactl)
#   8. FFmpeg instalado
#   9. xclip instalado
#
# CÓDIGOS DE COLOR:
#   Verde  - Verificación exitosa
#   Rojo   - Verificación fallida (requiere acción)
#   Amarillo - Advertencia (puede funcionar pero no es óptimo)
#
# SALIDA:
#   El script muestra un resumen al final indicando:
#   - Número de problemas encontrados
#   - Instrucciones de reinstalación si hay fallas
#   - Próximos pasos si todo está bien
#
# DEPENDENCIAS:
#   - gsettings: Para verificar atajos de teclado GNOME
#   - pactl: Para verificar configuración de audio
#   - Python con torch instalado
#
# EJEMPLOS:
#   # Verificación completa
#   ./scripts/v2m-verify.sh
#
#   # Guardar resultado a archivo
#   ./scripts/v2m-verify.sh > verificacion.log 2>&1
#
# NOTAS:
#   - Ejecutar antes de reportar problemas
#   - Los atajos de teclado solo se verifican en GNOME
#
# AUTOR:
#   Voice2Machine Team
#
# DESDE:
#   v1.0.0
#

echo "🔍 Verificando setup de Whisper..."
echo "=================================="

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ISSUES=0

# Detectar directorio del proyecto dinámicamente
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "${SCRIPT_DIR}/../utils/common.sh"

# BACKEND_DIR y REPO_ROOT vienen de common.sh

# 1. Verificar venv
echo -n "✓ Entorno virtual: "
if [ -d "${BACKEND_DIR}/venv" ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FALLO${NC}"
    ISSUES=$((ISSUES + 1))
fi

# 2. Verificar faster-whisper
echo -n "✓ Faster-Whisper instalado: "
if source "${BACKEND_DIR}/venv/bin/activate" 2>/dev/null && python3 -c "import faster_whisper" 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FALLO${NC}"
    ISSUES=$((ISSUES + 1))
fi

# 3. Verificar CUDA
echo -n "✓ CUDA disponible: "
if source "${BACKEND_DIR}/venv/bin/activate" 2>/dev/null && python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null | grep -q "True"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}NO (Verificar CUDA)${NC}"
    ISSUES=$((ISSUES + 1))
fi

# 4. Verificar LD_LIBRARY_PATH
echo -n "✓ LD_LIBRARY_PATH configurado: "
if source "${BACKEND_DIR}/venv/bin/activate" 2>/dev/null && [ -n "$LD_LIBRARY_PATH" ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}VACIO (Se configurará al activar)${NC}"
fi

# 5. Verificar script principal
echo -n "✓ Script v2m-toggle.sh: "
if [ -x "${BACKEND_DIR}/scripts/service/v2m-toggle.sh" ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FALLO${NC}"
    ISSUES=$((ISSUES + 1))
fi

# 6. Verificar atajo de teclado
echo -n "✓ Atajo de teclado Ctrl+Shift+Space: "
if gsettings get org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/whisper0/ command 2>/dev/null | grep -q "v2m-toggle.sh"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}NO CONFIGURADO${NC}"
    ISSUES=$((ISSUES + 1))
fi

# 7. Verificar micrófono
echo -n "✓ Micrófono detectado: "
if pactl info | grep -q "Default Source"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}NO O NO CONFIGURADO${NC}"
fi

# 8. Verificar ffmpeg
echo -n "✓ FFmpeg instalado: "
if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FALLO${NC}"
    ISSUES=$((ISSUES + 1))
fi

# 9. Verificar xclip
echo -n "✓ xclip instalado: "
if command -v xclip &> /dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FALLO${NC}"
    ISSUES=$((ISSUES + 1))
fi

echo "=================================="

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✨ ¡Setup completamente funcional!${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "1. Presiona Ctrl+Shift+Space para grabar"
    echo "2. Habla claramente en español"
    echo "3. Presiona Ctrl+Shift+Space nuevamente para transcribir"
    echo "4. Ctrl+V para pegar el resultado"
else
    echo -e "${RED}⚠️  Se encontraron $ISSUES problema(s)${NC}"
    echo ""
    echo "Para reinstalar:"
    echo "cd ${BACKEND_DIR}"
    echo "rm -rf venv/"
    echo "python3 -m venv venv"
    echo "venv/bin/pip install -r requirements.txt"
fi
