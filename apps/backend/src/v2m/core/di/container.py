
"""
Contenedor de Inyección de Dependencias (DI) para Voice2Machine.

Este módulo implementa el patrón de Inyección de Dependencias que conecta
toda la aplicación. Gestiona el ciclo de vida de los servicios, incluyendo
el worker persistente de Whisper y el Session Manager para streaming.
"""

import asyncio
import atexit
import contextlib
import logging
import sys
from concurrent.futures import ThreadPoolExecutor

from v2m.application.command_handlers import (
    ProcessTextHandler,
    StartRecordingHandler,
    StopRecordingHandler,
    TranscribeFileHandler,
)
from v2m.application.llm_service import LLMService
from v2m.application.transcription_service import TranscriptionService
from v2m.config import config
from v2m.core.client_session import ClientSessionManager
from v2m.core.cqrs.command_bus import CommandBus
from v2m.core.interfaces import ClipboardInterface, NotificationInterface
from v2m.core.logging import logger
from v2m.core.providers import ProviderNotFoundError, llm_registry, transcription_registry
from v2m.infrastructure.file_transcription_service import FileTranscriptionService
from v2m.infrastructure.gemini_llm_service import GeminiLLMService
from v2m.infrastructure.linux_adapters import LinuxClipboardAdapter
from v2m.infrastructure.local_llm_service import LocalLLMService
from v2m.infrastructure.notification_service import LinuxNotificationService
from v2m.infrastructure.ollama_llm_service import OllamaLLMService
from v2m.infrastructure.persistent_model import PersistentWhisperWorker

# --- AUTO-REGISTRO DE PROVEEDORES ---
from v2m.infrastructure.whisper_transcription_service import WhisperTranscriptionService

# Registrar providers (para fallback o consistencia)
transcription_registry.register("whisper", WhisperTranscriptionService)
llm_registry.register("local", LocalLLMService)
llm_registry.register("gemini", GeminiLLMService)
llm_registry.register("ollama", OllamaLLMService)


