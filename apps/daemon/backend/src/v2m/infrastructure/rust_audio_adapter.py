import asyncio
import logging
import time
from collections.abc import AsyncIterator

import numpy as np

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

        # Buffer state
        buffer_list: list[np.ndarray] = []
        buffer_len = 0
        CHUNK_SIZE = 512  # Required for Silero VAD @ 16kHz

        try:
            while True:
                # Wait for data without blocking event loop
                await self._recorder.wait_for_data()

                # Retrieve all available data
                chunk = self._recorder.read_chunk()

                if len(chunk) > 0:
                    buffer_list.append(chunk)
                    buffer_len += len(chunk)

                    # Process accumulated data if enough for at least one chunk
                    if buffer_len >= CHUNK_SIZE:
                        # Merge all pending chunks
                        full_buffer = np.concatenate(buffer_list)

                        # Yield all complete chunks
                        start_idx = 0
                        while start_idx + CHUNK_SIZE <= len(full_buffer):
                            yield_chunk = full_buffer[start_idx : start_idx + CHUNK_SIZE]
                            yield VADChunk(timestamp=time.time(), audio=yield_chunk)
                            start_idx += CHUNK_SIZE

                        # Keep remainder
                        remainder = full_buffer[start_idx:]
                        buffer_list = [remainder] if len(remainder) > 0 else []
                        buffer_len = len(remainder)

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
