
import pytest
import asyncio
import numpy as np
from unittest.mock import MagicMock, AsyncMock
from v2m.infrastructure.streaming_transcriber import StreamingTranscriber

@pytest.fixture
def mock_worker():
    worker = AsyncMock()
    # Mock inference to return fake segments
    async def fake_inference(func):
        # We need to simulate Faster Whisper result
        # The transcriber expects a list with 'text' attribute
        Segment = MagicMock()
        Segment.text = " hello world"
        return [Segment]
    worker.run_inference = fake_inference
    return worker

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def mock_recorder():
    recorder = MagicMock()
    async def wait_side_effect(*args, **kwargs):
        await asyncio.sleep(0.01) # Simulate IO delay

    recorder.wait_for_data = AsyncMock(side_effect=wait_side_effect)

    # Simulate a few chunks then return empty
    chunks = [np.zeros(16000, dtype=np.float32) for _ in range(5)] # 5 seconds
    iter_chunks = iter(chunks)

    def read():
        try:
            return next(iter_chunks)
        except StopIteration:
            return np.array([], dtype=np.float32)

    recorder.read_chunk = read
    recorder.start = MagicMock()
    recorder.stop = MagicMock()
    return recorder

@pytest.mark.asyncio
async def test_streaming_lifecycle(mock_worker, mock_session, mock_recorder):
    streamer = StreamingTranscriber(mock_worker, mock_session, mock_recorder)

    await streamer.start()
    mock_recorder.start.assert_called_once()

    # Let it run for a bit
    await asyncio.sleep(0.6) # Enough for inference interval (0.5s)

    text = await streamer.stop()

    mock_recorder.stop.assert_called_once()
    mock_session.emit_event.assert_called()
    assert text == "hello world"

@pytest.mark.asyncio
async def test_streaming_emits_partials(mock_worker, mock_session, mock_recorder):
    streamer = StreamingTranscriber(mock_worker, mock_session, mock_recorder)

    # Mock inference to return different things
    async def fake_infer_prov(func):
        S = MagicMock(); S.text=" hello"; return [S]

    mock_worker.run_inference = fake_infer_prov

    await streamer.start()
    await asyncio.sleep(0.7)

    # Verify provisional event
    calls = [c for c in mock_session.emit_event.call_args_list if c[0][0] == "transcription_update"]
    # Check if any provisional (final=False)
    has_provisional = any(c[0][1]['final'] is False for c in calls)
    assert has_provisional

    await streamer.stop()
