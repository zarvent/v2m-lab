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

Este módulo implementa la interfaz `TranscriptionService` utilizando la librería
`faster-whisper`.
Maneja:
- Gestión de la grabación de audio vía `AudioRecorder`.
- Carga diferida (lazy loading) del modelo Whisper para optimizar el inicio.
- Transcripción de audio en memoria (sin archivos intermedios si es posible).
"""

from faster_whisper import WhisperModel

from v2m.application.transcription_service import TranscriptionService
from v2m.config import config
from v2m.core.logging import logger
from v2m.domain.errors import RecordingError
from v2m.infrastructure.audio.recorder import AudioRecorder


class WhisperTranscriptionService(TranscriptionService):
    """
    Implementación concreta de `TranscriptionService` utilizando `faster-whisper`.
    """

    def __init__(self) -> None:
        """
        Inicializa el servicio de transcripción.
        Nota: El modelo no se carga en este punto para mejorar el tiempo de arranque (lazy).
        """
        self._model: WhisperModel | None = None
        # Acceder a la configuración a través de la nueva estructura anidada
        self.recorder = AudioRecorder(device_index=config.transcription.whisper.audio_device_index)

    @property
    def model(self) -> WhisperModel:
        """
        Carga diferida (Lazy Load) del modelo Whisper.

        Returns:
            WhisperModel: La instancia del modelo cargada y lista para usar.
        """
        if self._model is None:
            logger.info("cargando modelo whisper...")
            whisper_config = config.transcription.whisper

            try:
                self._model = WhisperModel(
                    whisper_config.model,
                    device=whisper_config.device,
                    compute_type=whisper_config.compute_type,
                    device_index=whisper_config.device_index,
                    num_workers=whisper_config.num_workers,
                )
                logger.info(f"modelo whisper cargado en {whisper_config.device}")
            except Exception as e:
                logger.error(f"error cargando modelo en {whisper_config.device}: {e}")
                if whisper_config.device == "cuda":
                    logger.warning("intentando fallback a cpu...")
                    try:
                        self._model = WhisperModel(
                            whisper_config.model,
                            device="cpu",
                            compute_type="int8",  # CPU usualmente requiere int8 para velocidad
                            num_workers=whisper_config.num_workers,
                        )
                        logger.info("modelo whisper cargado en cpu (fallback)")
                    except Exception as e2:
                        logger.critical(f"fallo crítico: no se pudo cargar el modelo ni en cpu: {e2}")
                        raise e2
                else:
                    raise e

        return self._model

    def start_recording(self) -> None:
        """
        Inicia la grabación de audio.

        Raises:
            RecordingError: Si falla el inicio de la grabación.
        """
        try:
            self.recorder.start()
            logger.info("grabación iniciada")
        except RecordingError as e:
            logger.error(f"error iniciando grabación: {e}")
            raise e

    def stop_and_transcribe(self) -> str:
        """
        Detiene la grabación y transcribe el audio capturado.

        Returns:
            str: El texto transcrito.

        Raises:
            RecordingError: Si no se grabó audio o falló la grabación.
        """
        try:
            # Detener grabación y obtener datos sin guardar a disco (in-memory)
            audio_data = self.recorder.stop(copy_data=False)
        except RecordingError as e:
            logger.error(f"error deteniendo grabación: {e}")
            raise e

        if audio_data.size == 0:
            raise RecordingError("no se grabó audio o el buffer está vacío")

        # --- Transcripción con Whisper ---
        logger.info("transcribiendo audio...")
        whisper_config = config.transcription.whisper

        try:
            # 1. Lógica de auto-detección
            lang = whisper_config.language
            if lang == "auto":
                lang = None  # None habilita la auto-detección en faster-whisper

            # 2. Prompt inicial para guiar el contexto del modelo
            initial_prompt = "Transcripción."

            segments, info = self.model.transcribe(
                audio_data,
                language=lang,
                task="transcribe",
                initial_prompt=initial_prompt,
                beam_size=whisper_config.beam_size,
                best_of=whisper_config.best_of,
                temperature=whisper_config.temperature,
                vad_filter=whisper_config.vad_filter,
                vad_parameters=whisper_config.vad_parameters.model_dump() if whisper_config.vad_filter else None,
            )

            if lang is None:
                logger.info(f"idioma detectado {info.language} probabilidad {info.language_probability:.2f}")

            # Unir segmentos eficientemente
            text = " ".join(segment.text.strip() for segment in segments)
            logger.info("transcripción completada")
            return text

        except Exception as e:
            logger.error(f"error durante la transcripción: {e}")
            raise e
        finally:
            pass
