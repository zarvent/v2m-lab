# 🛠️ Frontend Utility Scripts

High-value tools for developing and maintaining the Voice2Machine GUI (Tauri).

## 🚀 Daily Development

### `dev.sh`

The primary entry point.

- Checks if the backend daemon is running (and starts it if necessary).
- Launches the Tauri development environment (`tauri dev`).
- **Usage**: `./scripts/dev.sh`

## 🧹 Maintenance & QA

### `clean.sh`

Deep cleanup for when things get weird.

- Nukes `node_modules`, `dist`, and Rust `target` folders.
- Optionally reinstalls dependencies.
- **Usage**: `./scripts/clean.sh`

### `audit.sh`

QA suite for code health.

- Runs TypeScript type-checking (`tsc`).
- Runs unit tests (`vitest`).
- **Usage**: `./scripts/audit.sh`

## 📦 Build & Assets

### `bundle.sh`

Production bundling wrapper.

- Runs `tauri build`.
- Automatically exports `.deb` and `.AppImage` artifacts to the project's root `release/` folder.
- **Usage**: `./scripts/bundle.sh`

### `setup-icons.sh`

Fast icon regeneration.

- Updates all platform-specific icons from a single source image.
- **Usage**: `./scripts/setup-icons.sh [path/to/logo.png]` (defaults to `src/assets/logo.png`)
