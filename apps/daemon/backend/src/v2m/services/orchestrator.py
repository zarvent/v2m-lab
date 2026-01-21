"""Orquestador Central de Voice2Machine.

Módulo principal que coordina el flujo de trabajo completo del sistema de dictado.
Implementa el patrón Orchestrator como reemplazo simplificado de CQRS/CommandBus.

Flujo Principal:
    toggle() → {idle: start() → recording} | {recording: stop() → transcribir → clipboard}

Decisión Arquitectónica:
    Usa Lazy Initialization para mantener el tiempo de arranque del servidor <100ms.
    Los servicios pesados (Whisper, LLM) se crean cuando se necesitan por primera vez.
    Ver: docs/adr/002-orchestrator-pattern.md

Example:
    >>> orchestrator = Orchestrator(broadcast_fn=websocket_broadcast)
    >>> response = await orchestrator.toggle()
    >>> print(response.status)  # 'recording' o 'idle'
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


#: Tipo para funciones de broadcast a clientes WebSocket.
#: Recibe (event_type, data) y retorna una corutina.
BroadcastFn = Callable[[str, dict[str, Any]], Coroutine[Any, Any, None]]


class WebSocketSessionAdapter:
    """Adaptador que conecta StreamingTranscriber con el broadcast de WebSocket.

    Implementa el patrón Adapter para desacoplar el transcriptor del sistema
    de notificaciones WebSocket, facilitando testing y extensibilidad.

    Attributes:
        _broadcast_fn: Función inyectada para emitir eventos a clientes conectados.
    """

    def __init__(self, broadcast_fn: BroadcastFn | None = None) -> None:
        """Inicializa el adaptador con una función opcional de broadcast.

        Args:
            broadcast_fn: Función async que recibe (event_type, data) y envía
                a los clientes WebSocket. Si es None, los eventos se descartan
                silenciosamente.
        """
        self._broadcast_fn = broadcast_fn

    async def emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Emite un evento a todos los clientes WebSocket conectados.

        Args:
            event_type: Tipo de evento (ej. 'transcription_update', 'heartbeat').
            data: Payload del evento como diccionario serializable a JSON.

        Note:
            Si no hay broadcast_fn configurada, el método retorna silenciosamente.
            Esto permite usar el transcriptor sin WebSocket en tests.
        """
        if self._broadcast_fn:
            await self._broadcast_fn(event_type, data)


