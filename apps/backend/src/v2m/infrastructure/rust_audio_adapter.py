import asyncio
import logging
import time
from collections.abc import AsyncIterator

try:
    import v2m_engine
except ImportError:
    v2m_engine = None

from v2m.domain.audio_stream import AudioStreamPort, VADChunk


# Assuming v2m.domain.errors exists or we use standard exceptions
class RecordingError(Exception):
    pass


logger = logging.getLogger(__name__)


class RustAudioStream(AudioStreamPort):
    def __init__(self, sample_rate: int = 16000):
        if v2m_engine is None:
            raise ImportError("v2m_engine extension not available")
        self._recorder = v2m_engine.AudioRecorder(sample_rate)

    async def __aiter__(self) -> AsyncIterator[VADChunk]:
        logger.info("Starting Rust audio stream")
        try:
            self._recorder.start()
        except Exception as e:
            raise RecordingError(f"Failed to start Rust recorder: {e}") from e

        try:
            while True:
                # Wait for data without blocking event loop
                await self._recorder.wait_for_data()

                # Retrieve all available data
                chunk = self._recorder.read_chunk()
                # Ensure chunk is numpy array (it is from Rust side)
                if len(chunk) > 0:
                    yield VADChunk(timestamp=time.time(), audio=chunk)
        except asyncio.CancelledError:
            logger.info("Audio stream cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in audio stream: {e}")
            raise
        finally:
            logger.info("Stopping Rust audio stream")
            try:
                self._recorder.stop()
            except Exception as e:
                logger.error(f"Error stopping recorder: {e}")
