#!/bin/bash
# apps/frontend/scripts/setup-icons.sh - V2M Icon Generator
# Simplifies icon updates for the Tauri app.

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
FRONTEND_DIR="$( cd "${SCRIPT_DIR}/.." &> /dev/null && pwd )"

# Default source icon path
SOURCE_ICON="${FRONTEND_DIR}/src/assets/logo.png"

echo "🎨 V2M Icon Setup Utility..."

if [[ ! -f "$SOURCE_ICON" ]]; then
    # Attempt to find common alternatives
    SOURCE_ICON="${FRONTEND_DIR}/public/logo.png"
fi

if [[ ! -f "$SOURCE_ICON" ]]; then
    echo "❌ Error: Source icon not found. Please provide a path to a 1024x1024 PNG."
    echo "   Usage: $0 [path/to/icon.png]"
    exit 1
fi

if [[ -n "${1:-}" ]]; then
    SOURCE_ICON="$1"
fi

echo "🎬 Generating icons from: $SOURCE_ICON"

cd "$FRONTEND_DIR"

if [[ -f "pnpm-lock.yaml" ]] && command -v pnpm &> /dev/null; then
    pnpm tauri icon "$SOURCE_ICON"
else
    npm run tauri icon "$SOURCE_ICON" || npx tauri icon "$SOURCE_ICON"
fi

echo "✅ Icons generated successfully in src-tauri/icons/"
