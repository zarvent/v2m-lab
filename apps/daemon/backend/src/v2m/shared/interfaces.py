"""Interfaces compartidas para toda la aplicación."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SessionManagerInterface(Protocol):
    """Protocolo para emisión de eventos a clientes conectados."""

    async def emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Emite un evento a los clientes (ej. WebSocket)."""
        ...
