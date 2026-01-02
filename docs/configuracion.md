# ⚙️ Guía de Configuración

**Voice2Machine** es altamente configurable a través del archivo `config.toml` ubicado en la raíz del proyecto. Este archivo permite ajustar el comportamiento de los modelos de IA, las rutas del sistema y los parámetros de grabación.

---

## Estructura de `config.toml`

El archivo se divide en secciones lógicas. A continuación se explica cada parámetro en detalle.

### `[paths]`

Define las rutas críticas para el funcionamiento del sistema.

| Parámetro        | Descripción                                                               | Valor por Defecto                              |
| :--------------- | :------------------------------------------------------------------------ | :--------------------------------------------- |
| `recording_flag` | Archivo temporal usado como semáforo para indicar si se está grabando.    | `/tmp/v2m_recording.pid`                       |
| `audio_file`     | Ruta donde se guarda temporalmente el audio grabado antes de transcribir. | `/tmp/v2m_audio.wav`                           |
| `log_file`       | Ruta del archivo de logs para depuración.                                 | `/tmp/v2m.log`                                 |
| `venv_path`      | Ruta al entorno virtual de Python.                                        | Auto-detectado: `<proyecto>/apps/backend/venv` |

### `[whisper]`

Configuración del motor de transcripción local (Whisper).

| Parámetro      | Descripción                                                                             | Recomendación                                                          |
| :------------- | :-------------------------------------------------------------------------------------- | :--------------------------------------------------------------------- |
| `model`        | El tamaño del modelo Whisper a usar.                                                    | `large-v3-turbo` (mejor calidad), `medium` (balance), `base` (rápido). |
| `device`       | Dispositivo de cómputo.                                                                 | `cuda` (GPU NVIDIA), `cpu` (Lento).                                    |
| `compute_type` | Precisión de los cálculos.                                                              | `float16` (GPU), `int8` (CPU).                                         |
| `beam_size`    | Tamaño del haz para la búsqueda de decodificación. Mayor es más preciso pero más lento. | `3` - `5`                                                              |
| `vad_filter`   | Activa el filtro de detección de actividad de voz (VAD) interno de Whisper.             | `true`                                                                 |

### `[whisper.vad_parameters]`

Ajuste fino del VAD (Voice Activity Detection) para truncar silencios.

- `threshold`: Umbral de probabilidad para considerar un segmento como voz (0.5).
- `min_speech_duration_ms`: Duración mínima para considerar voz (250ms).

### `[gemini]`

Configuración para el servicio de refinado de texto con Google Gemini.

| Parámetro     | Descripción                                                                             |
| :------------ | :-------------------------------------------------------------------------------------- |
| `model`       | Identificador del modelo de Gemini.                                                     |
| `temperature` | Creatividad del modelo (0.0 - 1.0). Para corrección de texto, usar valores bajos (0.3). |
| `max_tokens`  | Límite de tokens para la respuesta.                                                     |
| `api_key`     | **NO EDITAR**. Se lee automáticamente de la variable de entorno `${GEMINI_API_KEY}`.    |

---

## Variables de Entorno (`.env`)

Por seguridad, las credenciales sensibles no van en `config.toml`, sino en un archivo `.env` que no se comparte en el repositorio.

```ini
# .env
GEMINI_API_KEY="AIzaSy..."
```
