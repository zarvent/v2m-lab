---
title: Guía de Configuración
description: Instrucciones detalladas para configurar los servicios de transcripción y LLM.
ai_context: "Configuración, TOML, Whisper, Gemini, Ollama"
depends_on: []
status: stable
---

# ⚙️ Guía de Configuración

!!! info "Gestión de Configuración"
La configuración se gestiona principalmente a través de la interfaz gráfica del Frontend (Icono de engranaje ⚙️). Sin embargo, los usuarios avanzados pueden editar directamente el archivo `config.toml`.

> **Ubicación del archivo**: `$XDG_CONFIG_HOME/v2m/config.toml` (usualmente `~/.config/v2m/config.toml`).

---

## 1. Transcripción Local (`[transcription]`)

El corazón del sistema. Estos parámetros controlan el motor **Faster-Whisper**.

| Parámetro            | Tipo   | Default           | Descripción y "Best Practice" 2026                                                                                    |
| :------------------- | :----- | :---------------- | :-------------------------------------------------------------------------------------------------------------------- |
| `model`              | `str`  | `distil-large-v3` | Modelo a cargar. `distil-large-v3` ofrece velocidad extrema con precisión SOTA. Opciones: `large-v3-turbo`, `medium`. |
| `device`             | `str`  | `cuda`            | `cuda` (GPU NVIDIA) es mandatorio para experiencia en tiempo real. `cpu` es funcional pero no recomendado.            |
| `compute_type`       | `str`  | `float16`         | Precisión de tensores. `float16` o `int8_float16` optimizan VRAM y throughput en GPUs modernas.                       |
| `use_faster_whisper` | `bool` | `true`            | Habilita el backend optimizado CTranslate2.                                                                           |

### Detección de Voz (VAD)

El sistema utiliza **Silero VAD** (versión Rust en `v2m_engine`) para filtrar silencio antes de invocar a Whisper, ahorrando GPU.

- **`vad_filter`** (`true`): Activa el pre-filtrado.
- **`vad_parameters`**: Ajuste fino de sensibilidad (umbral de silencio, duración mínima de voz).

---

## 2. Servicios LLM (`[llm]`)

Voice2Machine implementa un patrón de **Proveedor** para soportar múltiples backends de IA para el refinado de texto.

### Configuración Global

| Parámetro  | Descripción                                                          |
| :--------- | :------------------------------------------------------------------- |
| `provider` | Proveedor activo: `gemini` (Nube) u `ollama` (Local).                |
| `model`    | Nombre del modelo específico (ej. `gemini-1.5-flash` o `llama3:8b`). |

### Proveedores Específicos

#### Google Gemini (`provider = "gemini"`)

Requiere API Key. Ideal para usuarios sin GPU potente (VRAM < 8GB).

- **Modelo recomendado**: `gemini-1.5-flash-latest` (latencia mínima).
- **Temperatura**: `0.3` (conservador) para corrección gramatical.

#### Ollama (`provider = "ollama"`)

Privacidad total. Requiere correr el servidor de Ollama (`ollama serve`).

- **Endpoint**: `http://localhost:11434`
- **Modelo recomendado**: `qwen2.5:7b` o `llama3.1:8b`.

---

## 3. Grabación (`[recording]`)

Controla la captura de audio mediante `SoundDevice` y `v2m_engine`.

- **`sample_rate`**: `16000` (Fijo, requerido por Whisper).
- **`channels`**: `1` (Mono).
- **`device_index`**: ID del micrófono. Si es `null`, usa el default del sistema (PulseAudio/PipeWire).

---

## 4. Sistema (`[system]`)

Configuración de bajo nivel para el Daemon y comunicación.

- **`host`**: Host del servidor (`127.0.0.1` para acceso solo local).
- **`port`**: Puerto HTTP (`8765` por defecto).
- **`log_level`**: `INFO` por defecto. Cambiar a `DEBUG` para diagnósticos profundos.

---

## Secretos y Seguridad

Las claves de API se gestionan mediante variables de entorno o almacenamiento seguro, nunca en texto plano dentro de `config.toml` si es posible.

```bash
# Definir en .env o entorno del sistema
export GEMINI_API_KEY="AIzaSy_TU_CLAVE_AQUI"
```

!!! warning "Importante"
Reinicia el demonio (usando `scripts/operations/daemon/restart_daemon.sh`) después de editar manualmente el archivo de configuración para aplicar los cambios.
