# 🛠️ Backend Utility Scripts

This directory contains scripts for managing the **Voice2Machine** backend, organized by domain.

## 📂 Subdirectories

- **`service/`**: Core daemon control (`v2m-daemon.sh`, `v2m-toggle.sh`, `v2m-process.sh`).
- **`diagnostics/`**: Tools to verify CUDA, audio, and daemon health.
- **`integrations/`**: Cloud and local LLM integration scripts.
- **`maintenance/`**: Cleanup and library repair tools.
- **`setup/`**: Installation and model downloaders.
- **`testing/`**: Latency benchmarks and component tests.
- **`utils/`**: Shared Bash and Python helpers.
- **`development/`**: Developer-specific workflow scripts.

## 🚀 Key Commands

| Script                      | Purpose                                     |
| :-------------------------- | :------------------------------------------ |
| `service/v2m-daemon.sh`     | Start/Stop/Status of the backend service.   |
| `service/v2m-toggle.sh`     | Toggle recording (best mapped to a hotkey). |
| `diagnostics/v2m-verify.sh` | Full environment health check.              |
| `setup/install.sh`          | Idempotent installation script.             |

## 🔧 Path Standards

All scripts use `utils/common.sh` for robust path resolution. In Python scripts, `Path(__file__)` is used to ensure they work regardless of the current working directory.
