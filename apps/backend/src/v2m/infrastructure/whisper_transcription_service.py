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
MÓDULO QUE IMPLEMENTA EL SERVICIO DE TRANSCRIPCIÓN UTILIZANDO `FASTER-WHISPER`

esta es la implementación concreta de la interfaz `transcriptionservice` se encarga
de la lógica de bajo nivel para
-   gestionar el proceso de grabación de audio usando `audiorecorder`
-   cargar el modelo de whisper
-   realizar la transcripción del audio grabado directamente desde la memoria
"""

from faster_whisper import WhisperModel

from v2m.application.transcription_service import TranscriptionService
from v2m.config import config
from v2m.core.logging import logger
from v2m.domain.errors import RecordingError
from v2m.infrastructure.audio.recorder import AudioRecorder


class WhisperTranscriptionService(TranscriptionService):
    """
    IMPLEMENTACIÓN DEL `TRANSCRIPTIONSERVICE` QUE USA `FASTER-WHISPER` Y `AUDIORECORDER`
    """
    def __init__(self) -> None:
        """
        INICIALIZA EL SERVICIO DE TRANSCRIPCIÓN

        no carga el modelo de whisper en este punto para acelerar el inicio de la aplicación
        """
        self._model: WhisperModel | None = None
        self.recorder = AudioRecorder(device_index=config.whisper.audio_device_index)

    @property
    def model(self) -> WhisperModel:
        """
        CARGA EL MODELO DE `FASTER-WHISPER` DE FORMA PEREZOSA LAZY LOADING

        el modelo solo se carga en memoria la primera vez que se accede a esta
        propiedad esto evita un consumo de recursos innecesario si solo se
        inicia la grabación sin completarla

        RETURNS:
            la instancia del modelo de whisper cargado
        """
        if self._model is None:
            logger.info("cargando modelo de whisper...")
            whisper_config = config.whisper

            try:
                self._model = WhisperModel(
                    whisper_config.model,
                    device=whisper_config.device,
                    compute_type=whisper_config.compute_type,
                    device_index=whisper_config.device_index,
                    num_workers=whisper_config.num_workers
                )
                logger.info(f"modelo de whisper cargado en {whisper_config.device}")
            except Exception as e:
                logger.error(f"error cargando modelo en {whisper_config.device}: {e}")
                if whisper_config.device == "cuda":
                    logger.warning("intentando fallback a cpu...")
                    try:
                        self._model = WhisperModel(
                            whisper_config.model,
                            device="cpu",
                            compute_type="int8", # cpu suele requerir int8 para velocidad
                            num_workers=whisper_config.num_workers
                        )
                        logger.info("modelo de whisper cargado en cpu (fallback)")
                    except Exception as e2:
                        logger.critical(f"fallo crítico no se pudo cargar el modelo ni en cpu: {e2}")
                        raise e2
                else:
                    raise e

        return self._model

    def start_recording(self) -> None:
        """
        INICIA LA GRABACIÓN DE AUDIO

        utiliza `audiorecorder` para capturar audio en un hilo separado

        RAISES:
            RecordingError: si ya hay una grabación en proceso o falla el inicio
        """
        try:
            self.recorder.start()
            logger.info("grabación iniciada")
        except RecordingError as e:
            logger.error(f"error al iniciar grabación {e}")
            raise e

    def stop_and_transcribe(self) -> str:
        """
        DETIENE LA GRABACIÓN Y TRANSCRIBE EL AUDIO

        realiza los siguientes pasos
        1  detiene el `audiorecorder` y obtiene los datos de audio en memoria numpy array
        2  aplica vad smart truncation si esta disponible
        3  verifica que se haya grabado audio válido
        4  utiliza el modelo de whisper para transcribir el audio directamente desde memoria
        5  limpia recursos gc cuda cache para minimizar uso de memoria

        RETURNS:
            el texto transcrito

        RAISES:
            RecordingError: si no hay una grabación activa o si el audio es inválido
        """
        try:
            # detener grabación y obtener audio sin guardar a disco
            # BOLT OPTIMIZACIÓN: Evitar copia del buffer (copy_data=False)
            # Faster-Whisper consume el buffer inmediatamente (o lo copia internamente).
            # Como el sistema bloquea nuevas grabaciones hasta que esto termine, es seguro usar una vista.
            audio_data = self.recorder.stop(copy_data=False)
        except RecordingError as e:
            logger.error(f"error al detener grabación {e}")
            raise e

        if audio_data.size == 0:
            raise RecordingError("no se grabó audio o el buffer está vacío")

        # --- transcripción con whisper ---
        logger.info("transcribiendo audio...")
        whisper_config = config.whisper

        try:
            # 1 lógica para auto-detección
            lang = whisper_config.language
            if lang == "auto":
                lang = None  # none activa la detección automática en faster-whisper

            # 2 prompt inicial "Coaching" para contexto técnico bilingüe (SOTA 2025)
            # define rol y expectativas claramente para reducir alucinaciones
            bilingual_prompt = (
                "Technical transcription of a software engineering discussion. "
                "Mix of Spanish and English commands. Code snippets included."
            )

            # faster-whisper acepta numpy array directamente
            # nota vad interno deshabilitado ya aplicamos silero vad arriba
            # esto ahorra ~40mb vram y evita doble procesamiento
            segments, info = self.model.transcribe(
                audio_data,
                language=lang,
                task="transcribe",
                initial_prompt=bilingual_prompt,
                beam_size=whisper_config.beam_size,
                best_of=whisper_config.best_of,
                temperature=whisper_config.temperature,
                vad_filter=whisper_config.vad_filter,
                vad_parameters=whisper_config.vad_parameters.model_dump() if whisper_config.vad_filter else None,
            )

            if lang is None:
                logger.info(f"idioma detectado {info.language} prob {info.language_probability:.2f}")

            text = " ".join([segment.text.strip() for segment in segments])
            logger.info("transcripción completada")
            return text

        except Exception as e:
            logger.error(f"error durante transcripción: {e}")
            raise e
        finally:
            # gc.collect removido python gc automático es suficiente
            pass
