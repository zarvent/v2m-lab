#!/bin/bash
# apps/frontend/scripts/bundle.sh - V2M Production Bundler
# Prepares the application for release.

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
FRONTEND_DIR="$( cd "${SCRIPT_DIR}/.." &> /dev/null && pwd )"
REPO_ROOT="$( cd "${FRONTEND_DIR}/.." &> /dev/null && pwd )"
RELEASE_DIR="${REPO_ROOT}/release"

echo "📦 V2M Production Bundler..."

# 1. Environment Check
if ! command -v cargo &> /dev/null; then
    echo "❌ Error: Rust/Cargo not found. Required for Tauri build."
    exit 1
fi

# 2. Build
cd "$FRONTEND_DIR"
echo "🚀 Building application..."
if [[ -f "pnpm-lock.yaml" ]] && command -v pnpm &> /dev/null; then
    pnpm tauri build
else
    npm run tauri build
fi

# 3. Export to central release folder
mkdir -p "$RELEASE_DIR"
echo "📂 Moving artifacts to $RELEASE_DIR..."

# Detect OS to find the right binary (Linux focused as per user info)
if [[ -d "src-tauri/target/release/bundle" ]]; then
    # Copy .deb/AppImage if they exist
    find src-tauri/target/release/bundle -name "*.AppImage" -exec cp {} "$RELEASE_DIR/" \;
    find src-tauri/target/release/bundle -name "*.deb" -exec cp {} "$RELEASE_DIR/" \;
    echo "✅ Artifacts exported to $RELEASE_DIR"
else
    echo "⚠️ Warning: Could not find build artifacts in standard Tauri location."
fi
