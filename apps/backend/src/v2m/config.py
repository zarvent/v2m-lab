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

Provee un sistema de configuración tipado utilizando Pydantic Settings.
Soporta: Argumentos, ENV, .env, config.toml y Defaults.
"""

from pathlib import Path
from typing import Literal
import re

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from v2m.utils.paths import get_secure_runtime_dir

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RUNTIME_DIR = get_secure_runtime_dir()


class PathsConfig(BaseModel):
    """Rutas del sistema y archivos temporales."""
    recording_flag: Path = Field(default=RUNTIME_DIR / "v2m_recording.pid")
    audio_file: Path = Field(default=RUNTIME_DIR / "v2m_audio.wav")
    log_file: Path = Field(default=RUNTIME_DIR / "v2m_debug.log")
    venv_path: Path = Field(default=BASE_DIR / "venv")


class VadParametersConfig(BaseModel):
    """Parámetros para la Detección de Actividad de Voz (VAD)."""
    threshold: float = 0.3
    min_speech_duration_ms: int = 250
    min_silence_duration_ms: int = 500


class WhisperConfig(BaseModel):
    """
    Configuración del modelo de transcripción Whisper.

    Defaults optimizados para 2026:
    - Model: distil-large-v3 (6x más rápido que large-v2, precisión similar).
    - Compute: float16 (GPU) o int8 (CPU).
    """
    model: str = "distil-large-v3"
    language: str = "es"
    device: str = "cuda"
    compute_type: str = "float16"
    device_index: int = 0
    num_workers: int = 4
    beam_size: int = 2
    best_of: int = 2
    temperature: float | list[float] = 0.0
    vad_filter: bool = True
    audio_device_index: int | None = None
    vad_parameters: VadParametersConfig = Field(default_factory=VadParametersConfig)


class GeminiConfig(BaseModel):
    """Configuración del servicio LLM Google Gemini."""
    model: str = "models/gemini-1.5-flash-latest"
    temperature: float = 0.3
    max_tokens: int = 2048
    max_input_chars: int = 6000
    request_timeout: int = 30
    retry_attempts: int = 3
    retry_min_wait: int = 2
    retry_max_wait: int = 10
    translation_temperature: float = 0.3
    api_key: SecretStr | None = Field(default=None)


class NotificationsConfig(BaseModel):
    """Configuración de notificaciones de escritorio."""
    expire_time_ms: int = Field(default=3000, ge=500, le=30000)
    auto_dismiss: bool = Field(default=True)


class LocalLLMConfig(BaseModel):
    """Configuración para LLM local usando llama.cpp."""
    model_path: Path = Field(default=Path("models/qwen2.5-3b-instruct-q4_k_m.gguf"))
    n_gpu_layers: int = Field(default=-1)
    n_ctx: int = Field(default=2048, ge=512, le=32768)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    translation_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=4096)


class OllamaConfig(BaseModel):
    """Configuración para backend LLM Ollama."""
    host: str = Field(default="http://localhost:11434")
    model: str = Field(default="gemma2:2b")
    keep_alive: str = Field(default="5m")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    translation_temperature: float = Field(default=0.3, ge=0.0, le=2.0)

    @field_validator("keep_alive")
    @classmethod
    def validate_keep_alive(cls, v: str) -> str:
        if v == "-1" or re.match(r"^\d+[msdh]$", v):
            return v
        raise ValueError("keep_alive debe ser formato duración (ej: 5m, 1h) o -1")


class LLMConfig(BaseModel):
    """Selector de backend y configuración de LLM."""
    backend: Literal["local", "gemini", "ollama"] = Field(default="local")
    local: LocalLLMConfig = Field(default_factory=LocalLLMConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)


class TranscriptionConfig(BaseModel):
    """Configuración del Servicio de Transcripción."""
    backend: str = Field(default="whisper")
    whisper: WhisperConfig = Field(default_factory=WhisperConfig)
    lazy_load: bool = Field(default=False)


class Settings(BaseSettings):
    """
    Configuración Principal de la Aplicación.
    Combina rutas, transcripción, LLM y notificaciones.
    """
    paths: PathsConfig = Field(default_factory=PathsConfig)
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
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )


config = Settings()
