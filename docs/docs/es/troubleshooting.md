# 🔧 Solución de Problemas (Troubleshooting)

!!! danger "Regla de Oro"
    Ante cualquier problema, el primer paso siempre es consultar los logs del sistema.
    ```bash
    # Ver logs en tiempo real
    tail -f ~/.local/state/v2m/v2m.log
    ```

---

## 🛑 Audio y Grabación

### No se escucha nada / Transcripción vacía
*   **Síntoma**: La grabación inicia y termina, pero no se genera texto.
*   **Diagnóstico**:
    Ejecuta el script de diagnóstico de audio:
    ```bash
    python scripts/diagnose_audio.py
    ```
*   **Soluciones**:
    1.  **Driver de Audio**: Voice2Machine usa `SoundDevice`. Asegúrate de que tu sistema (PulseAudio/PipeWire) tenga un micrófono predeterminado activo.
    2.  **Permisos**: En Linux, tu usuario debe pertenecer al grupo `audio` (`sudo usermod -aG audio $USER`).

### Frases cortadas o incompletas
*   **Causa**: El detector de silencio (VAD) es demasiado agresivo.
*   **Solución**:
    Ajusta la configuración en `config.toml` o desde la GUI:
    - Reduce el `threshold` (ej. de `0.35` a `0.30`).
    - Aumenta el `min_silence_duration_ms` (ej. a `800ms`).

---

## 🐢 Rendimiento y GPU

### Transcripción lenta (> 2 segundos)
*   **Causa Probable**: Whisper está ejecutándose en **CPU** en lugar de GPU.
*   **Verificación**:
    ```bash
    python scripts/test_whisper_gpu.py
    ```
*   **Solución**:
    1.  Instala drivers NVIDIA actualizados (compatible con CUDA 12).
    2.  Verifica que `config.toml` tenga `device = "cuda"`.
    3.  Si no tienes GPU dedicada, cambia el modelo a `distil-medium.en` o `base`.

### Error `CUDA out of memory`
*   **Causa**: Tu GPU no tiene suficiente VRAM para el modelo seleccionado.
*   **Solución**:
    - Cambia `compute_type` a `int8_float16` (reduce uso de VRAM a la mitad).
    - Usa un modelo más ligero (`distil-large-v3` consume menos que `large-v3` original).

---

## 🔌 Conectividad y Demonio

### "Daemon disconnected" en GUI o Scripts
*   **Causa**: El proceso backend (Python) no está corriendo o el socket se corrompió.
*   **Solución**:
    1.  Verifica el estado:
        ```bash
        pgrep -a python | grep v2m
        ```
    2.  Si no corre, inícialo manualmente para ver errores de arranque:
        ```bash
        python -m v2m.main --daemon
        ```
    3.  Si dice "Address already in use", limpia el socket huérfano:
        ```bash
        rm /tmp/v2m.sock
        ```

### Atajos de teclado no responden
*   **Causa**: Problema de permisos o ruta incorrecta en la configuración del gestor de ventanas.
*   **Solución**:
    - Ejecuta el script manualmente en terminal: `scripts/v2m-toggle.sh`.
    - Si funciona, el error está en tu configuración de atajos (ej. ruta relativa `~/` en lugar de `/home/...`).
    - Si no funciona, verifica permisos: `chmod +x scripts/*.sh`.

---

## 🧠 Errores de IA (LLM)

### Error 401/403 con Gemini
*   **Causa**: API Key inválida o expirada.
*   **Solución**: Regenera tu clave en Google AI Studio y actualiza el archivo `.env` o la variable de entorno `GEMINI_API_KEY`.

### "Connection refused" con Ollama
*   **Causa**: El servidor de Ollama no está corriendo.
*   **Solución**: Ejecuta `ollama serve` en otra terminal.
