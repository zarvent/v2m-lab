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
MÓDULO DE CONFIGURACIÓN DE LA APLICACIÓN VOICE2MACHINE

este módulo proporciona un sistema de configuración robusto y tipado utilizando
pydantic settings soporta múltiples fuentes de configuración con la siguiente
prioridad de mayor a menor

    1 argumentos de inicialización constructor
    2 variables de entorno
    3 archivo .env
    4 archivo config.toml
    5 valores por defecto

LA CONFIGURACIÓN ESTÁ ORGANIZADA EN SECCIONES LÓGICAS
    - ``PathsConfig`` rutas de archivos temporales y del sistema
    - ``WhisperConfig`` parámetros del modelo de transcripción
    - ``GeminiConfig`` configuración del servicio llm

EJEMPLO
    acceder a la configuración desde cualquier parte de la aplicación::

        from v2m.config import config

        # acceder a configuración de whisper
        modelo = config.whisper.model
        dispositivo = config.whisper.device

        # acceder a rutas
        archivo_audio = config.paths.audio_file

NOTAS
    - el archivo config.toml debe estar en la raíz del proyecto
    - las variables de entorno tienen prefijo automático del nombre de la sección
    - gemini_api_key debe definirse en el archivo .env o como variable de entorno
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

# --- ruta base del proyecto ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- directorio seguro de ejecución ---
RUNTIME_DIR = get_secure_runtime_dir()

class PathsConfig(BaseModel):
    """
    CONFIGURACIÓN DE RUTAS DE ARCHIVOS Y DIRECTORIOS PARA LA APLICACIÓN

    esta clase define las rutas utilizadas por el sistema para almacenar
    archivos temporales banderas de estado y registros de depuración

    ATTRIBUTES:
        recording_flag: ruta al archivo pid que indica una grabación activa
            se crea cuando inicia la grabación y se elimina al terminar
        audio_file: ruta al archivo wav temporal donde se guarda el audio
            grabado antes de la transcripción
        log_file: ruta al archivo de registro para depuración y diagnóstico
        venv_path: ruta al entorno virtual de python de la aplicación
            utilizado por los scripts de shell para activar el entorno

    EXAMPLE
        acceder a las rutas configuradas::

            from v2m.config import config

            if config.paths.recording_flag.exists():
                print("hay una grabación en progreso")
    """
    recording_flag: Path = Field(default=RUNTIME_DIR / "v2m_recording.pid")
    audio_file: Path = Field(default=RUNTIME_DIR / "v2m_audio.wav")
    log_file: Path = Field(default=RUNTIME_DIR / "v2m_debug.log")
    venv_path: Path = Field(default=BASE_DIR / "venv")

    def __getitem__(self, item):
        return getattr(self, item)

class VadParametersConfig(BaseModel):
    """
    PARÁMETROS PARA LA DETECCIÓN DE ACTIVIDAD DE VOZ VAD

    el vad voice activity detection filtra los segmentos de silencio del audio
    antes de enviarlos al modelo de transcripción mejorando la eficiencia y
    reduciendo alucinaciones en pausas largas

    ATTRIBUTES:
        threshold: umbral de probabilidad 0.0 a 1.0 para clasificar un
            segmento como voz valores más altos igual a detección más estricta
            por defecto 0.5
        min_speech_duration_ms: duración mínima en milisegundos que debe tener
            un segmento de audio para ser considerado como habla filtra
            ruidos breves por defecto 250ms
        min_silence_duration_ms: duración mínima del silencio en milisegundos
            requerida para considerar que el habla terminó valores más altos
            permiten pausas más largas dentro de una oración por defecto 500ms

    NOTE
        estos parámetros se pasan directamente a faster-whisper cuando
        ``vad_filter=true`` está habilitado en whisperconfig
    """
    threshold: float = 0.3
    min_speech_duration_ms: int = 250
    min_silence_duration_ms: int = 500


    def __getitem__(self, item):
        return getattr(self, item)

