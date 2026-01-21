"""Protocolo de Servicio de Transcripción.

Define la interfaz (Protocol) que deben implementar los servicios de transcripción
(como Whisper). Utiliza `typing.Protocol` para tipado estructural, desacoplando
completamente la implementación de la abstracción.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class TranscriptionService(Protocol):
    """Protocolo que define las operaciones de grabación y transcripción."""

    def start_recording(self) -> None:
        """Inicia el proceso de grabación de audio de forma asíncrona (non-blocking)
        o en un hilo separado.
        """
        ...

    async def stop_and_transcribe(self) -> str:
        """Detiene la grabación activa y procesa el audio para generar texto.

        Returns:
            str: El texto transcrito.

        Raises:
            RecordingError: Si ocurre un error durante la captura o procesamiento.
        """
        ...
