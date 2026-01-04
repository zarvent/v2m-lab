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
Application Configuration Module.

This module provides a robust and typed configuration system using Pydantic Settings.
It supports multiple configuration sources with the following priority (highest to lowest):

1. Initialization arguments
2. Environment variables
3. .env file
4. config.toml file
5. Default values

Configuration is organized into logical sections:
- `PathsConfig`: System and temporary file paths.
- `TranscriptionConfig`: Transcription backend configuration (e.g., Whisper).
- `GeminiConfig`: Google Gemini LLM service configuration.
- `LLMConfig`: General LLM configuration (Local vs Cloud).
- `NotificationsConfig`: Desktop notification settings.

Example:
    Access configuration from anywhere in the application:

    ```python
    from v2m.config import config

    # Access Whisper configuration
    model = config.transcription.whisper.model
    device = config.transcription.whisper.device

    # Access paths
    audio_file = config.paths.audio_file
    ```

Notes:
    - The `config.toml` file must be in the project root.
    - Environment variables are automatically prefixed with the section name.
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

# --- Project Base Path ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- Secure Runtime Directory ---
RUNTIME_DIR = get_secure_runtime_dir()


class PathsConfig(BaseModel):
    """
    Configuration for file paths and directories.

    Attributes:
        recording_flag: Path to the PID file indicating active recording.
        audio_file: Path to the temporary WAV file for recorded audio.
        log_file: Path to the log file for debugging.
        venv_path: Path to the Python virtual environment.
    """

    recording_flag: Path = Field(default=RUNTIME_DIR / "v2m_recording.pid")
    audio_file: Path = Field(default=RUNTIME_DIR / "v2m_audio.wav")
    log_file: Path = Field(default=RUNTIME_DIR / "v2m_debug.log")
    venv_path: Path = Field(default=BASE_DIR / "venv")


class VadParametersConfig(BaseModel):
    """
    Parameters for Voice Activity Detection (VAD).

    VAD filters silent segments before transcription to improve efficiency
    and reduce hallucinations.

    Attributes:
        threshold: Probability threshold (0.0 to 1.0) to classify a segment as speech.
            Default: 0.3
        min_speech_duration_ms: Minimum duration (ms) to be considered speech.
            Default: 250ms
        min_silence_duration_ms: Minimum silence duration (ms) to consider speech ended.
            Default: 500ms
    """

    threshold: float = 0.3
    min_speech_duration_ms: int = 250
    min_silence_duration_ms: int = 500


class WhisperConfig(BaseModel):
    """
    Configuration for the Whisper transcription model.

    Attributes:
        model: Whisper model name or path (e.g., 'tiny', 'base', 'large-v3').
            Default: 'large-v2'
        language: ISO 639-1 language code (e.g., 'es', 'en') or 'auto'.
            Default: 'es'
        device: Compute device ('cuda' for GPU, 'cpu').
            Default: 'cuda'
        compute_type: Numerical precision ('float16', 'int8_float16', 'int8').
            Default: 'int8_float16'
        device_index: GPU index to use. Default: 0
        num_workers: Number of workers for parallel processing. Default: 4
        beam_size: Beam search size. Default: 2
        best_of: Number of candidates to consider. Default: 2
        temperature: Sampling temperature (0.0 for deterministic).
            Default: 0.0
        vad_filter: Whether to apply VAD filtering. Default: True
        vad_parameters: Detailed VAD configuration.
        audio_device_index: Input audio device index (None for default).
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
    Configuration for Google Gemini LLM service.

    Attributes:
        model: Gemini model identifier (e.g., 'models/gemini-1.5-flash-latest').
        temperature: Generation temperature (0.0 to 2.0). Default: 0.3
        max_tokens: Maximum tokens to generate. Default: 2048
        max_input_chars: Input character limit. Default: 6000
        request_timeout: HTTP request timeout in seconds. Default: 30
        retry_attempts: Number of automatic retries. Default: 3
        retry_min_wait: Minimum wait between retries (seconds). Default: 2
        retry_max_wait: Maximum wait between retries (seconds). Default: 10
        api_key: API Key for Google Cloud (set via env var GEMINI_API_KEY).
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
    Configuration for desktop notifications.

    Attributes:
        expire_time_ms: Time in ms before auto-closing. Default: 3000
        auto_dismiss: Whether to force programmatic dismissal. Default: True
    """

    expire_time_ms: int = Field(default=3000, ge=500, le=30000)
    auto_dismiss: bool = Field(default=True)


class LocalLLMConfig(BaseModel):
    """
    Configuration for local LLM using llama.cpp.

    Attributes:
        model_path: Path to GGUF model file.
        n_gpu_layers: Number of layers to offload to GPU (-1 for all).
        n_ctx: Context window size. Default: 2048
        temperature: Generation temperature. Default: 0.3
        max_tokens: Maximum tokens to generate. Default: 512
    """

    model_path: Path = Field(default=Path("models/qwen2.5-3b-instruct-q4_k_m.gguf"))
    n_gpu_layers: int = Field(default=-1)
    n_ctx: int = Field(default=2048, ge=512, le=32768)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    translation_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=4096)


class OllamaConfig(BaseModel):
    """
    Configuration for Ollama LLM backend (SOTA 2026).

    Attributes:
        host: Ollama server URL. Default: http://localhost:11434
        model: Model name (phi3.5-mini, gemma2:2b, qwen2.5-coder:7b).
        keep_alive: Time to keep model loaded. "0m" frees VRAM immediately.
        temperature: Generation temperature. 0.0 for deterministic structured outputs.
    """

    host: str = Field(default="http://localhost:11434")
    model: str = Field(default="phi3.5-mini")
    keep_alive: str = Field(default="0m")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)


class LLMConfig(BaseModel):
    """
    LLM Service Configuration.

    Attributes:
        backend: Backend selector ("local", "gemini", or "ollama"). Default: "local"
        local: Configuration for the local llama.cpp backend.
        ollama: Configuration for the Ollama backend.
    """

    backend: Literal["local", "gemini", "ollama"] = Field(default="local")
    local: LocalLLMConfig = Field(default_factory=LocalLLMConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)


class TranscriptionConfig(BaseModel):
    """
    Transcription Service Configuration.

    Attributes:
        backend: Backend selector ("whisper"). Default: "whisper"
        whisper: Configuration for the Whisper backend.
    """

    backend: str = Field(default="whisper")
    whisper: WhisperConfig = Field(default_factory=WhisperConfig)


class Settings(BaseSettings):
    """
    Main Application Settings.

    Aggregates all configuration sections using Pydantic Settings.

    Attributes:
        paths: Paths configuration.
        transcription: Transcription configuration.
        gemini: Gemini LLM configuration.
        notifications: Notifications configuration.
        llm: LLM configuration.
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
        Customizes the priority of configuration sources.
        """
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )


config = Settings()
