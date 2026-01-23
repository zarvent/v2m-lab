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

from v2m.shared.config import config
from v2m.shared.logging import logger

if TYPE_CHECKING:
    from v2m.api.schemas import LLMResponse, StatusResponse, ToggleResponse
    from v2m.features.audio.recorder import AudioRecorder
    from v2m.features.desktop.linux_adapters import LinuxClipboardAdapter
    from v2m.features.desktop.notification_service import LinuxNotificationService
    from v2m.features.transcription.persistent_model import PersistentWhisperWorker
    from v2m.features.audio.streaming_transcriber import StreamingTranscriber


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


from v2m.orchestration.recording_workflow import RecordingWorkflow
from v2m.orchestration.llm_workflow import LLMWorkflow


class Orchestrator:
    """Orquestador central (Facade delegando a Workflows)."""

    def __init__(self, broadcast_fn: BroadcastFn | None = None) -> None:
        self.recording_wf = RecordingWorkflow(broadcast_fn=broadcast_fn)
        self.llm_wf = LLMWorkflow()

    async def warmup(self) -> None:
        await self.recording_wf.warmup()

    async def toggle(self) -> ToggleResponse:
        return await self.recording_wf.toggle()

    async def start(self) -> ToggleResponse:
        return await self.recording_wf.start()

    async def stop(self) -> ToggleResponse:
        return await self.recording_wf.stop()

    async def process_text(self, text: str) -> LLMResponse:
        return await self.llm_wf.process_text(text)

    async def translate_text(self, text: str, target_lang: str) -> LLMResponse:
        return await self.llm_wf.translate_text(text, target_lang)

    def get_status(self) -> StatusResponse:
        return self.recording_wf.get_status()

    async def shutdown(self) -> None:
        await self.recording_wf.shutdown()
