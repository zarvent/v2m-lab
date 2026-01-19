#!/bin/bash

#
# repair_libs.sh - Script de reparación de librerías NVIDIA
#
# DESCRIPCIÓN:
#   Este script repara problemas comunes con las librerías NVIDIA
#   (cuDNN, cuBLAS) reinstalando las versiones compatibles con
#   faster-whisper y ctranslate2.
#
# USO:
#   ./scripts/repair_libs.sh
#
# OPERACIONES REALIZADAS:
#   1. Desinstala paquetes conflictivos:
#      - nvidia-cudnn-cu12
#      - nvidia-cublas-cu12
#      - faster-whisper
#      - ctranslate2
#   2. Reinstala versiones compatibles:
#      - nvidia-cudnn-cu12 (compatible con cuDNN 9.x)
#      - nvidia-cublas-cu12
#      - faster-whisper (trae ctranslate2 compatible)
#
# CUÁNDO USAR:
#   - Error "Could not load library libcudnn_ops.so.9"
#   - Error "cuDNN version mismatch"
#   - Transcripción falla en GPU pero funciona en CPU
#   - Después de actualizar drivers NVIDIA
#
# REQUISITOS:
#   - Entorno virtual activado (source venv/bin/activate)
#   - Conexión a internet para descargar paquetes
#   - ~3GB de espacio libre para descargas temporales
#
# ADVERTENCIAS:
#   - El script usa 'set -e', se detiene ante cualquier error
#   - Puede tomar varios minutos dependiendo de la conexión
#   - Ejecutar desde la raíz del proyecto
#
# VERIFICACIÓN POST-REPARACIÓN:
#   python scripts/check_cuda.py
#   python scripts/test_whisper_standalone.py
#
# AUTOR:
#   Voice2Machine Team
#
# DESDE:
#   v1.0.0
#

set -e

echo "🔧 Reparando instalación de librerías NVIDIA..."

source venv/bin/activate

# Desinstalar paquetes conflictivos
pip uninstall -y nvidia-cudnn-cu12 nvidia-cublas-cu12 faster-whisper ctranslate2

# Reinstalar versiones compatibles
# faster-whisper 1.2.1 trae ctranslate2 4.6.1
# ctranslate2 4.6.1 funciona bien con cudnn 9.x si se configura bien
pip install nvidia-cudnn-cu12 nvidia-cublas-cu12 faster-whisper

echo "✅ Reinstalación completada."
