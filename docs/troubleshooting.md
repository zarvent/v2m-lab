# 🔧 Resolución de Problemas (Troubleshooting)

Esta guía recopila los problemas más comunes y sus soluciones. Si encuentras un error que no está aquí, por favor revisa los logs en `/tmp/v2m.log`.

---

## 🛑 Problemas de Audio

### "No se detecta el micrófono" o Grabación vacía
*   **Síntoma**: El sistema dice "Grabación iniciada" pero al detenerse no transcribe nada o da error.
*   **Solución**:
    1.  Verifica que `ffmpeg` y `pactl` estén instalados.
    2.  Asegúrate de que tu micrófono predeterminado en el sistema operativo esté activo y con volumen.
    3.  Ejecuta `arecord -l` para listar dispositivos.

### La transcripción corta frases o palabras
*   **Causa**: El VAD (Voice Activity Detection) puede ser demasiado agresivo.
*   **Solución**:
    1.  Edita `config.toml`.
    2.  En `[whisper.vad_parameters]`, reduce `threshold` (ej. a `0.3`) o aumenta `min_speech_duration_ms`.

---

## 🐢 Problemas de Rendimiento

### La transcripción es muy lenta (>5 segundos para frases cortas)
*   **Causa**: Probablemente Whisper se está ejecutando en la **CPU** en lugar de la **GPU**.
*   **Diagnóstico**: Ejecuta `python scripts/test_whisper_gpu.py`.
*   **Solución**:
    1.  Verifica que tienes drivers NVIDIA y CUDA instalados.
    2.  Reinstala `torch` con soporte CUDA explícito.
    3.  En `config.toml`, asegura `device = "cuda"`.

### `OutOfMemoryError` (OOM) en GPU
*   **Causa**: El modelo `large-v3` es demasiado grande para tu VRAM.
*   **Solución**:
    1.  Cambia el modelo en `config.toml` a `medium` o `small`.
    2.  Cambia `compute_type` a `int8_float16` (híbrido) si tu tarjeta lo soporta.

---

## 🤖 Problemas con Gemini (LLM)

### "Error de autenticación" o "API Key inválida"
*   **Solución**:
    1.  Verifica que el archivo `.env` existe en la raíz.
    2.  Asegúrate de que la variable se llame `GEMINI_API_KEY`.
    3.  Genera una nueva clave en Google AI Studio.

### El texto refinado es peor que el original
*   **Solución**:
    1.  Ajusta el `system_prompt` en `src/v2m/infrastructure/gemini_llm_service.py` (o en `prompts/` si está externalizado).
    2.  Baja la `temperature` en `config.toml` a `0.1` para hacerlo más determinista.

---

## 📜 Logs y Depuración

Para ver qué está pasando en tiempo real:

```bash
# Ver el log en vivo
tail -f /tmp/v2m.log
```

Si reportas un bug, por favor incluye las últimas líneas de este archivo.
