# 🔧 Resolución de Problemas (Troubleshooting)

Esta guía recopila los problemas más comunes y sus soluciones. **Regla de Oro**: Siempre revisa los logs primero.

```bash
tail -f /tmp/v2m.log
```

---

## 🛑 Problemas de Audio

### "Grabación iniciada" pero no transcribe nada
*   **Síntoma**: Suena el beep, hablas, suena el beep de fin, pero el portapapeles está vacío o sale error.
*   **Causa**: Dispositivo de entrada muteado o no seleccionado.
*   **Solución**:
    1.  Ejecuta `python scripts/diagnose_audio.py` para ver el vúmetro en consola.
    2.  Revisa la privacidad del micrófono en tu SO.
    3.  Verifica que `ffmpeg` y `pulseaudio-utils` estén instalados.

### Frases cortadas
*   **Causa**: El VAD (Voice Activity Detection) es muy agresivo.
*   **Solución**:
    *   Edita `config.toml`.
    *   Baja `[whisper.vad_parameters] threshold` (ej. a `0.3`).
    *   Sube `min_silence_duration_ms` a `800`.

---

## 🐢 Problemas de Rendimiento

### La transcripción es lenta (>5s para frases cortas)
*   **Causa**: Whisper probablemente está corriendo en **CPU**.
*   **Diagnóstico**: Ejecuta `python scripts/test_whisper_gpu.py`.
*   **Solución**:
    1.  Instala drivers NVIDIA y CUDA Toolkit 12+.
    2.  Asegura `device = "cuda"` en `config.toml`.
    3.  Si *debes* usar CPU, cambia a `model = "base"` y `compute_type = "int8"`.

### `OutOfMemoryError` (OOM)
*   **Causa**: `large-v3-turbo` requiere ~4GB VRAM.
*   **Solución**:
    *   Cambia a modelo `medium`.
    *   Usa `compute_type = "int8_float16"`.

---

## 🤖 Problemas con Gemini / LLM

### "Error de Autenticación"
*   **Solución**:
    1.  Revisa que exista el archivo `.env`.
    2.  Verifica que la variable sea `GEMINI_API_KEY`.
    3.  Regenera la clave en Google AI Studio.

### Mala calidad en el refinado
*   **Solución**:
    *   Baja la `temperature` a `0.1`.
    *   Asegúrate de haber copiado texto antes de lanzar el atajo.

---

## 🖥️ Demonio / Conectividad

### "Connection Refused" (Error de Socket)
*   **Síntoma**: CLI o GUI se quejan de `/tmp/v2m.sock`.
*   **Causa**: El daemon no está corriendo.
*   **Solución**:
    ```bash
    # Inícialo manualmente para ver errores
    python -m v2m.main --daemon
    ```
    Si crashea o dice "address in use":
    ```bash
    pkill -f v2m.main
    rm /tmp/v2m.sock
    ```
