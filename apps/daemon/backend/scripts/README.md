# 🛠️ Backend Utility Scripts

This directory contains scripts for managing the **Voice2Machine** backend, organized by macro-to-micro domains.

## 📂 Subdirectories

- **`operations/`**: Everything to run and interact with the system.
    - `daemon/`: Core service management (start/stop/restart).
    - `client/`: User-facing tools (toggle, integrations, process).
- **`diagnostics/`**: System health, CUDA verification, and audio troubleshooting.
- **`development/`**: Tools for extending the system.
    - `testing/`: Benchmarks and standalone component tests.
    - `maintenance/`: System cleanup and library repairs.
- **`setup/`**: Idempotent installation and model provisioning.
- **`shared/`**: Common logic and utilities used across all script categories.

## 🚀 Key Commands

| Script                                 | Purpose                                     |
| :------------------------------------- | :------------------------------------------ |
| `operations/client/v2m-daemon.sh`      | Start/Stop/Status of the backend service.   |
| `operations/client/v2m-toggle.sh`      | Toggle recording (best mapped to a hotkey). |
| `diagnostics/v2m-verify.sh`            | Full environment health check.              |
| `setup/install.sh`                     | Idempotent installation script.             |

## 🔧 Path Standards

All scripts leverage `shared/common.sh` (Bash) or `pathlib` (Python) to ensure they function correctly from any working directory, respecting the nested monorepo structure.
