#!/usr/bin/env bash
# =============================================================================
# install.sh - Automated installation script for voice2machine (Daemon only)
# =============================================================================
# WHAT THIS SCRIPT DOES:
#   1. Detects your operating system (Linux only for now)
#   2. Installs system dependencies
#   3. Creates Python virtual environment and installs the backend daemon
#   4. Configures your Gemini API key (optional)
#   5. Verifies GPU acceleration
# =============================================================================

set -euo pipefail

# --- Navigate to correct directory ---
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# SCRIPT_DIR is .../apps/daemon/backend/scripts/setup
BACKEND_DIR="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No color

log_info() { echo -e "${BLUE}[info]${NC} $1"; }
log_success() { echo -e "${GREEN}[ok]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[warn]${NC} $1"; }
log_error() { echo -e "${RED}[error]${NC} $1"; }
log_step() { echo -e "\n${CYAN}━━━ $1 ━━━${NC}"; }

# --- Help flag ---
show_help() {
    echo "Usage: ./install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help          Show this help message"
    echo "  --skip-gpu      Skip GPU verification"
    echo ""
    echo "Example:"
    echo "  ./install.sh              # Full installation"
    echo "  ./install.sh --skip-gpu   # Skip GPU check (for CPU-only systems)"
    exit 0
}

# Parse arguments
SKIP_GPU=false
for arg in "$@"; do
    case $arg in
        --help) show_help ;;
        --skip-gpu) SKIP_GPU=true ;;
    esac
done

# -----------------------------------------------------------------------------
# 1. PRE-FLIGHT CHECKS
# -----------------------------------------------------------------------------
preflight_checks() {
    log_step "Pre-flight checks"

    # Check OS
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        log_error "This script only supports Linux"
        log_warn "Detected: $OSTYPE"
        log_warn "For macOS/Windows, see manual installation in docs/"
        exit 1
    fi
    log_success "Linux detected"

    # Check curl (needed for uv install)
    if ! command -v curl &>/dev/null; then
        log_error "curl is required but not installed"
        log_warn "Install with: sudo apt install curl"
        exit 1
    fi
    log_success "curl available"

    # Check git
    if ! command -v git &>/dev/null; then
        log_warn "git not found - some features may not work"
    fi
}

