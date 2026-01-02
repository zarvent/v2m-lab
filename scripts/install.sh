#!/usr/bin/env bash
# =============================================================================
# install.sh - script de instalación automatizada de voice2machine
# =============================================================================
# QUÉ HACE ESTE SCRIPT
#   1 detecta tu sistema operativo solo linux por ahora
#   2 instala las dependencias del sistema
#   3 crea el entorno virtual de python
#   4 instala las dependencias de python
#   5 configura tu clave de api para gemini
#   6 verifica si tienes tarjeta gráfica compatible
# =============================================================================

set -euo pipefail

# --- navegación al directorio correcto ---
# este script está en scripts/, navegamos a apps/backend
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "${SCRIPT_DIR}" )"
BACKEND_DIR="${PROJECT_ROOT}/apps/backend"

# colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # sin color

log_info() { echo -e "${BLUE}[info]${NC} $1"; }
log_success() { echo -e "${GREEN}[ok]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[aviso]${NC} $1"; }
log_error() { echo -e "${RED}[error]${NC} $1"; }

# -----------------------------------------------------------------------------
# 1 DETECCIÓN DEL SISTEMA OPERATIVO
# -----------------------------------------------------------------------------
check_os() {
    log_info "verificando el sistema operativo..."

    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        log_error "por ahora este script solo funciona en linux"
        log_warn "sistema detectado: $OSTYPE"
        log_warn "para macos o windows revisa la documentación para instalación manual"
        exit 1
    fi

    log_success "linux detectado"
}

