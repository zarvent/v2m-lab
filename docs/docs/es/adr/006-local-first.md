# ADR-006: Local-first: Procesamiento sin Cloud

## Estado

Aceptada

## Fecha

2024-03-01

## Contexto

Los servicios de dictado existentes (Google Speech-to-Text, Whisper API, Dragon) requieren enviar audio a servidores externos.

### Problemas con cloud-based dictation:

1. **Privacidad**: Audio sensible (médico, legal, personal) sale de la máquina
2. **Latencia de red**: 100-500ms RTT adicionales
3. **Disponibilidad**: Requiere conexión a internet
4. **Costos**: APIs de transcripción cobran por minuto
5. **Rate limits**: Throttling en uso intensivo

### Requisitos del usuario:

- **Privacidad absoluta**: Ningún dato debe salir de la máquina
- **Funcionamiento offline**: El sistema debe operar sin internet
- **Latencia mínima**: < 500ms end-to-end
- **Costo cero**: Sin suscripciones ni pagos por uso

## Decisión

**Adoptar filosofía "Local-first"** donde todo el procesamiento de voz ocurre en el dispositivo del usuario.

### Implementación:

| Componente     | Solución Local                                |
| -------------- | --------------------------------------------- |
| Transcripción  | faster-whisper en GPU local                   |
| LLM (opcional) | Ollama con modelos locales                    |
| Audio          | Procesado en memoria RAM                      |
| Almacenamiento | Solo archivos temporales, eliminados post-uso |

### Excepciones configurables:

El usuario puede **optar-in** a servicios cloud para el refinamiento de texto:

- Google Gemini API (para LLM)
- Pero **nunca** para el audio crudo

## Consecuencias

### Positivas

- ✅ **Privacidad garantizada**: Audio nunca sale del dispositivo
- ✅ **Sin latencia de red**: Todo procesamiento local
- ✅ **Funciona offline**: No requiere internet para dictar
- ✅ **Costo predecible**: Solo hardware (GPU), sin suscripciones
- ✅ **Compliance**: Compatible con regulaciones (HIPAA, GDPR)

### Negativas

- ⚠️ **Requiere GPU**: Sin GPU NVIDIA, rendimiento degradado
- ⚠️ **Modelos locales LLM**: Calidad inferior a GPT-4/Gemini Pro
- ⚠️ **Actualizaciones manuales**: Modelos no se auto-actualizan

## Alternativas Consideradas

### Hybrid (local STT + cloud LLM default)

- **Rechazado**: Viola principio de privacidad-por-defecto.

### Cloud-first con cache local

- **Rechazado**: Complejidad innecesaria, audio aún debe subirse.

### Federated Learning

- **Rechazado**: Sobre-ingeniería para el scope actual.

## Referencias

- [Local-first Software](https://www.inkandswitch.com/local-first/)
- [Ink & Switch - Seven Ideals](https://www.inkandswitch.com/local-first/#seven-ideals)
- [GDPR and Voice Data](https://gdpr.eu/voice-recognition/)
