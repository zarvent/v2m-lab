# Audio Infrastructure

This submodule handles everything related to low-level audio capture and processing.

## Content

- `recorder.py` - `AudioRecorder` class that manages audio capture using `sounddevice` with pre-allocated buffers for high performance
- `recording_worker.py` - Script to run recording in an isolated process if needed (to avoid GIL issues or blocks)

## Features

- Background thread recording support
- Direct numpy buffer access for efficiency (zero-copy)
- Robust audio device error handling
