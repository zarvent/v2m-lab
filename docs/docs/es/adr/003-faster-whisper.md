# ADR-003: Selección de faster-whisper sobre whisper.cpp

## Estado

Aceptada

## Fecha

2024-06-01

## Contexto

Para la transcripción de voz local, necesitábamos elegir una implementación del modelo Whisper de OpenAI que maximizara rendimiento en GPUs NVIDIA consumer (RTX 3060-4090).

### Opciones evaluadas:

1. **OpenAI Whisper (original)**: Implementación de referencia en PyTorch
2. **whisper.cpp**: Implementación en C++ puro con soporte CUDA
3. **faster-whisper**: Implementación sobre CTranslate2 (C++/CUDA optimizado)

### Requisitos:

- Latencia < 500ms para 5 segundos de audio (8x real-time mínimo)
- Soporte para modelos `large-v3` y variantes `distil`
- Cuantización INT8/FP16 para optimizar VRAM
- API Python para integración con el backend
- Streaming/chunking de audio

## Decisión

**Adoptar faster-whisper** como motor de transcripción principal.

### Justificación:

| Criterio            | Whisper (PyTorch) | whisper.cpp | faster-whisper   |
| ------------------- | ----------------- | ----------- | ---------------- |
| **Velocidad**       | 1x (baseline)     | 4x          | 4-8x             |
| **VRAM (large-v3)** | 10GB              | 6GB         | 4-5GB            |
| **Python API**      | ✅ Nativa         | ❌ Bindings | ✅ Excelente     |
| **Cuantización**    | Limited           | ✅          | ✅ INT8/FP16     |
| **Mantenimiento**   | OpenAI            | Comunidad   | Activo (Systran) |

## Consecuencias

### Positivas

- ✅ **4-8x más rápido** que Whisper original con misma precisión
- ✅ **~50% menos VRAM**: Permite usar large-v3 en GPUs de 6GB
- ✅ **API Pythonica**: Integración natural con FastAPI async
- ✅ **Soporte distil models**: `distil-large-v3` para latencia mínima

### Negativas

- ⚠️ **Dependencia adicional**: CTranslate2 binario (~100MB)
- ⚠️ **Menos portable**: Requiere CUDA toolkit compatible
- ⚠️ **Lag en nuevos modelos**: Nuevos releases de OpenAI tardan ~2 semanas en estar disponibles

## Alternativas Consideradas

### whisper.cpp

- **Rechazado**: Bindings Python inmaduros, debugging más complejo.

### OpenAI Whisper

- **Rechazado**: Demasiado lento para experiencia real-time sin hardware enterprise.

### Whisper JAX

- **Rechazado**: Requiere TPU o configuración compleja de JAX en CUDA.

## Referencias

- [faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [CTranslate2](https://github.com/OpenNMT/CTranslate2)
- [Whisper Benchmarks](https://github.com/SYSTRAN/faster-whisper#benchmark)
