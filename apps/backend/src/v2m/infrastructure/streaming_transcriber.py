import asyncio
import logging
import time

import numpy as np

from v2m.config import config
from v2m.core.client_session import ClientSessionManager
from v2m.infrastructure.persistent_model import PersistentWhisperWorker

logger = logging.getLogger(__name__)


class StreamingTranscriber:
    """
    Manages real-time transcription streaming.
    Accumulates audio chunks and performs periodic inference on the buffer
    to provide 'provisional' text feedback (sub-second latency).
    """

    def __init__(self, worker: PersistentWhisperWorker, session_manager: ClientSessionManager, recorder=None):
        self.worker = worker
        self.session_manager = session_manager
        self.recorder = recorder  # Injected AudioRecorder
        self._streaming_task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._audio_buffer = []
        self._buffer_duration = 0.0

    async def start(self):
        """Starts the streaming transcription loop."""
        if self._streaming_task and not self._streaming_task.done():
            logger.warning("Streaming already active")
            return

        if not self.recorder:
            logger.error("No recorder provided to StreamingTranscriber")
            raise RuntimeError("No recorder")

        self.recorder.start()  # Ensure recorder is started
        self._stop_event.clear()
        self._audio_buffer = []
        self._buffer_duration = 0.0
        self._streaming_task = asyncio.create_task(self._loop())
        logger.info("Streaming started")

    async def stop(self) -> str:
        """Stops streaming and returns final transcription."""
        if not self._streaming_task:
            return ""

        logger.info("Stopping streaming...")
        self._stop_event.set()
        try:
            # Wait for loop to finish
            final_text = await self._streaming_task
            return final_text
        except asyncio.CancelledError:
            return ""
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            return ""
        finally:
            self.recorder.stop()  # Ensure recorder is stopped
            self._streaming_task = None

    async def _loop(self) -> str:
        """Main streaming loop."""
        last_inference_time = time.time()
        provisional_text = ""

        # Intervalo para "Provisional" feedback (500ms)
        # Menos de 500ms puede saturar la GPU y el worker sin beneficio visible
        inference_interval = 0.5

        try:
            while not self._stop_event.is_set():
                # Async wait for data (non-blocking)
                # Use executor if wait_for_data is blocking?
                # Rust method wait_for_data is async-compatible?
                # In lib.rs: `fn wait_for_data<'py>(&self, py: Python<'py>) -> PyResult<&'py PyAny>`
                # It returns an Awaitable.
                await self.recorder.wait_for_data()

                chunk = self.recorder.read_chunk()
                if len(chunk) > 0:
                    self._audio_buffer.append(chunk)
                    chunk_duration = len(chunk) / 16000
                    self._buffer_duration += chunk_duration

                # Check if we should infer
                now = time.time()
                if (now - last_inference_time) > inference_interval and self._buffer_duration > 0.5:
                    last_inference_time = now
                    # Run provisional inference
                    text = await self._infer_provisional()
                    if text and text != provisional_text:
                        provisional_text = text
                        await self.session_manager.emit_event("transcription_update", {"text": text, "final": False})

            # End of stream (Stop called)
            # Final inference on full buffer
            final_text = await self._infer_final()
            await self.session_manager.emit_event("transcription_update", {"text": final_text, "final": True})
            return final_text

        except Exception as e:
            logger.error(f"Streaming loop error: {e}")
            return ""

    async def _infer_provisional(self) -> str:
        """Runs fast inference on current buffer."""
        # Concatenate buffer
        if not self._audio_buffer:
            return ""

        full_audio = np.concatenate(self._audio_buffer)

        # Use Persistent Worker
        # For provisional, we can use less beams or faster settings?
        # But allow worker to manage.
        # We pass 'task="transcribe"'

        # We define a custom inference func that returns just text string
        whisper_config = config.transcription.whisper

        def _inference_func(model):
            # Same logic as WhisperTranscriptionService, but maybe optimization parameters
            segments, _ = model.transcribe(
                full_audio,
                language=whisper_config.language if whisper_config.language != "auto" else None,
                task="transcribe",
                beam_size=1,  # Faster greedy for provisional
                best_of=1,
                temperature=0.0,
                vad_filter=True,  # Use internal VAD to avoid processing silence?
            )
            # Materialize
            return list(segments)

        try:
            segments = await self.worker.run_inference(_inference_func)
            text = " ".join(s.text.strip() for s in segments if s.text)
            return text
        except Exception:
            return ""

    async def _infer_final(self) -> str:
        """Runs high-quality final inference."""
        if not self._audio_buffer:
            return ""

        full_audio = np.concatenate(self._audio_buffer)
        whisper_config = config.transcription.whisper

        def _inference_func(model):
            segments, _info = model.transcribe(
                full_audio,
                language=whisper_config.language if whisper_config.language != "auto" else None,
                task="transcribe",
                beam_size=whisper_config.beam_size,  # Full quality
                best_of=whisper_config.best_of,
                temperature=whisper_config.temperature,
                vad_filter=whisper_config.vad_filter,
                vad_parameters=whisper_config.vad_parameters.model_dump() if whisper_config.vad_filter else None,
            )
            return list(segments)

        try:
            segments = await self.worker.run_inference(_inference_func)
            text = " ".join(s.text.strip() for s in segments if s.text)
            if not text:
                logger.debug("transcripción final vacía (posiblemente filtrado por VAD o silencio)")
            return text
        except Exception:
            return ""
