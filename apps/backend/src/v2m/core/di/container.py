# Este archivo es parte de voice2machine.
#
# voice2machine es software libre: puedes redistribuirlo y/o modificarlo
# bajo los términos de la Licencia Pública General GNU publicada por
# la Free Software Foundation, ya sea la versión 3 de la Licencia, o
# (a tu elección) cualquier versión posterior.
#
# voice2machine se distribuye con la esperanza de que sea útil,
# pero SIN NINGUNA GARANTÍA; ni siquiera la garantía implícita de
# COMERCIABILIDAD o IDONEIDAD PARA UN PROPÓSITO PARTICULAR. Consulta la
# Licencia Pública General GNU para más detalles.
#
# Deberías haber recibido una copia de la Licencia Pública General GNU
# junto con voice2machine. Si no, consulta <https://www.gnu.org/licenses/>.

"""
Contenedor de Inyección de Dependencias (DI) para Voice2Machine.

Este módulo implementa el "Composition Root" de la aplicación. Es el único lugar donde
se instancian las clases concretas y se cablean con sus dependencias.

Responsabilidades:
    1. Instanciar servicios de infraestructura (Singletons).
    2. Resolver implementaciones dinámicas (Factories basadas en configuración).
    3. Instanciar CommandHandlers inyectando dependencias.
    4. Configurar y exponer el CommandBus.

Patrón:
    - Composition Root.
    - Singleton implícito (variable global `container`).
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from v2m.application.command_handlers import (
    GetConfigHandler,
    PauseDaemonHandler,
    ProcessTextHandler,
    ResumeDaemonHandler,
    StartRecordingHandler,
    StopRecordingHandler,
    TranslateTextHandler,
    UpdateConfigHandler,
)
from v2m.application.config_manager import ConfigManager
from v2m.application.llm_service import LLMService
from v2m.application.transcription_service import TranscriptionService
from v2m.config import config
from v2m.core.cqrs.command_bus import CommandBus
from v2m.core.interfaces import ClipboardInterface, NotificationInterface
from v2m.core.logging import logger
from v2m.core.providers import ProviderNotFoundError, llm_registry, transcription_registry
from v2m.infrastructure.gemini_llm_service import GeminiLLMService
from v2m.infrastructure.linux_adapters import LinuxClipboardAdapter
from v2m.infrastructure.local_llm_service import LocalLLMService
from v2m.infrastructure.notification_service import LinuxNotificationService
from v2m.infrastructure.ollama_llm_service import OllamaLLMService

# --- AUTO-REGISTRO DE PROVIDERS ---
# Los imports fuerzan el registro en los registries globales.
from v2m.infrastructure.whisper_transcription_service import WhisperTranscriptionService

# Registrar providers explícitamente para claridad
transcription_registry.register("whisper", WhisperTranscriptionService)
llm_registry.register("local", LocalLLMService)
llm_registry.register("gemini", GeminiLLMService)
llm_registry.register("ollama", OllamaLLMService)


class Container:
    """
    Contenedor de Inyección de Dependencias.

    Gestiona el ciclo de vida y la resolución de dependencias de la aplicación.
    """

    def __init__(self) -> None:
        """
        Inicializa y cablea todas las dependencias.

        El proceso sigue un orden estricto de dependencias:
        Config -> Infrastructure -> Application Handlers -> CommandBus.
        """
        # --- 1. Servicios de Infraestructura (Singletons) ---

        # Config Manager
        self.config_manager = ConfigManager()

        # Selección de Backend de Transcripción
        transcription_backend = config.transcription.backend
        try:
            TranscriptionClass = transcription_registry.get(transcription_backend)
            self.transcription_service: TranscriptionService = TranscriptionClass()
            logger.info(f"backend de transcripción: {transcription_backend}")
        except ProviderNotFoundError as e:
            logger.critical(f"backend de transcripción inválido: {e}")
            raise

        # ThreadPoolExecutor para Warmup (libera el GIL)
        self._warmup_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="warmup")
        self._warmup_future = self._warmup_executor.submit(self._preload_models)

        # Selección de Backend LLM
        llm_backend = config.llm.backend
        try:
            LLMClass = llm_registry.get(llm_backend)
            self.llm_service: LLMService = LLMClass()
            logger.info(f"backend llm: {llm_backend}")
        except ProviderNotFoundError as e:
            logger.critical(f"backend llm inválido: {e}")
            raise

        # Adaptadores de Sistema
        self.notification_service: NotificationInterface = LinuxNotificationService()
        self.clipboard_service: ClipboardInterface = LinuxClipboardAdapter()

        # --- 2. Manejadores de Comandos (Application Layer) ---
        self.start_recording_handler = StartRecordingHandler(
            self.transcription_service, self.notification_service
        )
        self.stop_recording_handler = StopRecordingHandler(
            self.transcription_service, self.notification_service, self.clipboard_service
        )
        self.process_text_handler = ProcessTextHandler(
            self.llm_service, self.notification_service, self.clipboard_service
        )
        self.translate_text_handler = TranslateTextHandler(
            self.llm_service, self.notification_service
        )

        # Handlers de Gestión y Configuración
        self.update_config_handler = UpdateConfigHandler(
            self.config_manager, self.notification_service
        )
        self.get_config_handler = GetConfigHandler(self.config_manager)
        self.pause_daemon_handler = PauseDaemonHandler(self.notification_service)
        self.resume_daemon_handler = ResumeDaemonHandler(self.notification_service)

        # --- 3. Bus de Comandos ---
        self.command_bus = CommandBus()
        self.command_bus.register(self.start_recording_handler)
        self.command_bus.register(self.stop_recording_handler)
        self.command_bus.register(self.process_text_handler)
        self.command_bus.register(self.translate_text_handler)
        self.command_bus.register(self.update_config_handler)
        self.command_bus.register(self.get_config_handler)
        self.command_bus.register(self.pause_daemon_handler)
        self.command_bus.register(self.resume_daemon_handler)

    def get_command_bus(self) -> CommandBus:
        """
        Retorna la instancia configurada del CommandBus.
        """
        return self.command_bus

    def _preload_models(self) -> None:
        """
        Precarga modelos pesados en segundo plano.
        Reduce la latencia de la primera interacción ("Cold Start").
        """
        try:
            # Forzar carga lazy del modelo Whisper
            _ = self.transcription_service.model
            logger.info("✅ whisper precargado correctamente")
        except Exception as e:
            # Evitar fallo catastrófico en warmup
            logger.warning(f"⚠️ fallo en precarga de whisper: {e}")

    async def wait_for_warmup(self, timeout: float = 30.0) -> bool:
        """
        Espera la finalización de la precarga de modelos.

        Args:
            timeout: Tiempo máximo de espera en segundos.

        Returns:
            bool: True si la carga fue exitosa, False si hubo timeout.
        """
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, self._warmup_future.result), timeout=timeout
            )
            return True
        except TimeoutError:
            logger.warning(f"timeout de warmup después de {timeout}s")
            return False


# --- Instancia Global del Contenedor ---
# Singleton implícito para uso en todo el módulo
try:
    container = Container()
except Exception as e:
    logger.critical(f"Fallo crítico al inicializar el contenedor: {e}")
    raise e