class WhisperConfig(BaseModel):
    """
    CONFIGURACIÓN PARA EL MODELO DE TRANSCRIPCIÓN WHISPER

    define todos los parámetros necesarios para cargar y ejecutar el modelo
    faster-whisper incluyendo configuración de hardware idioma y opciones
    de decodificación

    ATTRIBUTES:
        model: nombre o ruta del modelo whisper a utilizar modelos disponibles
            ``tiny`` ``base`` ``small`` ``medium`` ``large-v2``
            ``large-v3`` ``large-v3-turbo`` por defecto ``large-v2``
        language: código iso 639-1 del idioma para la transcripción ej ``es``
            ``en`` usar ``auto`` para detección automática por defecto ``es``
        device: dispositivo de cómputo ``cuda`` para gpu nvidia o ``cpu``
            por defecto ``cuda``
        compute_type: precisión numérica para inferencia opciones ``float32``
            ``float16`` ``int8`` gpu soporta ``float16`` cpu prefiere ``int8``
            por defecto ``float16``
        device_index: índice de la gpu a utilizar cuando hay múltiples
            por defecto 0 primera gpu
        num_workers: número de workers para procesamiento paralelo de audio
            por defecto 4
        beam_size: tamaño del beam search durante la decodificación valores
            más altos mejoran calidad pero aumentan latencia por defecto 2
        best_of: número de candidatos a considerar en cada paso de
            decodificación por defecto 2
        temperature: temperatura para el muestreo 0.0 para decodificación
            determinística greedy por defecto 0.0
        vad_filter: si se debe aplicar filtro vad integrado de faster-whisper
            para remover silencios por defecto ``true``
        vad_parameters: configuración detallada de los parámetros vad

    EXAMPLE
        configuración típica para gpu con alta calidad::

            [whisper]
            model = "large-v3-turbo"
            device = "cuda"
            compute_type = "float16"
            beam_size = 5
    """
    model: str = "large-v2"
    language: str = "es"
    device: str = "cuda"
    compute_type: str = "int8_float16"
    device_index: int = 0
    num_workers: int = 4
    beam_size: int = 2
    best_of: int = 2
    temperature: float = 0.0
    vad_filter: bool = True
    audio_device_index: int | None = None
    vad_parameters: VadParametersConfig = Field(default_factory=VadParametersConfig)

    def __getitem__(self, item):
        return getattr(self, item)

class GeminiConfig(BaseModel):
    """
    CONFIGURACIÓN PARA EL SERVICIO LLM DE GOOGLE GEMINI

    define los parámetros para conectarse a la api de google gemini y configurar
    el comportamiento del modelo de lenguaje utilizado para refinar las
    transcripciones

    ATTRIBUTES:
        model: identificador del modelo gemini formato
            ``models/<nombre-modelo>`` por defecto ``models/gemini-1.5-flash-latest``
        temperature: temperatura para la generación de texto 0.0 a 2.0
            valores más bajos igual a respuestas más determinísticas
            por defecto 0.3
        max_tokens: número máximo de tokens a generar en la respuesta
            por defecto 2048
        max_input_chars: límite de caracteres de entrada para evitar exceder
            el contexto del modelo por defecto 6000
        request_timeout: tiempo máximo de espera para una solicitud http
            en segundos por defecto 30
        retry_attempts: número de reintentos automáticos ante errores
            transitorios red rate limiting por defecto 3
        retry_min_wait: tiempo mínimo de espera entre reintentos en segundos
            usado con backoff exponencial por defecto 2
        retry_max_wait: tiempo máximo de espera entre reintentos en segundos
            por defecto 10
        api_key: clave de api para autenticación con google cloud
            se recomienda definir en archivo ``.env`` como ``gemini_api_key``

    WARNING
        la ``api_key`` es sensible y no debe incluirse en control de versiones
        utiliza variables de entorno o un archivo ``.env`` local

    EXAMPLE
        configuración en config.toml::

            [gemini]
            model = "models/gemini-1.5-pro"
            temperature = 0.2
            api_key = "${GEMINI_API_KEY}"
    """
    model: str = "models/gemini-1.5-flash-latest"
    temperature: float = 0.3
    max_tokens: int = 2048
    max_input_chars: int = 6000
    request_timeout: int = 30
    retry_attempts: int = 3
    retry_min_wait: int = 2
    retry_max_wait: int = 10
    api_key: str | None = Field(default=None)

    def __getitem__(self, item):
        return getattr(self, item)


class NotificationsConfig(BaseModel):
    """
    CONFIGURACIÓN PARA EL SISTEMA DE NOTIFICACIONES DEL ESCRITORIO

    define parámetros para controlar el comportamiento de las notificaciones
    visuales incluyendo tiempo de expiración y cierre programático

    ATTRIBUTES:
        expire_time_ms: tiempo en milisegundos antes de auto-cerrar la
            notificación por defecto 3000 o 3 segundos
        auto_dismiss: si true fuerza el cierre programático via dbus
            necesario para unity o gnome que ignoran expire-time
            por defecto true

    EXAMPLE:
        configuración en config.toml::

            [notifications]
            expire_time_ms = 5000
            auto_dismiss = true
    """
    expire_time_ms: int = Field(default=3000, ge=500, le=30000)
    auto_dismiss: bool = Field(default=True)

    def __getitem__(self, item):
        return getattr(self, item)


