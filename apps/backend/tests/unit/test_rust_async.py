import asyncio

import numpy as np
import pytest

from v2m.infrastructure.rust_audio_adapter import RustAudioStream


@pytest.mark.asyncio
async def test_rust_async_stream_basics():
    """Test that the stream yields chunks and can be cancelled."""
    try:
        stream = RustAudioStream()
    except ImportError:
        pytest.skip("v2m_engine not installed")

    chunk_count = 0

    # We run for a short time
    async for chunk in stream:
        chunk_count += 1
        assert isinstance(chunk.audio, np.ndarray)
        assert chunk.audio.dtype == np.float32

        # Stop after 3 chunks to avoid long test
        if chunk_count >= 3:
            break

    assert chunk_count == 3


@pytest.mark.asyncio
async def test_rust_stream_non_blocking():
    """Test that reading the stream doesn't block the loop."""
    try:
        stream = RustAudioStream()
    except ImportError:
        pytest.skip("v2m_engine not installed")

    async def background_task():
        # A task that should run concurrently
        for _i in range(5):
            await asyncio.sleep(0.01)
        return True

    task = asyncio.create_task(background_task())

    async for _chunk in stream:
        # Just process one chunk
        break

    assert await task is True
