# Development Guide

This guide details how to set up and contribute to the Voice2Machine frontend.

## 🛠️ Prerequisites

- **Node.js**: Version 20 (LTS Iron) or higher. We recommend using `nvm`.
- **Rust**: Stable toolchain (1.75+) to compile `src-tauri`.
- **System Dependencies (Linux)**:
  ```bash
  sudo apt install libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev
  ```
- **Daemon**: For full functionality, the `voice2machine` service must be installed or running in another terminal.

## ⌨️ Key Commands

Commands should be run from the project root or from `apps/frontend/`.

### 🚀 Development Server

There are two modes to start the application:

1.  **Pure Web Mode (Mocked)**:

    ```bash
    npm run dev
    ```

    - **Speed**: Instant (<300ms).
    - **Usage**: UI/UX design, layout, isolated component logic.
    - **Limitation**: No access to Rust APIs or the real Daemon.

2.  **Tauri Mode (Native)**:
    ```bash
    npm run tauri dev
    ```

    - **Speed**: Requires Rust compilation (~10s initial, <2s incremental).
    - **Usage**: Real integration, IPC testing, final verification.
    - **Debug**: Opens a native window + DevTools (Inspect Element).

### ✅ Quality and Testing

We maintain rigorous "State of the Art" standards.

- **Linting**:

  ```bash
  npm run lint
  # or to auto-fix:
  npx eslint . --fix
  ```

- **Testing (Vitest)**:
  The project uses `vitest` with `happy-dom` for ultra-fast test execution.
  ```bash
  npm test
  ```

  - **Scope**: Unit tests for stores, utilities, and isolated components.
  - **Snapshot**: Snapshots are used to detect visual regressions in complex components.

### 📦 Build

To generate the final distributable binary:

```bash
npm run tauri build
```

The resulting artifact (`.deb`, `.AppImage`, or `.msi`) will be generated in `src-tauri/target/release/bundle/`.

## 🧪 Testing Strategy

### Unit Tests

Located alongside the code (`MyComponent.spec.tsx`). They must test:

1.  Correct rendering.
2.  Basic interactions (clicks, inputs).
3.  Conditional logic (loading/error states).

### Integration Tests

Test complete flows, for example:

1.  Start recording -> Store changes to `recording` -> UI shows Stop button.

### Tauri Mocks

Since `window.__TAURI__` does not exist in the `vitest` environment, we use a robust mock in `vitest.setup.ts` that simulates backend responses (`invoke`).
