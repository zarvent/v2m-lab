#!/bin/bash
# apps/frontend/scripts/audit.sh - V2M Frontend QA Suite
# Runs linting, type-checking, and tests.

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
FRONTEND_DIR="$( cd "${SCRIPT_DIR}/.." &> /dev/null && pwd )"

echo "🩺 V2M Frontend Audit..."
cd "$FRONTEND_DIR"

# 1. Type Check
echo "🔍 Running Type Check (tsc)..."
if [[ -f "pnpm-lock.yaml" ]] && command -v pnpm &> /dev/null; then
    pnpm exec tsc --noEmit
else
    npm run build -- --noEmit || npx tsc --noEmit
fi
echo "   ✅ Types OK."

# 2. Unit Tests
echo "🧪 Running Unit Tests (vitest)..."
if [[ -f "pnpm-lock.yaml" ]] && command -v pnpm &> /dev/null; then
    pnpm run test --run
else
    npm run test -- --run
fi

echo "✨ Audit complete. Everything looks healthy!"
