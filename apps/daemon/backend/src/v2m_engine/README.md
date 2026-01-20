# `v2m_engine` (Rust performance engine)

`v2m_engine` is a high-performance Rust crate intended to provide low-latency primitives for Voice2Machine via a Python extension module (`pyo3`).

Today, consider it an **engine layer** you can iterate on independently; it is not automatically built/installed by the backend’s current `setuptools` packaging configuration.

## What it contains

- **Audio capture**: `cpal` input stream
- **Lock-free buffering**: single-producer/single-consumer ring buffer (`ringbuf`)
- **High-quality resampling**: band-limited sinc resampler (`rubato`)
- **VAD**: WebRTC VAD (`webrtc-vad`)
- **System monitoring hooks**: `sysinfo`
- Optional **NVIDIA** monitoring via `nvml-wrapper` feature

The crate is configured as a `cdylib` so it can be exposed to Python.

## Layout

- `Cargo.toml`: Rust package manifest
- `src/lib.rs`: PyO3 module entry + engine implementation

## Build (Rust-only)

From this directory:

```bash
cargo build --release
```

This produces a shared library under `target/release/`.

## Python integration status

The crate uses `pyo3` with `extension-module`, which is the right foundation for Python bindings.
However, the current backend build system (`apps/backend/pyproject.toml`) uses `setuptools` and does not yet ship/build this Rust extension as part of `pip install`.

If you want this engine to be used by the Python daemon, you’ll need an explicit integration step (packaging + import path + adapter implementation on the Python side).

## When to use it

Use `v2m_engine` when Python overhead becomes a bottleneck in:

- real-time audio capture,
- buffering,
- resampling,
- voice activity detection,
- or system-level telemetry.

Keep higher-level orchestration in `v2m/` and treat this crate as a fast, focused dependency.
