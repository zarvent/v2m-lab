"""Interfaces (Protocolos) para adaptadores de escritorio.

Define los contratos que deben cumplir los adaptadores para interactuar con el
sistema operativo (Clipboard, Notificaciones).
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ClipboardInterface(Protocol):
    """Protocolo para operaciones del portapapeles del sistema."""

    def copy(self, text: str) -> None:
        """Copia el texto al portapapeles."""
        ...

    def paste(self) -> str:
        """Obtiene el contenido del portapapeles."""
        ...


@runtime_checkable
class NotificationInterface(Protocol):
    """Protocolo para el sistema de notificaciones del escritorio."""

    def notify(self, title: str, message: str) -> None:
        """Envía una notificación visual."""
        ...
