import asyncio
import logging
from typing import Any

from v2m.core.ipc_protocol import IPCResponse, send_ipc_message

logger = logging.getLogger(__name__)


class ClientSessionManager:
    """
    Manages the active client connection for sending unsolicited events (streaming).
    Assumes single active client session (Last Write Wins).
    """

    def __init__(self):
        self._writer = None
        self._lock = asyncio.Lock()

    async def register(self, writer: asyncio.StreamWriter):
        async with self._lock:
            self._writer = writer
            logger.debug("Client session registered")

    async def unregister(self):
        async with self._lock:
            self._writer = None
            logger.debug("Client session unregistered")

    async def emit_event(self, event_type: str, data: dict[str, Any]):
        """Emit an event to the connected client."""
        async with self._lock:
            if not self._writer:
                # Silent failure if no client (expected if client disconnects)
                return

            # Protocol extensions: Events are identified by status="event"
            response = IPCResponse(status="event", data={"type": event_type, **data})
            try:
                await send_ipc_message(self._writer, response)
            except Exception as e:
                logger.error(f"Failed to emit event: {e}")
