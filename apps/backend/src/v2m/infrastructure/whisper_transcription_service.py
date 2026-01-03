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
Whisper Transcription Service Implementation.

This module implements the `TranscriptionService` interface using `faster-whisper`.
It handles:
- Audio recording management via `AudioRecorder`.
- Lazy loading of the Whisper model.
- In-memory audio transcription.
"""

from faster_whisper import WhisperModel

from v2m.application.transcription_service import TranscriptionService
from v2m.config import config
from v2m.core.logging import logger
from v2m.domain.errors import RecordingError
from v2m.infrastructure.audio.recorder import AudioRecorder


class WhisperTranscriptionService(TranscriptionService):
    """
    Implementation of `TranscriptionService` using `faster-whisper`.
    """

    def __init__(self) -> None:
        """
        Initializes the transcription service.
        The model is not loaded at this point to improve startup time.
        """
        self._model: WhisperModel | None = None
        # Access config via transcription.whisper
        self.recorder = AudioRecorder(device_index=config.transcription.whisper.audio_device_index)

    @property
    def model(self) -> WhisperModel:
        """
        Lazy loads the `faster-whisper` model.

        Returns:
            The loaded WhisperModel instance.
        """
        if self._model is None:
            logger.info("loading whisper model...")
            whisper_config = config.transcription.whisper

            try:
                self._model = WhisperModel(
                    whisper_config.model,
                    device=whisper_config.device,
                    compute_type=whisper_config.compute_type,
                    device_index=whisper_config.device_index,
                    num_workers=whisper_config.num_workers,
                )
                logger.info(f"whisper model loaded on {whisper_config.device}")
            except Exception as e:
                logger.error(f"error loading model on {whisper_config.device}: {e}")
                if whisper_config.device == "cuda":
                    logger.warning("attempting cpu fallback...")
                    try:
                        self._model = WhisperModel(
                            whisper_config.model,
                            device="cpu",
                            compute_type="int8",  # CPU usually requires int8 for speed
                            num_workers=whisper_config.num_workers,
                        )
                        logger.info("whisper model loaded on cpu (fallback)")
                    except Exception as e2:
                        logger.critical(f"critical failure: could not load model on cpu either: {e2}")
                        raise e2
                else:
                    raise e

        return self._model

    def start_recording(self) -> None:
        """
        Starts audio recording.

        Raises:
            RecordingError: If recording fails to start.
        """
        try:
            self.recorder.start()
            logger.info("recording started")
        except RecordingError as e:
            logger.error(f"error starting recording: {e}")
            raise e

    def stop_and_transcribe(self) -> str:
        """
        Stops recording and transcribes the audio.

        Returns:
            The transcribed text.

        Raises:
            RecordingError: If no audio was recorded or recording failed.
        """
        try:
            # Stop recording and get audio data without saving to disk
            audio_data = self.recorder.stop(copy_data=False)
        except RecordingError as e:
            logger.error(f"error stopping recording: {e}")
            raise e

        if audio_data.size == 0:
            raise RecordingError("no audio recorded or buffer empty")

        # --- Transcription with Whisper ---
        logger.info("transcribing audio...")
        whisper_config = config.transcription.whisper

        try:
            # 1. Auto-detection logic
            lang = whisper_config.language
            if lang == "auto":
                lang = None  # None enables auto-detection in faster-whisper

            # 2. Initial prompt to guide the model (context)
            # Using a generic prompt if not configured.
            initial_prompt = "Transcription."

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
                logger.info(f"detected language {info.language} prob {info.language_probability:.2f}")

            # Join segments efficiently
            text = " ".join(segment.text.strip() for segment in segments)
            logger.info("transcription completed")
            return text

        except Exception as e:
            logger.error(f"error during transcription: {e}")
            raise e
        finally:
            pass
