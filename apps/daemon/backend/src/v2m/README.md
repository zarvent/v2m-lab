# `v2m` (Python backend package)

`v2m` is the main backend package for Voice2Machine.

It provides:

- The long-running **daemon** that keeps inference “warm”.
- A **Unix-socket IPC** protocol used by CLI and GUI clients.
- A **hexagonal architecture** layout (`domain/`, `application/`, `infrastructure/`, `core/`).

This package is designed to be **local-first**: by default, it does not expose a network API.

## Quick start (developer)

From `apps/backend/` (recommended):

```bash
python -m v2m.main --daemon
```

Then, from another terminal:

```bash
python -m v2m.main PING
python -m v2m.main START_RECORDING
python -m v2m.main STOP_RECORDING
```

## Package map

- `main.py`: unified entry point (daemon mode vs client/command mode).
- `daemon.py`: daemon process (IPC server + command dispatch).
- `client.py`: minimal async IPC client (used by CLI and scripts).
- `config.py`: Pydantic settings + config loading (env/.env/config.toml).
- `core/`: IPC framing, logging, DI container, command bus.
- `application/`: commands + handlers (use cases).
- `domain/`: entities, protocols (ports), domain errors.
- `infrastructure/`: concrete adapters (audio capture, whisper, LLM, filesystem).
- `utils/`: shared helpers (especially XDG-safe runtime paths).

## IPC protocol

The backend listens on a Unix socket path defined in `v2m.core.ipc_protocol`.

Framing:

- 4-byte big-endian length prefix
- UTF-8 JSON payload

Request shape:

```json
{ "cmd": "PING", "data": { "optional": "payload" } }
```

Response shape:

```json
{ "status": "success", "data": { "state": "idle" } }
```

Payload size is capped by `MAX_PAYLOAD_SIZE`.

## Adding a new IPC command (extension point)

High-level checklist:

1. Define/extend the command enum + schemas in `v2m.core.ipc_protocol`.
2. Add routing in `v2m.daemon.Daemon.handle_client`.
3. Implement a use case in `v2m.application` (prefer a command + handler).
4. If infrastructure is needed, define a protocol (port) under `v2m.domain` and implement it under `v2m.infrastructure`.
5. Wire dependencies via the DI container (`v2m.core.di.container`).

Keep dependency direction strict:

- `domain` → no imports from `application`/`infrastructure`
- `application` → may import from `domain`
- `infrastructure` → implements `domain` protocols

## Config + secrets

Default config is committed at `apps/backend/config.toml`.

- Use env vars or `.env` for secrets (e.g. `GEMINI_API_KEY`).
- Keep runtime paths XDG-compliant via `v2m.utils.paths`.

## Troubleshooting

- **Client says daemon isn’t running**: start with `python -m v2m.main --daemon`.
- **Socket path issues**: verify `$XDG_RUNTIME_DIR` and check the runtime dir created by `v2m.utils.paths.get_secure_runtime_dir`.
- **High latency on first command**: expected if models aren’t warmed; daemon mode is intended to keep inference hot.
