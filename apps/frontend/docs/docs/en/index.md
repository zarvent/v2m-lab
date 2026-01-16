# Frontend Documentation

Welcome to the technical documentation for the **Voice2Machine** frontend. This application represents the state of the art (SOTA 2026) in local AI user interfaces: ultra-lightweight, reactive, and privacy-respecting.

## 🚀 Overview

The frontend is not just a "view"; it is an **intelligent orchestrator** that manages the interaction between the human user and the local inference engine.

### Key Features

- **Local-First & Offline**: Works without internet. Privacy is the norm.
- **Native Performance**: Built on Tauri 2.0, consuming a fraction of the RAM traditional Electron apps use.
- **Zero Latency**: Optimistic interface that reacts instantaneously while the backend processes asynchronously.
- **Accessible**: Strict compliance with WCAG 2.1 AA.

## 📚 Documentation Navigation

This documentation is structured for different profiles:

- **For Architects**: See [Architecture](architecture.md) to understand data flow and the IPC bridge.
- **For UI Developers**: Check [Components](components.md) and [Hooks and Utilities](hooks_utils.md).
- **For Integration Engineers**: Study [State Management](state_management.md) and data contracts.
- **For Contributors**: Follow the [Development](development.md) guide to set up your environment.

## 🛠️ Main Technologies

| Technology       | Version | Purpose                                       |
| :--------------- | :------ | :-------------------------------------------- |
| **Tauri**        | 2.0     | Native application framework (Rust Core).     |
| **React**        | 19      | UI library with concurrent rendering.         |
| **TypeScript**   | 5.x     | Static type safety and IPC contracts.         |
| **Zustand**      | 5.x     | Atomic and optimized global state management. |
| **Tailwind CSS** | 4.0     | Utility-first design system with Rust engine. |
| **Vitest**       | 1.x     | High-speed unit testing.                      |

---

!!! info "Version Note"
This documentation corresponds to version `v2.0.0-alpha` (Codename: _Hyperion_).
