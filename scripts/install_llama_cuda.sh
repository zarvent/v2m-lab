#!/bin/bash
# This file is part of voice2machine.
#
# voice2machine is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# instala llama-cpp-python con soporte CUDA para RTX 3060

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/apps/backend/venv"
CUDA_VERSION="cu124"  # RTX 3060 con driver 580.x soporta CUDA 12.4+

echo "🔧 instalando llama-cpp-python con CUDA ${CUDA_VERSION}..."

# activar venv si existe
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    echo "✅ venv activado: $VENV_PATH"
else
    echo "⚠️  venv no encontrado en $VENV_PATH, usando pip global"
fi

# instalar con wheels precompilados para CUDA
pip install llama-cpp-python \
    --extra-index-url "https://abetlen.github.io/llama-cpp-python/whl/${CUDA_VERSION}"

echo ""
echo "✅ instalación completada"
echo "verifica con: python -c 'from llama_cpp import Llama; print(\"ok\")'"
