"""
Orquestador Central de Voice2Machine

Flujo simplificado:
    toggle() → si no graba: start() → si graba: stop() → transcribir → clipboard

Lazy Initialization:
    Los servicios pesados (Whisper, LLM) se crean cuando se necesitan, no al inicio.
    Esto permite que el servidor FastAPI arranque rápido (~100ms).
"""

from __future__ import annotations

import asyncio
import contextlib
import re
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any

from v2m.config import config
from v2m.core.logging import logger

if TYPE_CHECKING:
    from v2m.api import LLMResponse, StatusResponse, ToggleResponse
    from v2m.infrastructure.audio.recorder import AudioRecorder
    from v2m.infrastructure.linux_adapters import LinuxClipboardAdapter
    from v2m.infrastructure.notification_service import LinuxNotificationService
    from v2m.infrastructure.persistent_model import PersistentWhisperWorker
    from v2m.infrastructure.streaming_transcriber import StreamingTranscriber


# Tipo para la función de broadcast de eventos WebSocket
BroadcastFn = Callable[[str, dict[str, Any]], Coroutine[Any, Any, None]]


class Orchestrator:
    """
    Orquestador central de V2M.

    Coordina todos los servicios (audio, transcripción, LLM, clipboard, notificaciones)
    usando lazy initialization. Reemplaza el patrón CQRS + DI Container.

    Atributos:
        _is_recording: Estado actual de grabación.
        _model_loaded: True si el modelo Whisper está cargado en VRAM.
        _broadcast_fn: Función para emitir eventos a clientes WebSocket.
    """

    def __init__(self, broadcast_fn: BroadcastFn | None = None) -> None:
        """
        Inicializa el orquestador.

        Args:
            broadcast_fn: Función opcional para enviar eventos a WebSocket clients.
        """
        # Estado
        self._is_recording: bool = False
        self._model_loaded: bool = False
        self._broadcast_fn = broadcast_fn

        # Servicios (lazy init)
        self._worker: PersistentWhisperWorker | None = None
        self._recorder: AudioRecorder | None = None
        self._transcriber: StreamingTranscriber | None = None
        self._clipboard: LinuxClipboardAdapter | None = None
        self._notifications: LinuxNotificationService | None = None
        self._llm_service: Any | None = None  # Tipo dinámico según backend

    # =========================================================================
    # Propiedades con Lazy Initialization
    # =========================================================================

    @property
    def worker(self) -> PersistentWhisperWorker:
        """Obtiene el worker de Whisper (lazy init)."""
        if self._worker is None:
            from v2m.infrastructure.persistent_model import PersistentWhisperWorker

            whisper_cfg = config.transcription.whisper
            self._worker = PersistentWhisperWorker(
                model_size=whisper_cfg.model,
                device=whisper_cfg.device,
                compute_type=whisper_cfg.compute_type,
                device_index=whisper_cfg.device_index,
                num_workers=whisper_cfg.num_workers,
                keep_warm=whisper_cfg.keep_warm,
            )
        return self._worker

    @property
    def recorder(self) -> AudioRecorder:
        """Obtiene el grabador de audio (lazy init)."""
        if self._recorder is None:
            from v2m.infrastructure.audio.recorder import AudioRecorder

            whisper_cfg = config.transcription.whisper
            self._recorder = AudioRecorder(
                sample_rate=16000,
                channels=1,
                device_index=whisper_cfg.audio_device_index,
            )
        return self._recorder

    @property
    def transcriber(self) -> StreamingTranscriber:
        """Obtiene el transcriptor streaming (lazy init)."""
        if self._transcriber is None:
            from v2m.core.client_session import ClientSessionManager
            from v2m.infrastructure.streaming_transcriber import StreamingTranscriber

            # Session manager que emite eventos a WebSocket
            session_manager = ClientSessionManager()
            if self._broadcast_fn:
                # Conectar el broadcast de WebSocket
                session_manager.emit_event = self._create_emit_wrapper()

            self._transcriber = StreamingTranscriber(
                worker=self.worker,
                session_manager=session_manager,
                recorder=self.recorder,
            )
        return self._transcriber

    @property
    def clipboard(self) -> LinuxClipboardAdapter:
        """Obtiene el servicio de clipboard (lazy init)."""
        if self._clipboard is None:
            from v2m.infrastructure.linux_adapters import LinuxClipboardAdapter

            self._clipboard = LinuxClipboardAdapter()
        return self._clipboard

    @property
    def notifications(self) -> LinuxNotificationService:
        """Obtiene el servicio de notificaciones (lazy init)."""
        if self._notifications is None:
            from v2m.infrastructure.notification_service import LinuxNotificationService

            self._notifications = LinuxNotificationService()
        return self._notifications

    @property
    def llm_service(self) -> Any:
        """Obtiene el servicio LLM según configuración (lazy init)."""
        if self._llm_service is None:
            backend = config.llm.backend

            if backend == "gemini":
                from v2m.infrastructure.gemini_llm_service import GeminiLLMService

                self._llm_service = GeminiLLMService()
            elif backend == "ollama":
                from v2m.infrastructure.ollama_llm_service import OllamaLLMService

                self._llm_service = OllamaLLMService()
            else:  # "local"
                from v2m.infrastructure.local_llm_service import LocalLLMService

                self._llm_service = LocalLLMService()

            logger.info(f"LLM backend inicializado: {backend}")
        return self._llm_service

    def _create_emit_wrapper(self) -> Callable:
        """Crea un wrapper para conectar SessionManager con WebSocket broadcast."""

        async def emit_event(event_type: str, data: dict[str, Any]) -> None:
            if self._broadcast_fn:
                await self._broadcast_fn(event_type, data)

        return emit_event

    # =========================================================================
    # Métodos Públicos (API Surface - Lo que ve el Junior)
    # =========================================================================

    async def warmup(self) -> None:
        """
        Pre-carga el modelo Whisper en VRAM.

        Llamado en startup del servidor para tener el modelo "caliente"
        y reducir latencia en la primera transcripción.
        """
        if self._model_loaded:
            return

        try:
            # Warmup sincrono en el executor del worker
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.worker.initialize_sync)
            self._model_loaded = True
            logger.info("✅ Modelo Whisper precargado en VRAM")
        except Exception as e:
            logger.error(f"❌ Error en warmup del modelo: {e}")
            # No re-lanzamos - el modelo se cargará on-demand

    async def toggle(self) -> ToggleResponse:
        """
        Toggle de grabación.

        Si no está grabando → inicia.
        Si está grabando → detiene y transcribe.

        Returns:
            ToggleResponse: Estado actual y texto transcrito (si aplica).
        """
        if not self._is_recording:
            return await self.start()
        else:
            return await self.stop()

    async def start(self) -> ToggleResponse:
        """
        Inicia la grabación de audio.

        Returns:
            ToggleResponse: Confirmación de inicio.
        """
        from v2m.api import ToggleResponse

        if self._is_recording:
            return ToggleResponse(
                status="recording",
                message="⚠️ Ya está grabando",
            )

        try:
            # Iniciar streaming transcriber
            await self.transcriber.start()
            self._is_recording = True

            # Crear flag file para scripts externos
            config.paths.recording_flag.touch()

            # Notificar al usuario
            self.notifications.notify("🎤 voice2machine", "grabación iniciada...")

            logger.info("🎙️ Grabación iniciada")
            return ToggleResponse(
                status="recording",
                message="🎙️ Grabando...",
            )

        except Exception as e:
            logger.error(f"Error iniciando grabación: {e}")
            return ToggleResponse(
                status="error",
                message=f"❌ Error: {e}",
            )

    async def stop(self) -> ToggleResponse:
        """
        Detiene la grabación y transcribe el audio.

        Returns:
            ToggleResponse: Texto transcrito.
        """
        from v2m.api import ToggleResponse

        if not self._is_recording:
            return ToggleResponse(
                status="idle",
                message="⚠️ No hay grabación en curso",
            )

        try:
            self._is_recording = False

            # Eliminar flag file
            if config.paths.recording_flag.exists():
                config.paths.recording_flag.unlink()

            # Notificar procesamiento
            self.notifications.notify("⚡ v2m procesando", "procesando...")

            # Detener y obtener transcripción
            transcription = await self.transcriber.stop()

            # Validar resultado
            if not transcription or not transcription.strip():
                self.notifications.notify("❌ whisper", "no se detectó voz en el audio")
                return ToggleResponse(
                    status="idle",
                    message="❌ No se detectó voz",
                    text=None,
                )

            # Copiar al portapapeles
            self.clipboard.copy(transcription)

            # Notificar éxito
            preview = transcription[:80]
            self.notifications.notify("✅ whisper - copiado", f"{preview}...")

            logger.info(f"✅ Transcripción completada: {len(transcription)} chars")
            return ToggleResponse(
                status="idle",
                message="✅ Copiado al portapapeles",
                text=transcription,
            )

        except Exception as e:
            logger.error(f"Error deteniendo grabación: {e}")
            self._is_recording = False
            return ToggleResponse(
                status="error",
                message=f"❌ Error: {e}",
            )

    async def process_text(self, text: str) -> LLMResponse:
        """
        Procesa texto con LLM (limpieza, puntuación, formato).

        Args:
            text: Texto a procesar.

        Returns:
            LLMResponse: Texto procesado y backend usado.
        """
        from v2m.api import LLMResponse

        backend_name = config.llm.backend

        try:
            # El servicio LLM puede ser sync o async
            if asyncio.iscoroutinefunction(self.llm_service.process_text):
                refined = await self.llm_service.process_text(text)
            else:
                refined = await asyncio.to_thread(self.llm_service.process_text, text)

            # Copiar al portapapeles
            self.clipboard.copy(refined)
            self.notifications.notify(f"✅ {backend_name} - copiado", f"{refined[:80]}...")

            return LLMResponse(text=refined, backend=backend_name)

        except Exception as e:
            logger.error(f"Error procesando texto con {backend_name}: {e}")
            # Fallback: copiar texto original
            self.clipboard.copy(text)
            self.notifications.notify(f"⚠️ {backend_name} falló", "usando texto original...")
            return LLMResponse(text=text, backend=f"{backend_name} (fallback)")

    async def translate_text(self, text: str, target_lang: str) -> LLMResponse:
        """
        Traduce texto con LLM.

        Args:
            text: Texto a traducir.
            target_lang: Idioma destino (ej. 'en', 'es').

        Returns:
            LLMResponse: Texto traducido.
        """
        from v2m.api import LLMResponse

        backend_name = config.llm.backend

        # Validar target_lang para prevenir inyección
        if not re.match(r"^[a-zA-Z\s\-]{2,20}$", target_lang):
            logger.warning(f"Idioma inválido: {target_lang}")
            self.notifications.notify("❌ Error", "Idioma de destino inválido")
            return LLMResponse(text=text, backend="error")

        try:
            if asyncio.iscoroutinefunction(self.llm_service.translate_text):
                translated = await self.llm_service.translate_text(text, target_lang)
            else:
                translated = await asyncio.to_thread(self.llm_service.translate_text, text, target_lang)

            self.clipboard.copy(translated)
            self.notifications.notify(f"✅ Traducción ({target_lang})", f"{translated[:80]}...")

            return LLMResponse(text=translated, backend=backend_name)

        except Exception as e:
            logger.error(f"Error traduciendo con {backend_name}: {e}")
            self.notifications.notify("❌ Error traducción", "Fallo al traducir")
            return LLMResponse(text=text, backend=f"{backend_name} (error)")

    def get_status(self) -> StatusResponse:
        """
        Retorna estado actual del daemon.

        Returns:
            StatusResponse: Estado de grabación y modelo.
        """
        from v2m.api import StatusResponse

        state = "recording" if self._is_recording else "idle"

        return StatusResponse(
            state=state,
            recording=self._is_recording,
            model_loaded=self._model_loaded,
        )

    async def shutdown(self) -> None:
        """Libera recursos al apagar el servidor."""
        logger.info("Liberando recursos del orquestador...")

        # Detener grabación si está activa
        if self._is_recording:
            with contextlib.suppress(Exception):
                await self.stop()

        # Descargar modelo de VRAM
        if self._worker:
            try:
                await self._worker.unload()
            except Exception as e:
                logger.warning(f"Error descargando modelo: {e}")

        # Cerrar servicio de notificaciones
        if self._notifications:
            self._notifications.shutdown(wait=False)

        logger.info("✅ Recursos liberados")
