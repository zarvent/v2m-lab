# This file is part of voice2machine.
#
# voice2machine is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# voice2machine is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with voice2machine.  If not, see <https://www.gnu.org/licenses/>.

"""
Módulo de Configuración de la Aplicación.

Provee un sistema de configuración robusto y tipado utilizando Pydantic Settings.
Soporta múltiples fuentes de configuración con la siguiente prioridad (de mayor a menor):

1. Argumentos de inicialización
2. Variables de entorno
3. Archivo .env
4. Archivo config.toml
5. Valores por defecto

La configuración está organizada en secciones lógicas:
- `PathsConfig`: Rutas del sistema y archivos temporales.
- `TranscriptionConfig`: Configuración del backend de transcripción (ej. Whisper).
- `GeminiConfig`: Configuración del servicio LLM Google Gemini.
- `LLMConfig`: Configuración general de LLM (Local vs Nube).
- `NotificationsConfig`: Ajustes de notificaciones de escritorio.

Ejemplo:
    Acceder a la configuración desde cualquier parte de la aplicación:

    ```python
    from v2m.config import config

    # Acceder a la configuración de Whisper
    model = config.transcription.whisper.model
    device = config.transcription.whisper.device

    # Acceder a rutas
    audio_file = config.paths.audio_file
    ```

Notas:
    - El archivo `config.toml` debe estar en la raíz del proyecto.
    - Las variables de entorno se prefijan automáticamente con el nombre de la sección.
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from v2m.utils.paths import get_secure_runtime_dir

# --- Ruta Base del Proyecto ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- Directorio Seguro de Ejecución ---
RUNTIME_DIR = get_secure_runtime_dir()


class PathsConfig(BaseModel):
    """
    Configuración para rutas de archivos y directorios.

    Atributos:
        recording_flag: Ruta al archivo PID que indica grabación activa.
        audio_file: Ruta al archivo WAV temporal para audio grabado.
        log_file: Ruta al archivo de log para depuración.
        venv_path: Ruta al entorno virtual de Python.
    """

    recording_flag: Path = Field(default=RUNTIME_DIR / "v2m_recording.pid")
    audio_file: Path = Field(default=RUNTIME_DIR / "v2m_audio.wav")
    log_file: Path = Field(default=RUNTIME_DIR / "v2m_debug.log")
    venv_path: Path = Field(default=BASE_DIR / "venv")


class VadParametersConfig(BaseModel):
    """
    Parámetros para la Detección de Actividad de Voz (VAD).

    El VAD filtra segmentos de silencio antes de la transcripción para mejorar la eficiencia
    y reducir alucinaciones del modelo.

    Atributos:
        threshold: Umbral de probabilidad (0.0 a 1.0) para clasificar un segmento como habla.
            Defecto: 0.3
        min_speech_duration_ms: Duración mínima (ms) para ser considerado habla.
            Defecto: 250ms
        min_silence_duration_ms: Duración mínima de silencio (ms) para considerar que el habla terminó.
            Defecto: 500ms
    """

    threshold: float = 0.3
    min_speech_duration_ms: int = 250
    min_silence_duration_ms: int = 500


class WhisperConfig(BaseModel):
    """
    Configuración del modelo de transcripción Whisper.

    Atributos:
        model: Nombre o ruta del modelo Whisper (ej. 'tiny', 'base', 'large-v3').
            Defecto: 'large-v2'
        language: Código de idioma ISO 639-1 (ej. 'es', 'en') o 'auto'.
            Defecto: 'es'
        device: Dispositivo de cómputo ('cuda' para GPU, 'cpu').
            Defecto: 'cuda'
        compute_type: Precisión numérica ('float16', 'int8_float16', 'int8').
            Defecto: 'int8_float16'
        device_index: Índice de GPU a utilizar. Defecto: 0
        num_workers: Número de workers para procesamiento paralelo. Defecto: 4
        beam_size: Tamaño del beam search. Defecto: 2
        best_of: Número de candidatos a considerar. Defecto: 2
        temperature: Temperatura de muestreo (0.0 para determinístico).
            Defecto: 0.0
        vad_filter: Activar filtrado VAD. Defecto: True
        vad_parameters: Configuración detallada del VAD.
        audio_device_index: Índice del dispositivo de entrada de audio (None para defecto).
    """

    model: str = "large-v2"
    language: str = "es"
    device: str = "cuda"
    compute_type: str = "int8_float16"
    device_index: int = 0
    num_workers: int = 4
    beam_size: int = 2
    best_of: int = 2
    temperature: float | list[float] = 0.0
    vad_filter: bool = True
    audio_device_index: int | None = None
    vad_parameters: VadParametersConfig = Field(default_factory=VadParametersConfig)


class GeminiConfig(BaseModel):
    """
    Configuración del servicio LLM Google Gemini.

    Atributos:
        model: Identificador del modelo Gemini (ej. 'models/gemini-1.5-flash-latest').
        temperature: Temperatura de generación (0.0 a 2.0). Defecto: 0.3
        max_tokens: Máximo de tokens a generar. Defecto: 2048
        max_input_chars: Límite de caracteres de entrada. Defecto: 6000
        request_timeout: Tiempo de espera de solicitud HTTP en segundos. Defecto: 30
        retry_attempts: Número de reintentos automáticos. Defecto: 3
        retry_min_wait: Espera mínima entre reintentos (segundos). Defecto: 2
        retry_max_wait: Espera máxima entre reintentos (segundos). Defecto: 10
        api_key: Clave de API para Google Cloud (configurar vía variable de entorno GEMINI_API_KEY).
    """

    model: str = "models/gemini-1.5-flash-latest"
    temperature: float = 0.3
    max_tokens: int = 2048
    max_input_chars: int = 6000
    request_timeout: int = 30
    retry_attempts: int = 3
    retry_min_wait: int = 2
    retry_max_wait: int = 10
    translation_temperature: float = 0.3
    api_key: str | None = Field(default=None)


class NotificationsConfig(BaseModel):
    """
    Configuración de notificaciones de escritorio.

    Atributos:
        expire_time_ms: Tiempo en ms antes del cierre automático. Defecto: 3000
        auto_dismiss: Forzar cierre programático. Defecto: True
    """

    expire_time_ms: int = Field(default=3000, ge=500, le=30000)
    auto_dismiss: bool = Field(default=True)


class LocalLLMConfig(BaseModel):
    """
    Configuración para LLM local usando llama.cpp.

    Atributos:
        model_path: Ruta al archivo del modelo GGUF.
        n_gpu_layers: Número de capas para descargar a la GPU (-1 para todas).
        n_ctx: Tamaño de la ventana de contexto. Defecto: 2048
        temperature: Temperatura de generación. Defecto: 0.3
        max_tokens: Máximo de tokens a generar. Defecto: 512
    """

    model_path: Path = Field(default=Path("models/qwen2.5-3b-instruct-q4_k_m.gguf"))
    n_gpu_layers: int = Field(default=-1)
    n_ctx: int = Field(default=2048, ge=512, le=32768)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    translation_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=4096)


class OllamaConfig(BaseModel):
    """
    Configuración para backend LLM Ollama (SOTA 2026).

    Atributos:
        host: URL del servidor Ollama. Defecto: http://localhost:11434
        model: Nombre del modelo (gemma2:2b, phi3.5-mini, qwen2.5-coder:7b).
        keep_alive: Tiempo para mantener el modelo cargado. "0m" libera VRAM inmediatamente.
        temperature: Temperatura de generación. 0.0 para salidas estructuradas determinísticas.
        translation_temperature: Temperatura para tareas de traducción.
    """

    host: str = Field(default="http://localhost:11434")
    model: str = Field(default="gemma2:2b")
    keep_alive: str = Field(default="5m")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    translation_temperature: float = Field(default=0.3, ge=0.0, le=2.0)


class LLMConfig(BaseModel):
    """
    Configuración del Servicio LLM.

    Atributos:
        backend: Selector de backend ("local", "gemini" u "ollama"). Defecto: "local"
        local: Configuración para el backend local llama.cpp.
        ollama: Configuración para el backend Ollama.
    """

    backend: Literal["local", "gemini", "ollama"] = Field(default="local")
    local: LocalLLMConfig = Field(default_factory=LocalLLMConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)


class TranscriptionConfig(BaseModel):
    """
    Configuración del Servicio de Transcripción.

    Atributos:
        backend: Selector de backend ("whisper"). Defecto: "whisper"
        whisper: Configuración para el backend Whisper.
    """

    backend: str = Field(default="whisper")
    whisper: WhisperConfig = Field(default_factory=WhisperConfig)


class Settings(BaseSettings):
    """
    Configuración Principal de la Aplicación.

    Agrega todas las secciones de configuración utilizando Pydantic Settings.

    Atributos:
        paths: Configuración de rutas.
        transcription: Configuración de transcripción.
        gemini: Configuración de Gemini LLM.
        notifications: Configuración de notificaciones.
        llm: Configuración de LLM.
    """

    paths: PathsConfig = Field(default_factory=PathsConfig)
    # whisper field removed in favor of transcription.whisper
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    transcription: TranscriptionConfig = Field(default_factory=TranscriptionConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        toml_file=BASE_DIR / "config.toml",
        frozen=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        Personaliza la prioridad de las fuentes de configuración.
        """
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )


config = Settings()
