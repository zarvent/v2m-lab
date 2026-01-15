# Voice2Machine Frontend

The Voice2Machine (V2M) frontend is a modern desktop application built with **Tauri 2** and **React 19**. It serves as a lightweight, secure, and efficient interface to control the local transcription engine (Python Daemon).

## 🚀 Philosophy

1.  **Local-First**: Privacy is paramount. All audio and text are processed on the local machine without unnecessary external calls.
2.  **Lightweight (SOTA 2026)**: Optimized binary (< 15MB) and low resource consumption (RAM < 50MB at rest) by eliminating the Node.js runtime in production.
3.  **Security**: Hardened communication via a secure IPC bridge in Rust. No Node.js APIs are exposed to the renderer context.

## 🛠️ Technology Stack

- **Desktop Framework**: [Tauri 2.x](https://tauri.app/) (Rust Backend)
- **UI Library**: [React 19](https://react.dev/)
- **Bundler**: [Vite 7.x](https://vitejs.dev/)
- **Language**: [TypeScript 5.8](https://www.typescriptlang.org/)
- **Styling**: [Tailwind CSS 4.1](https://tailwindcss.com/)
- **State**: [Zustand 5.x](https://zustand-demo.pmnd.rs/)
- **Forms**: React Hook Form + [Zod](https://zod.dev/)
- **Testing**: [Vitest](https://vitest.dev/) + Testing Library

## 🏛️ Project Structure

```
apps/frontend/
├── src/
│   ├── components/    # Atomic components and layouts
│   ├── hooks/         # Reusable hook logic
│   ├── stores/        # State management with Zustand
│   ├── schemas/       # Data and config validation
│   ├── types/         # TypeScript definitions (including IPC)
│   └── App.tsx        # Main application shell
├── src-tauri/
│   ├── src/lib.rs     # IPC bridge and socket handling
│   └── tauri.conf.json # Permissions and window configuration
└── docs/              # Technical documentation (frontend-specific)
```
