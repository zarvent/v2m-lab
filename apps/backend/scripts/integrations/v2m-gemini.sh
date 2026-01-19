#!/bin/bash

#
# v2m-gemini.sh - Script de procesamiento de texto con Gemini
#
# DESCRIPCIÓN:
#   Este script envía texto directamente al procesador de V2M para
#   ser procesado por Gemini AI. Útil para pruebas rápidas o
#   integración con otros scripts.
#
# USO:
#   ./scripts/v2m-gemini.sh "<texto a procesar>"
#
# PARÁMETROS:
#   $1 - Texto a procesar con Gemini (requerido)
#
# EJEMPLOS:
#   # Procesar un texto simple
#   ./scripts/v2m-gemini.sh "corrige este texto con errores"
#
#   # Procesar desde una variable
#   texto="mi texto"
#   ./scripts/v2m-gemini.sh "$texto"
#
# DEPENDENCIAS:
#   - Entorno virtual de Python configurado en ./venv
#   - Variable GEMINI_API_KEY configurada en .env
#
# NOTAS:
#   - El resultado se envía al portapapeles automáticamente
#   - Requiere conexión a internet para la API de Gemini
#
# AUTOR:
#   Voice2Machine Team
#
# DESDE:
#   v1.0.0
#

# --- Configuración ---
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$( cd "$( dirname "${SCRIPT_DIR}" )/.." &> /dev/null && pwd )"

# --- Rutas Derivadas ---
VENV_PATH="${PROJECT_DIR}/venv"
MAIN_SCRIPT="${PROJECT_DIR}/src/v2m/main.py"

# --- Función Principal ---
run_orchestrator() {
    local text_to_process=$1

    if [ ! -f "${VENV_PATH}/bin/activate" ]; then
        echo "❌ Error: Entorno virtual no encontrado en ${VENV_PATH}" >&2
        exit 1
    fi

    source "${VENV_PATH}/bin/activate"
    echo "${text_to_process}" | python3 "${MAIN_SCRIPT}" "process"
}

# --- Lógica Principal ---
if [ -n "$1" ]; then
    run_orchestrator "$1"
else
    echo "Usage: $0 \"<text to process>\"" >&2
    exit 1
fi
