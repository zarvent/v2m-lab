#!/bin/bash
# This file is part of voice2machine.
#
# voice2machine is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# descarga Qwen2.5-3B-Instruct GGUF Q4_K_M para uso local

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_DIR="$SCRIPT_DIR/../apps/backend/models"
MODEL_FILE="qwen2.5-3b-instruct-q4_k_m.gguf"
MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/${MODEL_FILE}"

mkdir -p "$MODEL_DIR"

if [ -f "$MODEL_DIR/$MODEL_FILE" ]; then
    echo "✅ modelo ya existe: $MODEL_DIR/$MODEL_FILE"
    ls -lh "$MODEL_DIR/$MODEL_FILE"
    exit 0
fi

echo "📥 descargando Qwen2.5-3B-Instruct Q4_K_M (~1.93GB)..."
echo "   desde: $MODEL_URL"
echo ""

# opción 1: huggingface-cli (si está instalado)
if command -v huggingface-cli &> /dev/null; then
    echo "usando huggingface-cli..."
    huggingface-cli download Qwen/Qwen2.5-3B-Instruct-GGUF \
        "$MODEL_FILE" \
        --local-dir "$MODEL_DIR"
else
    # opción 2: wget con progreso
    echo "usando wget..."
    wget --progress=bar:force:noscroll -O "$MODEL_DIR/$MODEL_FILE" "$MODEL_URL"
fi

echo ""
echo "✅ modelo descargado: $MODEL_DIR/$MODEL_FILE"
ls -lh "$MODEL_DIR/$MODEL_FILE"