class LocalLLMConfig(BaseModel):
    """
    CONFIGURACIÓN PARA EL MODELO DE LENGUAJE LOCAL USANDO LLAMA.CPP

    permite ejecutar modelos gguf como qwen llama phi mistral localmente
    en gpu sin depender de apis externas

    ATTRIBUTES:
        model_path: ruta relativa al archivo gguf del modelo desde base_dir
            por defecto usa qwen2.5-3b-instruct q4_k_m
        n_gpu_layers: número de capas a cargar en gpu usar -1 para todas
            las capas full gpu offload por defecto -1
        n_ctx: tamaño del context window en tokens por defecto 2048
        temperature: temperatura para generación 0.0 a 2.0 valores bajos
            igual a respuestas más determinísticas por defecto 0.3
        max_tokens: máximo de tokens a generar en la respuesta por defecto 512

    EXAMPLE:
        configuración en config.toml::

            [llm.local]
            model_path = "models/qwen2.5-3b-instruct-q4_k_m.gguf"
            n_gpu_layers = -1
            temperature = 0.3
    """
    model_path: Path = Field(default=Path("models/qwen2.5-3b-instruct-q4_k_m.gguf"))
    n_gpu_layers: int = Field(default=-1)
    n_ctx: int = Field(default=2048, ge=512, le=32768)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=4096)

    def __getitem__(self, item):
        return getattr(self, item)


class LLMConfig(BaseModel):
    """
    CONFIGURACIÓN DEL SERVICIO LLM CON SELECTOR DE BACKEND

    permite elegir entre un modelo local llama.cpp o la api de gemini
    el backend se selecciona mediante la opción ``backend``

    ATTRIBUTES:
        backend: selector del backend a usar
            - "local": modelo gguf local con llama.cpp offline
            - "gemini": api de google gemini cloud
            por defecto "local"
        local: configuración específica para el backend local

    EXAMPLE:
        configuración en config.toml::

            [llm]
            backend = "local"

            [llm.local]
            model_path = "models/qwen2.5-3b-instruct-q4_k_m.gguf"
    """
    backend: Literal["local", "gemini"] = Field(default="local")
    local: LocalLLMConfig = Field(default_factory=LocalLLMConfig)

    def __getitem__(self, item):
        return getattr(self, item)


class TranscriptionConfig(BaseModel):
    """
    CONFIGURACIÓN DEL SERVICIO DE TRANSCRIPCIÓN CON SELECTOR DE BACKEND

    permite elegir entre diferentes implementaciones de transcripción
    el backend se selecciona mediante la opción ``backend``

    ATTRIBUTES:
        backend: selector del backend a usar
            - "whisper": faster-whisper default gpu acelerado
            - futuro: "vosk" "speechbrain" "custom"
            por defecto "whisper"
        whisper: configuración específica para el backend whisper

    EXAMPLE:
        configuración en config.toml::

            [transcription]
            backend = "whisper"

            [transcription.whisper]
            model = "large-v3-turbo"
            device = "cuda"
    """
    backend: str = Field(default="whisper")
    whisper: WhisperConfig = Field(default_factory=WhisperConfig)

    def __getitem__(self, item):
        return getattr(self, item)

class Settings(BaseSettings):
    """
    CLASE PRINCIPAL DE CONFIGURACIÓN QUE AGRUPA TODAS LAS SECCIONES

    esta clase actúa como el punto de acceso centralizado para toda la
    configuración de la aplicación utiliza pydantic settings para cargar
    y validar la configuración desde múltiples fuentes

    ATTRIBUTES:
        paths: configuración de rutas de archivos y directorios
        whisper: configuración del modelo de transcripción whisper
        gemini: configuración del servicio llm gemini

    EXAMPLE
        uso típico desde cualquier módulo::

            from v2m.config import config

            # la instancia 'config' está pre-inicializada
            print(f"modelo whisper: {config.whisper.model}")
            print(f"dispositivo: {config.whisper.device}")

    NOTE
        esta clase no debe instanciarse directamente usar la instancia
        global ``config`` exportada por este módulo
    """
    paths: PathsConfig = Field(default_factory=PathsConfig)
    whisper: WhisperConfig = Field(default_factory=WhisperConfig)  # DEPRECATED v2.0: usar transcription.whisper
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    transcription: TranscriptionConfig = Field(default_factory=TranscriptionConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        toml_file=BASE_DIR / "config.toml"
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
        PERSONALIZA EL ORDEN DE LAS FUENTES DE CONFIGURACIÓN

        este método sobrescribe el comportamiento por defecto de pydantic settings
        para incluir archivos toml como fuente de configuración adicional

        el orden de prioridad resultante es de mayor a menor
            1 argumentos del constructor init_settings
            2 variables de entorno env_settings
            3 archivo .env dotenv_settings
            4 archivo config.toml tomlconfigsettingssource
            5 archivos de secretos file_secret_settings

        ARGS:
            settings_cls: la clase de configuración siendo inicializada
            init_settings: fuente para valores pasados al constructor
            env_settings: fuente para variables de entorno del sistema
            dotenv_settings: fuente para valores del archivo .env
            file_secret_settings: fuente para archivos de secretos docker secrets

        RETURNS:
            tupla ordenada de fuentes de configuración las fuentes al inicio
            tienen mayor prioridad y sobrescriben valores de fuentes posteriores
        """
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

    def __getitem__(self, item):
        return getattr(self, item)

config = Settings()
