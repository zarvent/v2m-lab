# This file is part of voice2machine.
#
# voice2machine is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# voice2machine is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with voice2machine.  If not, see <https://www.gnu.org/licenses/>.

"""
Implementación del Servicio de Transcripción Whisper.

Este módulo implementa la interfaz `TranscriptionService` utilizando
`persistent_model` para gestionar el ciclo de vida del modelo de forma eficiente
y `streaming_transcriber` para feedback en tiempo real.
"""

import asyncio

from v2m.application.transcription_service import TranscriptionService
from v2m.config import config
from v2m.core.client_session import ClientSessionManager
from v2m.core.logging import logger
from v2m.domain.errors import RecordingError
from v2m.infrastructure.audio.recorder import AudioRecorder
from v2m.infrastructure.persistent_model import PersistentWhisperWorker
from v2m.infrastructure.streaming_transcriber import StreamingTranscriber


class WhisperTranscriptionService(TranscriptionService):
    """
    Implementación concreta de `TranscriptionService` utilizando `faster-whisper`
    gestionado por un worker persistente. Soporta streaming.
    """

    def __init__(self, worker: PersistentWhisperWorker, session_manager: ClientSessionManager) -> None:
        """
        Inicializa el servicio de transcripción.

        Args:
            worker: Worker persistente que gestiona el modelo Whisper.
            session_manager: Gestor de sesión IPC para eventos de streaming.
        """
        self.worker = worker
        self.session_manager = session_manager
        # Acceder a la configuración a través de la nueva estructura anidada
        self.recorder = AudioRecorder(device_index=config.transcription.whisper.audio_device_index)

        # Delegar lógica de grabación/transcripción al streamer
        self.streamer = StreamingTranscriber(worker, session_manager, self.recorder)
        self._streaming_task = None  # Track streaming task reference

    def start_recording(self) -> None:
        """
        Inicia la grabación de audio y el streaming.

        Raises:
            RecordingError: Si falla el inicio de la grabación.
        """
        try:
            # Lanzar tarea de streaming (async desde contexto sync)
            try:
                loop = asyncio.get_running_loop()
                self._streaming_task = loop.create_task(self.streamer.start())
            except RuntimeError:
                # Si no hay loop (ej. tests sync), no podemos iniciar streaming async
                # Fallback a grabación normal?
                # La arquitectura Daemon siempre corre en loop.
                # Tests deben usar pytest-asyncio.
                raise RecordingError("No event loop found for streaming start") from None

            logger.info("grabación y streaming iniciados")
        except Exception as e:
            logger.error(f"error iniciando grabación: {e}")
            raise RecordingError(str(e)) from e

    async def stop_and_transcribe(self) -> str:
        """
        Detiene la grabación y devuelve el resultado final.

        Returns:
            str: El texto transcrito.

        Raises:
            RecordingError: Si no se grabó audio o falló la grabación.
        """
        try:
            text = await self.streamer.stop()
            logger.info("transcripción completada (stream stop)")
            return text
        except Exception as e:
            logger.error(f"error deteniendo/transcribiendo: {e}")
            raise RecordingError(str(e)) from e
