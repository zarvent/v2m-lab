"""
API REST para Voice2Machine (SOTA 2026).

Reemplaza el sistema IPC manual (sockets Unix + framing binario) por endpoints HTTP
estándar. Un Junior puede probar con `curl`, un Senior puede extender con WebSockets.

Endpoints:
    POST /toggle         - Iniciar/detener grabación (toggle)
    POST /start          - Iniciar grabación explícitamente
    POST /stop           - Detener grabación y transcribir
    POST /llm/process    - Refinar texto con LLM
    POST /llm/translate  - Traducir texto con LLM
    GET  /status         - Estado actual del daemon
    GET  /health         - Health check (para scripts/systemd)
    WS   /ws/events      - Stream de eventos (transcripción provisional)

Ejemplo de uso:
    curl -X POST http://localhost:8765/toggle | jq
    curl http://localhost:8765/status | jq
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from v2m.services.orchestrator import Orchestrator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from v2m.core.logging import logger

# =============================================================================
# Modelos de Request/Response (Pydantic V2)
# =============================================================================


class ToggleResponse(BaseModel):
    """Respuesta del endpoint /toggle."""

    status: str = Field(description="Estado actual: 'recording' o 'idle'")
    message: str = Field(description="Mensaje descriptivo para el usuario")
    text: str | None = Field(default=None, description="Texto transcrito (solo en stop)")


class StatusResponse(BaseModel):
    """Respuesta del endpoint /status."""

    state: str = Field(description="Estado del daemon: 'idle', 'recording', 'processing'")
    recording: bool = Field(description="True si está grabando actualmente")
    model_loaded: bool = Field(description="True si el modelo Whisper está cargado")


class ProcessTextRequest(BaseModel):
    """Request para /llm/process."""

    text: str = Field(min_length=1, max_length=10000, description="Texto a procesar")


class TranslateTextRequest(BaseModel):
    """Request para /llm/translate."""

    text: str = Field(min_length=1, max_length=10000, description="Texto a traducir")
    target_lang: str = Field(default="en", description="Idioma destino (ej. 'en', 'es')")


class LLMResponse(BaseModel):
    """Respuesta de endpoints LLM."""

    text: str = Field(description="Texto procesado/traducido")
    backend: str = Field(description="Backend usado: 'gemini', 'ollama', 'local'")


class HealthResponse(BaseModel):
    """Respuesta del endpoint /health."""

    status: str = Field(default="ok")
    version: str = Field(default="0.2.0")


# =============================================================================
# Estado Global (Singleton lazy - reemplaza DI Container)
# =============================================================================


class DaemonState:
    """
    Estado global del daemon.

    Lazy initialization: los servicios se crean cuando se necesitan por primera vez.
    Esto permite que el servidor arranque rápido y cargue el modelo en background.
    """

    def __init__(self):
        self._orchestrator: Orchestrator | None = None
        self._websocket_clients: set[WebSocket] = set()

    @property
    def orchestrator(self) -> Orchestrator:
        """Lazy initialization del orquestador."""
        if self._orchestrator is None:
            from v2m.services.orchestrator import Orchestrator

            self._orchestrator = Orchestrator(broadcast_fn=self.broadcast_event)
        return self._orchestrator

    async def broadcast_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Envía evento a todos los clientes WebSocket conectados."""
        if not self._websocket_clients:
            return

        message = {"event": event_type, "data": data}
        disconnected: list[WebSocket] = []

        for ws in self._websocket_clients:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)

        # Cleanup de conexiones muertas
        for ws in disconnected:
            self._websocket_clients.discard(ws)


# Singleton global
_state = DaemonState()


# =============================================================================
# Lifecycle (Startup/Shutdown)
# =============================================================================


# Almacenar referencia a tareas background (RUF006)
_background_tasks: set[asyncio.Task[None]] = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación.

    Startup: Carga el modelo Whisper en VRAM (warmup).
    Shutdown: Libera recursos GPU.
    """
    logger.info("🚀 Iniciando V2M API Server...")

    # Warmup del modelo en background (no bloquea el servidor)
    task = asyncio.create_task(_warmup_model())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    yield

    # Shutdown
    logger.info("🛑 Apagando V2M API Server...")
    if _state._orchestrator:
        await _state.orchestrator.shutdown()


async def _warmup_model() -> None:
    """Pre-carga el modelo Whisper en VRAM."""
    try:
        logger.info("⏳ Cargando modelo Whisper en GPU (warmup)...")
        await _state.orchestrator.warmup()
        logger.info("✅ Modelo Whisper listo")
    except Exception as e:
        logger.error(f"❌ Error en warmup: {e}")


# =============================================================================
# FastAPI App
# =============================================================================


app = FastAPI(
    title="Voice2Machine API",
    description="Transcripción de voz local con Whisper (SOTA 2026)",
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)


# =============================================================================
# Endpoints
# =============================================================================


@app.post("/toggle", response_model=ToggleResponse)
async def toggle_recording() -> ToggleResponse:
    """
    Toggle de grabación (iniciar/detener).

    Si no está grabando → inicia grabación.
    Si está grabando → detiene y transcribe.

    Este es el endpoint principal que usa el atajo de teclado.
    """
    return await _state.orchestrator.toggle()


@app.post("/start", response_model=ToggleResponse)
async def start_recording() -> ToggleResponse:
    """Inicia grabación explícitamente."""
    return await _state.orchestrator.start()


@app.post("/stop", response_model=ToggleResponse)
async def stop_recording() -> ToggleResponse:
    """Detiene grabación y transcribe."""
    return await _state.orchestrator.stop()


@app.post("/llm/process", response_model=LLMResponse)
async def process_text(request: ProcessTextRequest) -> LLMResponse:
    """
    Procesa texto con LLM (limpieza, puntuación, formato).

    El backend se selecciona según config.toml (gemini/ollama/local).
    """
    return await _state.orchestrator.process_text(request.text)


@app.post("/llm/translate", response_model=LLMResponse)
async def translate_text(request: TranslateTextRequest) -> LLMResponse:
    """Traduce texto con LLM."""
    return await _state.orchestrator.translate_text(request.text, request.target_lang)


@app.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """Retorna estado actual del daemon."""
    return _state.orchestrator.get_status()


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check para systemd/scripts."""
    return HealthResponse()


# =============================================================================
# WebSocket (Streaming de eventos)
# =============================================================================


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket) -> None:
    """
    Stream de eventos en tiempo real.

    Eventos emitidos:
    - transcription_update: {text: str, final: bool}
    - heartbeat: {timestamp: float, state: str}
    """
    await websocket.accept()
    _state._websocket_clients.add(websocket)
    logger.info(f"📡 WebSocket conectado (total: {len(_state._websocket_clients)})")

    try:
        # Keep-alive loop
        while True:
            # Esperamos mensajes del cliente (ping/pong o comandos futuros)
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _state._websocket_clients.discard(websocket)
        logger.info(f"📡 WebSocket desconectado (total: {len(_state._websocket_clients)})")
