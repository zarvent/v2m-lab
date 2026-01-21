# ADR-003: Selection of faster-whisper over whisper.cpp

## Status

Accepted

## Date

2024-06-01

## Context

For local voice transcription, we needed to choose a Whisper model implementation from OpenAI that would maximize performance on consumer NVIDIA GPUs (RTX 3060-4090).

### Options evaluated:

1. **OpenAI Whisper (original)**: Reference implementation in PyTorch
2. **whisper.cpp**: Pure C++ implementation with CUDA support
3. **faster-whisper**: Implementation on CTranslate2 (optimized C++/CUDA)

### Requirements:

- Latency < 500ms for 5 seconds of audio (8x real-time minimum)
- Support for `large-v3` models and `distil` variants
- INT8/FP16 quantization to optimize VRAM
- Python API for backend integration
- Audio streaming/chunking

## Decision

**Adopt faster-whisper** as the main transcription engine.

### Justification:

| Criteria            | Whisper (PyTorch) | whisper.cpp | faster-whisper   |
| ------------------- | ----------------- | ----------- | ---------------- |
| **Speed**           | 1x (baseline)     | 4x          | 4-8x             |
| **VRAM (large-v3)** | 10GB              | 6GB         | 4-5GB            |
| **Python API**      | ✅ Native         | ❌ Bindings | ✅ Excellent     |
| **Quantization**    | Limited           | ✅          | ✅ INT8/FP16     |
| **Maintenance**     | OpenAI            | Community   | Active (Systran) |

## Consequences

### Positive

- ✅ **4-8x faster** than original Whisper with same accuracy
- ✅ **~50% less VRAM**: Allows using large-v3 on 6GB GPUs
- ✅ **Pythonic API**: Natural integration with FastAPI async
- ✅ **Distil models support**: `distil-large-v3` for minimum latency

### Negative

- ⚠️ **Additional dependency**: CTranslate2 binary (~100MB)
- ⚠️ **Less portable**: Requires compatible CUDA toolkit
- ⚠️ **Lag on new models**: New OpenAI releases take ~2 weeks to be available

## Alternatives Considered

### whisper.cpp

- **Rejected**: Immature Python bindings, more complex debugging.

### OpenAI Whisper

- **Rejected**: Too slow for real-time experience without enterprise hardware.

### Whisper JAX

- **Rejected**: Requires TPU or complex JAX on CUDA configuration.

## References

- [faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [CTranslate2](https://github.com/OpenNMT/CTranslate2)
- [Whisper Benchmarks](https://github.com/SYSTRAN/faster-whisper#benchmark)
