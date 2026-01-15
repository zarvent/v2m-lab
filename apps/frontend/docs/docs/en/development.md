# Development Guide

This guide details how to set up and contribute to the Voice2Machine frontend.

## 🛠️ Prerequisites

- **Node.js**: Version 20 or higher.
- **Rust**: Stable toolchain (to compile `src-tauri`).
- **System Dependencies (Linux)**: `libwebkit2gtk-4.1-dev`, `libappindicator3-dev`, `librsvg2-dev`.
- **Python Daemon**: It is recommended to have the daemon running to see real data in the interface.

## ⌨️ Frequent Commands

Commands must be executed from the `apps/frontend/` directory.

### Development

- `npm run dev`: Starts the web development server (Vite) in the browser.
- `npm run tauri dev`: Starts the application in native mode with Hot Reload for both Rust and React.

### Validation and Quality

- `npx tsc -p tsconfig.json --noEmit`: Static type checking.
- `npx eslint . --fix`: Linting and style correction according to project configuration.
- `npm test`: Runs unit tests with Vitest.

### Build

- `npm run build`: Generate the web application production bundle.
- `npm run tauri build`: Compiles the optimized executable binary. The result will be in `src-tauri/target/release/`.

## 🧪 Testing

The project uses **Vitest** with the `happy-dom` environment.

- **Unit Tests**: Located next to components or utilities with the `.spec.tsx` or `.test.ts` extension.
- **Mocking**: We use mocks for Tauri APIs in `vitest.setup.ts` to allow tests to run without a real native environment.

**Golden Rule**: Whenever a bug is fixed or a feature is added, a test must be included to validate it.
