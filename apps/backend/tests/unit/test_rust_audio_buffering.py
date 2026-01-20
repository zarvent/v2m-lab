import pytest
from unittest.mock import MagicMock, AsyncMock
import numpy as np
import sys
import asyncio

# Mock v2m_engine before importing RustAudioStream
module_mock = MagicMock()
sys.modules["v2m_engine"] = module_mock

from v2m.infrastructure.rust_audio_adapter import RustAudioStream

@pytest.mark.asyncio
async def test_audio_stream_buffering():
    """Verify that RustAudioStream buffers small chunks into 512-sample chunks."""
    
    # Setup
    stream = RustAudioStream()
    recorder_mock = stream._recorder
    
    # Scenario: 
    # 1. 200 samples
    # 2. 200 samples (Total 400 - still no yield)
    # 3. 200 samples (Total 600 - yield 512, buffer 88)
    # 4. 500 samples (Total 588 - yield 512, buffer 76)
    
    chunk_200 = np.zeros(200, dtype=np.float32)
    chunk_500 = np.zeros(500, dtype=np.float32)
    
    # Configure mock
    # wait_for_data just returns immediately
    recorder_mock.wait_for_data = AsyncMock(return_value=None)
    
    # read_chunk returns our sequence
    # Note: The loop calls wait_for_data, then read_chunk.
    recorder_mock.read_chunk.side_effect = [
        chunk_200, 
        chunk_200, 
        chunk_200,
        chunk_500,
        Exception("StopTest") # Hack to break the infinite loop
    ]
    
    collected_chunks = []
    
    try:
        async for vad_chunk in stream:
            collected_chunks.append(vad_chunk)
            if len(collected_chunks) >= 2:
                break
    except Exception as e:
        if str(e) != "StopTest":
            raise e
            
    # Verification
    assert len(collected_chunks) == 2
    
    # Chunk 1: From first 3 inputs (600 samples) -> 512
    assert len(collected_chunks[0].audio) == 512
    
    # Chunk 2: Remainder 88 + 500 = 588 -> 512
    assert len(collected_chunks[1].audio) == 512
    
    # Verify we didn't lose data logic (implicit in sizes)