class Orchestrator:
    """Orquestador central del sistema Voice2Machine.

    Coordina todos los servicios del sistema (audio, transcripción, LLM, clipboard,
    notificaciones) usando Lazy Initialization. Reemplaza el patrón CQRS + DI Container
    con un enfoque más directo y fácil de depurar.

    El Orchestrator es el único punto de entrada para las operaciones de negocio.
    FastAPI delega todas las acciones aquí, manteniendo los endpoints "tontos".

    Attributes:
        _is_recording: Estado actual de grabación (True si está capturando audio).
        _model_loaded: True si el modelo Whisper está pre-cargado en VRAM.
        _broadcast_fn: Función opcional para emitir eventos a WebSocket clients.

    Note:
        Los servicios pesados (Whisper, LLM) se crean cuando se necesitan por primera
        vez, no al inicio. Esto permite que el servidor FastAPI arranque en ~100ms.
        Ver: docs/adr/002-orchestrator-pattern.md

    Example:
        >>> async def main():
        ...     orch = Orchestrator()
        ...     await orch.warmup()  # Pre-cargar Whisper en VRAM
        ...     response = await orch.toggle()
        ...     print(response.text)
    """

    def __init__(self, broadcast_fn: BroadcastFn | None = None) -> None:
        """Inicializa el orquestador con estado limpio y servicios diferidos.

        Args:
            broadcast_fn: Función opcional para enviar eventos en tiempo real
                a clientes WebSocket. Usada para transcripción provisional.

        Note:
            Los servicios reales (WhisperWorker, AudioRecorder, etc.) no se
            crean aquí. Se instancian en su primera llamada (Lazy Init).
        """
        # Estado interno
        self._is_recording: bool = False
        self._model_loaded: bool = False
        self._broadcast_fn = broadcast_fn

        # Servicios con lazy initialization (None hasta que se usen)
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
        """Obtiene el worker de Whisper, creándolo si no existe.

        El worker gestiona el modelo Whisper en VRAM, soportando políticas
        de keep-warm para eliminar latencia de carga en frío.

        Returns:
            PersistentWhisperWorker: Instancia configurada según config.toml.

        Note:
            La primera llamada puede tardar varios segundos mientras carga
            el modelo en GPU. Usa warmup() en startup para evitar esto.
        """
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
        """Obtiene el grabador de audio, creándolo si no existe.

        Utiliza la extensión Rust (v2m_engine) para captura de baja latencia.
        Ver: docs/adr/005-rust-audio-engine.md

        Returns:
            AudioRecorder: Instancia configurada para 16kHz mono (requerido por Whisper).
        """
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
        """Obtiene el transcriptor streaming, creándolo si no existe.

        Conecta AudioRecorder → WhisperWorker → WebSocket broadcast para
        proporcionar transcripción provisional en tiempo real.

        Returns:
            StreamingTranscriber: Instancia conectada al worker y recorder.
        """
        if self._transcriber is None:
            from v2m.infrastructure.streaming_transcriber import StreamingTranscriber

            # Adapter conecta eventos del transcriptor → WebSocket broadcast
            session_adapter = WebSocketSessionAdapter(self._broadcast_fn)

            self._transcriber = StreamingTranscriber(
                worker=self.worker,
                session_manager=session_adapter,
                recorder=self.recorder,
            )
        return self._transcriber

    @property
    def clipboard(self) -> LinuxClipboardAdapter:
        """Obtiene el servicio de clipboard del sistema.

        Returns:
            LinuxClipboardAdapter: Wrapper sobre xclip/wl-copy según el entorno.
        """
        if self._clipboard is None:
            from v2m.infrastructure.linux_adapters import LinuxClipboardAdapter

            self._clipboard = LinuxClipboardAdapter()
        return self._clipboard

    @property
    def notifications(self) -> LinuxNotificationService:
        """Obtiene el servicio de notificaciones de escritorio.

        Returns:
            LinuxNotificationService: Wrapper sobre notify-send/libnotify.
        """
        if self._notifications is None:
            from v2m.infrastructure.notification_service import LinuxNotificationService

            self._notifications = LinuxNotificationService()
        return self._notifications

    @property
    def llm_service(self) -> Any:
        """Obtiene el servicio LLM configurado, creándolo si no existe.

        Selecciona el backend según config.llm.backend:
        - "gemini": Google Gemini API (cloud)
        - "ollama": Ollama local
        - "local": Modelo embebido

        Returns:
            LLMService: Instancia del proveedor configurado.

        Note:
            El tipo de retorno es Any porque los backends tienen interfaces
            similares pero no idénticas. En producción, todos implementan
            process_text(str) -> str y translate_text(str, str) -> str.
        """
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

    # =========================================================================
    # Métodos Públicos (API Surface)
    # =========================================================================

    async def warmup(self) -> None:
        """Pre-carga el modelo Whisper en VRAM para eliminar latencia de arranque.

        Ejecuta la inicialización sincrónica del worker en un executor para no
        bloquear el event loop. Debe llamarse durante el lifecycle startup de
        FastAPI para tener el modelo "caliente" antes de la primera transcripción.

        Raises:
            RuntimeError: Si el worker no puede inicializarse (error silenciado
                en logs, el modelo se cargará on-demand si falla aquí).

        Example:
            >>> @asynccontextmanager
            ... async def lifespan(app: FastAPI):
            ...     await orchestrator.warmup()
            ...     yield
        """
        if self._model_loaded:
            return

        try:
            # Warmup sincrónico en el executor del worker
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.worker.initialize_sync)
            self._model_loaded = True
            logger.info("✅ Modelo Whisper precargado en VRAM")
        except Exception as e:
            logger.error(f"❌ Error en warmup del modelo: {e}")
            # No re-lanzamos - el modelo se cargará on-demand

    async def toggle(self) -> ToggleResponse:
        """Alterna el estado de grabación del sistema.

        Gestiona la lógica de cambio de estado: si el sistema está en reposo
        (idle), inicia la captura de audio y el streaming. Si está grabando,
        detiene la captura, finaliza la transcripción y copia al portapapeles.

        Este es el endpoint principal usado por los atajos de teclado.

        Returns:
            ToggleResponse: Objeto con el nuevo estado del sistema y, en caso
                de detenerse, el texto final transcrito.

        Raises:
            RuntimeError: Si los servicios de backend (Whisper/Audio) no responden.
                (Error capturado internamente y reportado en ToggleResponse.message)

        Example:
            >>> response = await orchestrator.toggle()
            >>> if response.status == "idle" and response.text:
            ...     print(f"Transcrito: {response.text}")
        """
        if not self._is_recording:
            return await self.start()
        else:
            return await self.stop()

    async def start(self) -> ToggleResponse:
        """Inicia la grabación de audio y el streaming de transcripción.

        Activa el AudioRecorder y el StreamingTranscriber. Crea un archivo
        flag en disco para que scripts externos puedan detectar el estado.

        Returns:
            ToggleResponse: Confirmación de inicio con status='recording'.

        Raises:
            RuntimeError: Si ya hay una grabación en curso o el micrófono
                no está disponible. (Error capturado en response.message)

        Note:
            Si ya está grabando, retorna inmediatamente sin error.
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
        """Detiene la grabación, finaliza transcripción y copia al portapapeles.

        Detiene el AudioRecorder, procesa el audio capturado con Whisper,
        y copia el texto resultante al portapapeles del sistema.

        Returns:
            ToggleResponse: Resultado con status='idle' y el texto transcrito
                en el campo 'text'. Si no se detectó voz, text=None.

        Raises:
            RuntimeError: Si no hay grabación en curso o Whisper falla.
                (Error capturado en response.message)

        Example:
            >>> response = await orchestrator.stop()
            >>> if response.text:
            ...     print(f"Copiado: {response.text}")
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
        """Procesa texto con LLM para limpieza, puntuación y formato.

        Envía el texto al backend LLM configurado (Gemini/Ollama/local) para
        refinamiento. El resultado se copia automáticamente al portapapeles.

        Args:
            text: Texto crudo a procesar (típicamente output de Whisper).

        Returns:
            LLMResponse: Texto refinado y nombre del backend usado.
                Si el LLM falla, retorna el texto original como fallback.

        Raises:
            ValueError: Si el texto está vacío (capturado internamente).

        Example:
            >>> response = await orchestrator.process_text("hola como estas")
            >>> print(response.text)  # "Hola, ¿cómo estás?"
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
        r"""Traduce texto a otro idioma usando el LLM configurado.

        Valida el idioma destino para prevenir inyección de prompts maliciosos,
        luego delega al backend LLM para traducción.

        Args:
            text: Texto a traducir en cualquier idioma.
            target_lang: Código o nombre del idioma destino (ej. 'en', 'español').
                Debe coincidir con regex: ^[a-zA-Z\s\-]{2,20}$

        Returns:
            LLMResponse: Texto traducido y backend usado.
                Si hay error, retorna texto original con backend='error'.

        Raises:
            ValueError: Si target_lang tiene caracteres inválidos (sanitizado).

        Example:
            >>> response = await orchestrator.translate_text("Buenos días", "en")
            >>> print(response.text)  # "Good morning"
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
        """Retorna el estado actual del daemon de forma sincrónica.

        Método ligero sin I/O, útil para health checks y polling.

        Returns:
            StatusResponse: Estado de grabación ('idle'|'recording'),
                flag booleano de grabación, y si el modelo está cargado.

        Example:
            >>> status = orchestrator.get_status()
            >>> if status.model_loaded:
            ...     print("Whisper listo")
        """
        from v2m.api import StatusResponse

        state = "recording" if self._is_recording else "idle"

        return StatusResponse(
            state=state,
            recording=self._is_recording,
            model_loaded=self._model_loaded,
        )

    async def shutdown(self) -> None:
        """Libera todos los recursos al apagar el servidor.

        Detiene grabación activa, descarga el modelo de VRAM, y cierra
        servicios de notificaciones. Llamado automáticamente en el
        lifecycle shutdown de FastAPI.

        Note:
            Los errores se logean pero no se re-lanzan para asegurar
            un apagado limpio incluso con fallos parciales.

        Example:
            >>> @asynccontextmanager
            ... async def lifespan(app: FastAPI):
            ...     await orchestrator.warmup()
            ...     yield
            ...     await orchestrator.shutdown()
        """
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
