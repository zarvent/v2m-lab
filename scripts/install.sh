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
# 2 DEPENDENCIAS DEL SISTEMA
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
# 3 ENTORNO VIRTUAL DE PYTHON
# -----------------------------------------------------------------------------
setup_venv() {
    log_info "configurando el entorno virtual de python..."

    if [[ -d "venv" ]]; then
        log_warn "el entorno virtual ya existe así que no lo voy a crear de nuevo"
    else
        python3 -m venv venv
        log_success "entorno virtual creado"
    fi

    # shellcheck disable=SC1091
    source venv/bin/activate
    log_success "entorno virtual activado"
}

# -----------------------------------------------------------------------------
# 4 DEPENDENCIAS DE PYTHON
# -----------------------------------------------------------------------------
install_python_deps() {
    log_info "instalando dependencias de python..."

    pip install --upgrade pip -q
    pip install -r requirements.txt -q

    log_success "dependencias de python instaladas correctamente"
}

# -----------------------------------------------------------------------------
# 5 CONFIGURAR VARIABLES DE ENTORNO
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
# 6 VERIFICAR TARJETA GRÁFICA
# -----------------------------------------------------------------------------
verify_gpu() {
    log_info "verificando si hay aceleración por gpu..."

    if python scripts/check_cuda.py 2>/dev/null; then
        log_success "aceleración por gpu disponible"
    else
        log_warn "no detecté ninguna gpu así que whisper correrá en el procesador y será más lento"
        log_warn "si tienes una tarjeta nvidia instala los controladores de cuda"
    fi
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
    install_system_deps
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
