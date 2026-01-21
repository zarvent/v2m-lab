# ADR-005: Motor de Audio en Rust (v2m_engine)

## Estado

Aceptada

## Fecha

2025-01-10

## Contexto

La captura de audio en Python puro presentaba limitaciones críticas para una experiencia de dictado real-time:

### Problemas identificados:

1. **GIL blocking**: La captura de audio competía con transcripción por el GIL
2. **Latencia variable**: Jitter de 10-50ms en buffering de audio
3. **Overhead de sounddevice**: Callbacks Python añadían latencia
4. **VAD ineficiente**: Silero VAD en Python procesaba samples con overhead

### Requisitos:

- Latencia de captura < 10ms
- VAD pre-procesado antes de Python
- Buffer circular lock-free
- Zero-copy cuando sea posible

## Decisión

**Desarrollar extensión nativa en Rust** (`v2m_engine`) para tareas críticas de audio.

### Componentes:

```
v2m_engine/
├── src/
│   ├── audio_capture.rs  # CPAL-based capture
│   ├── ring_buffer.rs    # Lock-free circular buffer
│   ├── vad.rs            # Silero ONNX inference
│   └── lib.rs            # PyO3 bindings
```

### Interfaz Python:

```python
from v2m_engine import AudioCapture, VADProcessor

capture = AudioCapture(sample_rate=16000, buffer_size=4096)
vad = VADProcessor(threshold=0.5)

async with capture.stream() as audio:
    if vad.contains_speech(audio):
        await transcriber.process(audio)
```

## Consecuencias

### Positivas

- ✅ **Latencia < 5ms**: CPAL + lock-free buffers
- ✅ **GIL-free**: Audio thread independiente de Python
- ✅ **VAD eficiente**: ONNX runtime nativo, 10x más rápido
- ✅ **Zero-copy**: NumPy arrays comparten memoria con Rust

### Negativas

- ⚠️ **Complejidad de build**: Requiere Rust toolchain + maturin
- ⚠️ **Debugging cross-language**: Stack traces mixtos Python/Rust
- ⚠️ **Portabilidad**: Binarios específicos por plataforma

## Alternativas Consideradas

### Pure Python (sounddevice + numpy)

- **Rechazado**: GIL blocking y latencia inaceptable.

### Cython

- **Rechazado**: Todavía atado al GIL, beneficios limitados.

### C++ Extension

- **Rechazado**: Rust ofrece memory safety sin GC, mejor tooling (cargo).

## Referencias

- [PyO3 - Rust bindings for Python](https://pyo3.rs/)
- [CPAL - Cross-platform Audio Library](https://github.com/RustAudio/cpal)
- [Lock-free Ring Buffer](https://github.com/agerasev/ringbuf)
