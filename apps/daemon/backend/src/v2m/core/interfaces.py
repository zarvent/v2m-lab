"""
Interfaces (Protocolos) para los adaptadores del sistema.

Este módulo define los contratos que deben cumplir los adaptadores de infraestructura
para interactuar con el sistema operativo (Clipboard, Notificaciones).
Siguiendo las mejores prácticas de 2026, utilizamos `typing.Protocol` para definir
estas interfaces, permitiendo un tipado estructural flexible y desacoplado.

Interfaces definidas:
    - ``ClipboardInterface``: Operaciones del portapapeles.
    - ``NotificationInterface``: Envío de notificaciones al escritorio.
    - ``SessionManagerInterface``: Emisión de eventos a clientes conectados.
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SessionManagerInterface(Protocol):
    """
    Protocolo para emisión de eventos a clientes conectados.

    Define el contrato para cualquier adaptador que envíe eventos streaming
    (WebSocket, IPC, etc.) durante la transcripción en tiempo real.
    """

    async def emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """
        Emite un evento a los clientes conectados.

        Args:
            event_type: Tipo de evento (ej. "transcription_update", "heartbeat").
            data: Payload del evento como diccionario.
        """
        ...


@runtime_checkable
class ClipboardInterface(Protocol):
    """
    Protocolo para operaciones del portapapeles del sistema.

    Define el contrato estructural para cualquier adaptador que gestione
    el portapapeles (X11, Wayland, Windows, macOS).
    """

    def copy(self, text: str) -> None:
        """
        Copia el texto proporcionado al portapapeles del sistema.

        Args:
            text: El texto a copiar.
        """
        ...

    def paste(self) -> str:
        """
        Obtiene el contenido actual del portapapeles del sistema.

        Returns:
            str: El texto contenido en el portapapeles.
        """
        ...


@runtime_checkable
class NotificationInterface(Protocol):
    """
    Protocolo para el sistema de notificaciones del escritorio.

    Define el contrato estructural para cualquier adaptador que envíe
    alertas visuales al usuario.
    """

    def notify(self, title: str, message: str) -> None:
        """
        Envía una notificación visual al escritorio del usuario.

        Args:
            title: El título de la notificación.
            message: El cuerpo del mensaje.
        """
        ...
