# ⚙️ Guía de Configuración

> **Ubicación del archivo**: `apps/backend/config.toml` (en tiempo de ejecución se puede buscar en rutas locales).

Voice2Machine expone un sistema de configuración granular para desarrolladores y "power users". Permite ajustar desde la latencia de inferencia hasta la creatividad de la IA.

---

## 1. Transcripción Local (`[whisper]`)

El corazón del sistema. Estos parámetros controlan el modelo **Faster-Whisper**.

| Parámetro | Tipo | Descripción y "Best Practice" 2026 |
| :--- | :--- | :--- |
| `model` | `str` | Modelo a cargar. **Default**: `large-v3-turbo` (SOTA actual en equilibrio velocidad/precisión). Opciones: `distil-large-v3`, `medium`, `base`. |
| `device` | `str` | `cuda` (GPU) es mandatorio para experiencia en tiempo real. `cpu` es funcional pero lento. |
| `compute_type` | `str` | Precisión de tensores. `int8_float16` es el estándar para GPUs modernas (ahorra VRAM sin perder calidad). Usar `int8` para CPU. |
| `beam_size` | `int` | `5` es el estándar de oro. Define cuántas rutas de decodificación explora en paralelo. |
| `best_of` | `int` | `3`. Número de candidatos a generar antes de elegir el mejor. Reduce alucinaciones. |
| `temperature` | `float` | `0.0` (determinístico). Es crucial mantenerlo en 0 para transcripciones fieles. |

### Detección de Voz (`[whisper.vad_parameters]`)

El sistema VAD (Voice Activity Detection) filtra el silencio antes de transcribir, acelerando drásticamente el proceso.

- **`threshold`** (`0.35`): Sensibilidad. Más bajo = detecta susurros, pero puede captar ruido de fondo.
- **`min_speech_duration_ms`** (`250`): Un sonido debe durar al menos 1/4 de segundo para ser considerado voz.
- **`min_silence_duration_ms`** (`600`): Cuánto silencio esperar antes de "cortar" una frase.

---

## 2. Refinado con LLM (`[gemini]` & `[llm]`)

Voice2Machine soporta un enfoque híbrido: Nube (Gemini) o Local (Llama/Qwen).

### Gemini (Nube)
| Parámetro | Default | Notas |
| :--- | :--- | :--- |
| `model` | `gemini-1.5-flash-latest` | Modelo optimizado para baja latencia. |
| `temperature` | `0.3` | Baja creatividad para corrección de estilo. Subir a `0.7` para reescritura creativa. |
| `api_key` | `${GEMINI_API_KEY}` | **Seguridad**: Se inyecta desde variables de entorno. |

### Local LLM (Privacidad Total)
Configuración bajo la sección `[llm.local]`.
- **`model_path`**: Ruta al archivo `.gguf` (ej. `models/qwen2.5-3b-instruct-q4_k_m.gguf`).
- **`n_gpu_layers`**: `-1` para volcar todo a la VRAM (máxima velocidad).

---

## 3. Notificaciones (`[notifications]`)

Controla el feedback visual del sistema (popups de escritorio).

- **`expire_time_ms`** (`3000`): Las notificaciones desaparecen tras 3 segundos.
- **`auto_dismiss`** (`true`): Fuerza el cierre vía DBUS (útil en GNOME/Unity donde las notificaciones a veces se "pegan").

---

## 4. Rutas del Sistema (`[paths]`)

> ⚠️ **Zona de Peligro**: Cambiar esto puede romper la integración con los scripts de bash.

Se definen rutas temporales (`/tmp/v2m_*`) para comunicación entre procesos (IPC) usando archivos como semáforos y buffers. Esto asegura que no queden residuos en el disco duro tras reiniciar.

---

## Secretos (`.env`)

Las claves de API **nunca** deben ir en `config.toml`. Crea un archivo `.env` en la raíz:

```bash
# .env
GEMINI_API_KEY="AIzaSy_TU_CLAVE_AQUI"
```
