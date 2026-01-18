#!/bin/bash
# apps/frontend/scripts/clean.sh - V2M Deep Cleanup
# Nukes node_modules, dist, and Rust targets for a fresh start.

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
FRONTEND_DIR="$( cd "${SCRIPT_DIR}/.." &> /dev/null && pwd )"

echo "🧹 V2M Front-end Deep Clean..."

cd "$FRONTEND_DIR"

# 1. Clean Node environment
echo "   -> Removing node_modules and build artifacts..."
rm -rf node_modules dist .vite

# 2. Clean Tauri/Rust environment
if [[ -d "src-tauri" ]]; then
    echo "   -> Cleaning Rust target and build cache..."
    cd src-tauri
    # cargo clean is safer than rm -rf target for preserving tools
    if command -v cargo &> /dev/null; then
        cargo clean
    else
        rm -rf target
    fi
    rm -rf gen
    cd ..
fi

echo "✨ Cleanup complete."

# 3. Optional Reinstall
read -p "❓ Reinstall dependencies now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [[ -f "pnpm-lock.yaml" ]] && command -v pnpm &> /dev/null; then
        pnpm install
    else
        npm install
    fi
    echo "✅ Dependencies reinstalled."
fi