class Container:
    """
    Contenedor de DI que gestiona el ciclo de vida y las dependencias de los objetos.
    """

    def __init__(self) -> None:
        """
        Inicializa y configura todas las dependencias de la aplicación.
        """
        # --- 0. Core Services ---
        self.client_session_manager = ClientSessionManager()

        # --- 1. Instanciar Servicios (Infraestructura) ---

        # --- Configuración de Whisper Persistente ---
        transcription_backend = config.transcription.backend
        self.whisper_worker = None
        self._warmup_executor = None
        self._warmup_future = None

        if transcription_backend == "whisper":
            logger.info("Inicializando worker persistente de Whisper...")
            whisper_cfg = config.transcription.whisper
            self.whisper_worker = PersistentWhisperWorker(
                model_size=whisper_cfg.model,
                device=whisper_cfg.device,
                compute_type=whisper_cfg.compute_type,
                device_index=whisper_cfg.device_index,
                num_workers=whisper_cfg.num_workers,
                keep_warm=whisper_cfg.keep_warm,
            )

            # Inyectar worker y session_manager en el servicio
            self.transcription_service: TranscriptionService = WhisperTranscriptionService(
                self.whisper_worker, self.client_session_manager
            )

            # Precarga (Warmup)
            self._warmup_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="warmup")
            self._warmup_future = self._warmup_executor.submit(self._preload_models)
        else:
            # Fallback para otros backends
            try:
                transcription_cls = transcription_registry.get(transcription_backend)
                # Si otra clase requiere deps extra, aquí fallará si no se adapta
                self.transcription_service = transcription_cls()
                logger.info(f"backend de transcripción seleccionado: {transcription_backend}")
            except ProviderNotFoundError as e:
                logger.critical(f"backend de transcripción inválido: {e}")
                raise

        # --- Selección de backend LLM ---
        llm_backend = config.llm.backend
        try:
            llm_cls = llm_registry.get(llm_backend)
            self.llm_service: LLMService = llm_cls()
            logger.info(f"backend llm seleccionado: {llm_backend}")
        except ProviderNotFoundError as e:
            logger.critical(f"backend llm inválido: {e}")
            raise

        # Adaptadores de Sistema
        self.notification_service: NotificationInterface = LinuxNotificationService()
        self.clipboard_service: ClipboardInterface = LinuxClipboardAdapter()

        # --- 2. Instanciar Manejadores de Comandos ---
        self.start_recording_handler = StartRecordingHandler(self.transcription_service, self.notification_service)
        self.stop_recording_handler = StopRecordingHandler(
            self.transcription_service, self.notification_service, self.clipboard_service
        )
        self.process_text_handler = ProcessTextHandler(
            self.llm_service, self.notification_service, self.clipboard_service
        )

        # --- Servicio de Transcripción de Archivos ---
        if self.whisper_worker:
            self.file_transcription_service = FileTranscriptionService(self.whisper_worker)
            self.transcribe_file_handler = TranscribeFileHandler(self.file_transcription_service)
        else:
            logger.warning("FileTranscriptionService deshabilitado (requiere Whisper backend)")
            self.file_transcription_service = None
            self.transcribe_file_handler = None

        # --- 3. Instanciar y Configurar el Bus de Comandos ---
        self.command_bus = CommandBus()
        self.command_bus.register(self.start_recording_handler)
        self.command_bus.register(self.stop_recording_handler)
        self.command_bus.register(self.process_text_handler)

        if self.transcribe_file_handler:
            self.command_bus.register(self.transcribe_file_handler)

    def get_command_bus(self) -> CommandBus:
        return self.command_bus

    def _preload_models(self) -> None:
        """
        Precarga modelos de ML en segundo plano (Sync Warmup).
        """
        if self.whisper_worker:
            try:
                self.whisper_worker.initialize_sync()
                self._safe_log(logging.INFO, "✅ whisper precargado correctamente")
            except Exception as e:
                self._safe_log(logging.WARNING, f"⚠️ no se pudo precargar whisper: {e}")

    def _safe_log(self, level: int, msg: str) -> None:
        """Log safely, suppressing errors during interpreter shutdown."""
        try:
            if sys.stderr is None:
                return
            logger.log(level, msg)
        except (ValueError, OSError):
            pass

    async def wait_for_warmup(self, timeout: float = 30.0) -> bool:
        """
        Espera a que el warmup termine.
        """
        if not self._warmup_future:
            return True

        loop = asyncio.get_running_loop()
        try:
            await asyncio.wait_for(loop.run_in_executor(None, self._warmup_future.result), timeout=timeout)
            return True
        except TimeoutError:
            logger.warning(f"timeout de warmup después de {timeout}s")
            return False

    def shutdown(self) -> None:
        """
        Gracefully shutdown all background workers and executors.

        This prevents the 'I/O operation on closed file' error that occurs
        when daemon threads try to log after Python has begun shutdown.
        """
        # Wait for warmup to complete (with short timeout) before shutting down
        if self._warmup_future:
            with contextlib.suppress(Exception):
                # Wait up to 1 second for warmup to finish naturally
                self._warmup_future.result(timeout=1.0)
            self._warmup_future = None

        # Shutdown warmup executor - wait=True ensures threads finish cleanly
        if self._warmup_executor:
            self._warmup_executor.shutdown(wait=True, cancel_futures=True)
            self._warmup_executor = None

        # Shutdown whisper worker executor
        if (
            self.whisper_worker
            and hasattr(self.whisper_worker, '_executor')
            and self.whisper_worker._executor
        ):
            self.whisper_worker._executor.shutdown(wait=True, cancel_futures=True)


# --- Instancia Global del Contenedor ---
container = Container()

# Register shutdown handler to prevent "I/O operation on closed file" errors
# during Python interpreter shutdown
atexit.register(container.shutdown)
