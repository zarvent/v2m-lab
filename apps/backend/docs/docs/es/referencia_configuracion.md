# Referencia de Configuración

Voice2Machine utiliza un sistema de configuración jerárquico y tipado basado en **Pydantic V2**. Esto garantiza que cualquier valor incorrecto en la configuración (ej. un tipo de dato erróneo) detenga el inicio del servicio con un mensaje claro.

## ⚙️ Archivo `config.toml`

La fuente principal de configuración es el archivo `config.toml` ubicado en la raíz del proyecto. Este archivo debe seguir la estructura definida a continuación.

!!! tip "Recarga en Caliente"
    La mayoría de las configuraciones pueden actualizarse en tiempo real mediante el comando IPC `UPDATE_CONFIG` o editando el archivo `config.toml` (requiere reinicio en algunos casos como cambio de modelo VRAM).

---

## 🌍 Variables de Entorno

Cualquier configuración puede ser sobreescrita mediante variables de entorno. El formato es:

`V2M_[SECCION]__[CAMPO]` (Doble guion bajo como separador).

Ejemplo:
*   `config.toml`: `[gemini] api_key = "..."`
*   Env Var: `V2M_GEMINI__API_KEY="AIzaSy..."`

---

## 📝 Secciones de Configuración

### 1. `[paths]`
Rutas del sistema y archivos temporales.

| Campo | Tipo | Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `recording_flag` | Path | `$RUNTIME/v2m_recording.pid` | Archivo bandera que indica grabación activa. |
| `audio_file` | Path | `$RUNTIME/v2m_audio.wav` | Archivo temporal donde se guarda el audio grabado. |
| `log_file` | Path | `$RUNTIME/v2m_debug.log` | Archivo de logs para depuración. |

### 2. `[transcription]`
Configuración del motor de transcripción principal.

#### `[transcription.whisper]`
Parámetros para el motor Faster-Whisper.

| Campo | Tipo | Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `model` | str | `"large-v2"` | Modelo Whisper (`tiny`, `base`, `small`, `medium`, `large-v2`, `large-v3`). |
| `language` | str | `"es"` | Código ISO del idioma (o `"auto"`). |
| `device` | str | `"cuda"` | Dispositivo de cómputo (`cuda` o `cpu`). |
| `compute_type` | str | `"int8_float16"` | Precisión (`float16`, `int8`). Afecta uso de VRAM. |
| `vad_filter` | bool | `true` | Si activar el filtro de voz (VAD) interno de Whisper. |
| `keep_warm` | bool | `true` | Mantener el modelo en VRAM tras la transcripción. |

#### `[transcription.whisper.vad_parameters]`
Ajuste fino del detector de voz.

| Campo | Tipo | Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `threshold` | float | `0.3` | Sensibilidad (0.0 a 1.0). Mayor = menos sensible al ruido. |
| `min_speech_duration_ms` | int | `250` | Mínima duración para considerar habla. |

### 3. `[llm]`
Configuración general de Modelos de Lenguaje.

| Campo | Tipo | Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `backend` | enum | `"local"` | Motor a usar: `"local"`, `"gemini"`, o `"ollama"`. |

#### `[llm.local]` (Llama.cpp)
| Campo | Tipo | Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `model_path` | Path | `models/...gguf` | Ruta relativa al archivo GGUF del modelo. |
| `n_gpu_layers` | int | `-1` | Capas a descargar a GPU (-1 = todas). |
| `n_ctx` | int | `2048` | Ventana de contexto. |

#### `[llm.ollama]`
| Campo | Tipo | Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `host` | str | `"http://localhost:11434"` | URL del servidor Ollama. |
| `model` | str | `"gemma2:2b"` | Nombre del modelo a solicitar. |
| `keep_alive` | str | `"5m"` | Tiempo para mantener el modelo cargado. |

### 4. `[gemini]` (Google AI)
Requiere API Key válida.

| Campo | Tipo | Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `api_key` | str | `null` | Clave de API de Google AI Studio. |
| `model` | str | `"gemini-1.5-flash..."` | Identificador del modelo. |
| `temperature` | float | `0.3` | Creatividad de la respuesta. |

### 5. `[notifications]`
Comportamiento de las notificaciones de escritorio.

| Campo | Tipo | Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `expire_time_ms` | int | `3000` | Tiempo en pantalla (ms). |
| `auto_dismiss` | bool | `true` | Cerrar automáticamente. |

---

## 📄 Ejemplo Completo (`config.toml`)

```toml
[transcription.whisper]
model = "large-v3-turbo"
language = "es"
compute_type = "float16"

[transcription.whisper.vad_parameters]
threshold = 0.4

[llm]
backend = "ollama"

[llm.ollama]
model = "llama3.2"
keep_alive = "10m"

[notifications]
expire_time_ms = 5000
```
