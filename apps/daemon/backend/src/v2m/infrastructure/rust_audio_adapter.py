"""DEPRECATED: Este módulo no se usa en producción.

RustAudioStream fue reemplazado por la arquitectura Producer-Consumer
en streaming_transcriber.py que usa AudioRecorder directamente.

Se mantiene para compatibilidad con tests existentes.
Programado para eliminación en v2.0.
"""

import asyncio
import logging
import time
import warnings
from collections.abc import AsyncIterator

import numpy as np

from v2m.domain.audio_stream import AudioStreamPort, VADChunk

warnings.warn(
    "rust_audio_adapter.RustAudioStream está deprecado. "
    "Usar AudioRecorder con StreamingTranscriber.",
    DeprecationWarning,
    stacklevel=2,
)

try:
    import v2m_engine
except ImportError:
    v2m_engine = None


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
        chunk_size = 512  # Required for Silero VAD @ 16kHz

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
                    if buffer_len >= chunk_size:
                        # Merge all pending chunks
                        full_buffer = np.concatenate(buffer_list)

                        # Yield all complete chunks
                        start_idx = 0
                        while start_idx + chunk_size <= len(full_buffer):
                            yield_chunk = full_buffer[start_idx : start_idx + chunk_size]
                            yield VADChunk(timestamp=time.time(), audio=yield_chunk)
                            start_idx += chunk_size

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
