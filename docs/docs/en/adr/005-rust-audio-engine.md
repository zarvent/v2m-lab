# ADR-005: Rust Audio Engine (v2m_engine)

## Status

Accepted

## Date

2025-01-10

## Context

Audio capture in pure Python presented critical limitations for a real-time dictation experience:

### Identified problems:

1. **GIL blocking**: Audio capture competed with transcription for the GIL
2. **Variable latency**: 10-50ms jitter in audio buffering
3. **sounddevice overhead**: Python callbacks added latency
4. **Inefficient VAD**: Silero VAD in Python processed samples with overhead

### Requirements:

- Capture latency < 10ms
- Pre-processed VAD before Python
- Lock-free circular buffer
- Zero-copy when possible

## Decision

**Develop native Rust extension** (`v2m_engine`) for critical audio tasks.

### Components:

```
v2m_engine/
├── src/
│   ├── audio_capture.rs  # CPAL-based capture
│   ├── ring_buffer.rs    # Lock-free circular buffer
│   ├── vad.rs            # Silero ONNX inference
│   └── lib.rs            # PyO3 bindings
```

### Python interface:

```python
from v2m_engine import AudioCapture, VADProcessor

capture = AudioCapture(sample_rate=16000, buffer_size=4096)
vad = VADProcessor(threshold=0.5)

async with capture.stream() as audio:
    if vad.contains_speech(audio):
        await transcriber.process(audio)
```

## Consequences

### Positive

- ✅ **Latency < 5ms**: CPAL + lock-free buffers
- ✅ **GIL-free**: Audio thread independent from Python
- ✅ **Efficient VAD**: Native ONNX runtime, 10x faster
- ✅ **Zero-copy**: NumPy arrays share memory with Rust

### Negative

- ⚠️ **Build complexity**: Requires Rust toolchain + maturin
- ⚠️ **Cross-language debugging**: Mixed Python/Rust stack traces
- ⚠️ **Portability**: Platform-specific binaries

## Alternatives Considered

### Pure Python (sounddevice + numpy)

- **Rejected**: GIL blocking and unacceptable latency.

### Cython

- **Rejected**: Still tied to GIL, limited benefits.

### C++ Extension

- **Rejected**: Rust offers memory safety without GC, better tooling (cargo).

## References

- [PyO3 - Rust bindings for Python](https://pyo3.rs/)
- [CPAL - Cross-platform Audio Library](https://github.com/RustAudio/cpal)
- [Lock-free Ring Buffer](https://github.com/agerasev/ringbuf)