# -----------------------------------------------------------------------------
# 2 DETECTAR PYTHON COMPATIBLE (3.12+)
# -----------------------------------------------------------------------------
detect_python() {
    log_info "detectando versión de python compatible..."

    for py in python3.13 python3.12 python3; do
        if command -v "$py" &>/dev/null; then
            local version
            version=$($py -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
            # verificar que sea 3.12 o superior
            if [[ "${version}" =~ ^3\.(1[2-9]|[2-9][0-9])$ ]]; then
                PYTHON_CMD="$py"
                log_success "python ${version} detectado ($py)"
                return 0
            fi
        fi
    done

    log_error "se requiere python 3.12 o superior"
    log_warn "instala python 3.12+: sudo apt install python3.12 python3.12-venv"
    exit 1
}

# -----------------------------------------------------------------------------
# 3 DEPENDENCIAS DEL SISTEMA
# -----------------------------------------------------------------------------
install_system_deps() {
    log_info "instalando dependencias del sistema..."

    local deps=(ffmpeg xclip pulseaudio-utils python3-venv build-essential python3-dev)
    local missing=()

    for dep in "${deps[@]}"; do
        if ! dpkg -l "$dep" &>/dev/null; then
            missing+=("$dep")
        fi
    done

    if [[ ${#missing[@]} -eq 0 ]]; then
        log_success "todas las dependencias del sistema ya están instaladas"
        return
    fi

    log_info "instalando: ${missing[*]}"
    sudo apt-get update -qq
    sudo apt-get install -y "${missing[@]}"

    log_success "dependencias del sistema instaladas correctamente"
}

# -----------------------------------------------------------------------------
# 4 INSTALAR UV (gestor de dependencias state-of-the-art 2026)
# -----------------------------------------------------------------------------
install_uv() {
    if command -v uv &>/dev/null; then
        log_success "uv ya está instalado ($(uv --version))"
        return 0
    fi

    log_info "instalando uv (10-100x más rápido que pip)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"

    if command -v uv &>/dev/null; then
        log_success "uv instalado correctamente"
    else
        log_warn "no se pudo instalar uv, usando pip como fallback"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# 5 ENTORNO VIRTUAL DE PYTHON
# -----------------------------------------------------------------------------
setup_venv() {
    log_info "configurando el entorno virtual de python..."

    cd "${BACKEND_DIR}"

    if [[ -d "venv" ]]; then
        log_warn "el entorno virtual ya existe así que no lo voy a crear de nuevo"
    else
        # usar uv si está disponible, sino python3 -m venv
        if command -v uv &>/dev/null; then
            uv venv venv --python "${PYTHON_CMD}"
        else
            "${PYTHON_CMD}" -m venv venv
        fi
        log_success "entorno virtual creado"
    fi

    # shellcheck disable=SC1091
    source venv/bin/activate
    log_success "entorno virtual activado"
}

# -----------------------------------------------------------------------------
# 6 DEPENDENCIAS DE PYTHON
# -----------------------------------------------------------------------------
install_python_deps() {
    log_info "instalando dependencias de python..."

    # usar uv si está disponible (10-100x más rápido)
    if command -v uv &>/dev/null; then
        uv pip install --upgrade pip --quiet 2>/dev/null || pip install --upgrade pip -q
        uv pip install -r requirements.txt --quiet
    else
        pip install --upgrade pip -q
        pip install -r requirements.txt -q
    fi

    log_success "dependencias de python instaladas correctamente"
}

# -----------------------------------------------------------------------------
# 7 CONFIGURAR VARIABLES DE ENTORNO
# -----------------------------------------------------------------------------
configure_env() {
    log_info "configurando variables de entorno..."

    if [[ -f ".env" ]]; then
        log_warn "el archivo .env ya existe así que lo dejaré como está"
        return
    fi

    echo ""
    echo -e "${YELLOW}===========================================${NC}"
    echo -e "${YELLOW}  CONFIGURACIÓN DE LA API DE GOOGLE GEMINI${NC}"
    echo -e "${YELLOW}===========================================${NC}"
    echo ""
    echo "consigue tu clave de api gratis en: https://aistudio.google.com/"
    echo ""
    read -rp "ingresa tu clave de api de gemini o presiona enter para omitir: " api_key

    if [[ -z "$api_key" ]]; then
        log_warn "saltando configuración de la api key puedes agregarla después en el archivo .env"
        cp .env.example .env 2>/dev/null || echo "GEMINI_API_KEY=" > .env
    else
        echo "GEMINI_API_KEY=$api_key" > .env
        log_success "archivo .env configurado correctamente"
    fi
}

# -----------------------------------------------------------------------------
# 8 VERIFICAR TARJETA GRÁFICA (nvidia-smi nativo, sin dependencias Python)
# -----------------------------------------------------------------------------
verify_gpu() {
    log_info "verificando si hay aceleración por gpu..."

    # verificación robusta con nvidia-smi (no depende de Python)
    if command -v nvidia-smi &>/dev/null; then
        if nvidia-smi &>/dev/null; then
            log_success "GPU NVIDIA detectada:"
            nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null || true

            # verificar CUDA disponible en Python
            if python -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
                log_success "CUDA disponible en PyTorch"
            else
                log_warn "GPU detectada pero CUDA no disponible en Python"
                log_warn "ejecuta: pip install torch --index-url https://download.pytorch.org/whl/cu121"
            fi
            return 0
        fi
    fi

    log_warn "no detecté ninguna gpu así que whisper correrá en el procesador y será más lento"
    log_warn "si tienes una tarjeta nvidia instala los controladores de cuda"
    return 0
}

# -----------------------------------------------------------------------------
# PRINCIPAL
# -----------------------------------------------------------------------------
main() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  INSTALADOR DE VOICE2MACHINE${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    check_os
    detect_python
    install_system_deps
    install_uv
    setup_venv
    install_python_deps
    configure_env
    verify_gpu

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  INSTALACIÓN COMPLETADA${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "PRÓXIMOS PASOS:"
    echo "  1 activa el entorno virtual:  source venv/bin/activate"
    echo "  2 ejecuta el servicio:        python scripts/v2m-daemon.sh"
    echo "  3 configura los atajos:       mira docs/instalacion.md"
    echo ""
}

main "$@"