# -----------------------------------------------------------------------------
# 2. DETECT PYTHON (3.12+)
# -----------------------------------------------------------------------------
detect_python() {
    log_step "Detecting Python 3.12+"

    for py in python3.13 python3.12 python3; do
        if command -v "$py" &>/dev/null; then
            local version
            version=$($py -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
            if [[ "${version}" =~ ^3\.(1[2-9]|[2-9][0-9])$ ]]; then
                PYTHON_CMD="$py"
                log_success "Python ${version} detected ($py)"
                return 0
            fi
        fi
    done

    log_error "Python 3.12+ is required"
    log_warn "Install with: sudo apt install python3.12 python3.12-venv"
    exit 1
}

# -----------------------------------------------------------------------------
# 3. SYSTEM DEPENDENCIES
# -----------------------------------------------------------------------------
install_system_deps() {
    log_step "Installing system dependencies"

    local deps=(ffmpeg xclip pulseaudio-utils build-essential)
    local missing=()

    # Cross-distro check using command -v where possible
    for dep in "${deps[@]}"; do
        case "$dep" in
            ffmpeg|xclip)
                if ! command -v "$dep" &>/dev/null; then
                    missing+=("$dep")
                fi
                ;;
            *)
                # For packages without CLI, try dpkg (Debian) or rpm (RHEL)
                if command -v dpkg &>/dev/null; then
                    if ! dpkg -l "$dep" &>/dev/null 2>&1; then
                        missing+=("$dep")
                    fi
                fi
                ;;
        esac
    done

    if [[ ${#missing[@]} -eq 0 ]]; then
        log_success "All system dependencies already installed"
        return
    fi

    log_info "Installing: ${missing[*]}"

    # Detect package manager
    if command -v apt-get &>/dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y "${missing[@]}"
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y "${missing[@]}"
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm "${missing[@]}"
    else
        log_error "Unsupported package manager. Install manually: ${missing[*]}"
        exit 1
    fi

    log_success "System dependencies installed"
}

# -----------------------------------------------------------------------------
# 4. INSTALL UV (SOTA 2026 package manager)
# -----------------------------------------------------------------------------
install_uv() {
    log_step "Installing uv (fast Python package manager)"

    if command -v uv &>/dev/null; then
        log_success "uv already installed ($(uv --version))"
        return 0
    fi

    log_info "Installing uv (10-100x faster than pip)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"

    if command -v uv &>/dev/null; then
        log_success "uv installed"
    else
        log_warn "Could not install uv, using pip as fallback"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# 5. SETUP BACKEND VENV
# -----------------------------------------------------------------------------
setup_backend() {
    log_step "Setting up Python backend"

    cd "${BACKEND_DIR}"

    if [[ -d "venv" ]]; then
        log_warn "Virtual environment already exists, skipping creation"
    else
        if command -v uv &>/dev/null; then
            uv venv venv --python "${PYTHON_CMD}"
        else
            "${PYTHON_CMD}" -m venv venv
        fi
        log_success "Virtual environment created"
    fi

    # shellcheck disable=SC1091
    source venv/bin/activate
    log_success "Virtual environment activated"

    # Install dependencies
    log_info "Installing Python dependencies..."
    if command -v uv &>/dev/null; then
        uv pip install --upgrade pip --quiet 2>/dev/null || pip install --upgrade pip -q
        uv pip install -e . --quiet
    else
        pip install --upgrade pip -q
        pip install -e . -q
    fi

    log_success "Backend installed (v2m module ready)"
}

# -----------------------------------------------------------------------------
# 6. CONFIGURE ENV
# -----------------------------------------------------------------------------
configure_env() {
    log_step "Configuring environment"

    cd "${BACKEND_DIR}"

    if [[ -f ".env" ]]; then
        log_warn ".env already exists, skipping"
        return
    fi

    echo ""
    echo -e "${YELLOW}==========================================${NC}"
    echo -e "${YELLOW}  GOOGLE GEMINI API CONFIGURATION${NC}"
    echo -e "${YELLOW}==========================================${NC}"
    echo ""
    echo "Get your free API key at: https://aistudio.google.com/"
    echo ""
    read -rp "Enter your Gemini API key (or press Enter to skip): " api_key

    if [[ -z "$api_key" ]]; then
        log_warn "Skipping API key, you can add it later to .env"
        echo "GEMINI_API_KEY=" > .env
    else
        echo "GEMINI_API_KEY=$api_key" > .env
        log_success ".env configured"
    fi
}

# -----------------------------------------------------------------------------
# 7. VERIFY GPU
# -----------------------------------------------------------------------------
verify_gpu() {
    if [[ "$SKIP_GPU" == "true" ]]; then
        log_warn "Skipping GPU verification (--skip-gpu)"
        return
    fi

    log_step "Verifying GPU acceleration"

    if command -v nvidia-smi &>/dev/null; then
        if nvidia-smi &>/dev/null; then
            log_success "NVIDIA GPU detected:"
            nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null || true

            # Check CUDA in Python (with venv active)
            cd "${BACKEND_DIR}"
            source venv/bin/activate
            if python -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
                log_success "CUDA available in PyTorch"
            else
                log_warn "GPU detected but CUDA not available in Python"
                log_warn "Run: pip install torch --index-url https://download.pytorch.org/whl/cu121"
            fi
            return 0
        fi
    fi

    log_warn "No GPU detected - Whisper will run on CPU (slower)"
    log_warn "For NVIDIA GPU, install CUDA drivers"
}

# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║    VOICE2MACHINE INSTALLER             ║${NC}"
    echo -e "${BLUE}║    State-of-the-Art 2026               ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""

    preflight_checks
    detect_python
    install_system_deps
    install_uv
    setup_backend
    configure_env
    verify_gpu

    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║    INSTALLATION COMPLETE ✓             ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo "NEXT STEPS:"
    echo ""
    echo "  1. Start the backend daemon:"
    echo "     cd apps/daemon/backend && source venv/bin/activate"
    echo "     python -m v2m.main --daemon"
    echo ""
    echo "  2. Configure keyboard shortcuts:"
    echo "     See docs/es/instalacion.md"
    echo ""
}

main "$@"
