from unittest.mock import MagicMock, patch

import pytest

from v2m.infrastructure.persistent_model import PersistentWhisperWorker


@pytest.fixture
def mock_whisper_model():
    with patch("v2m.infrastructure.persistent_model.WhisperModel") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_class, mock_instance


@pytest.mark.asyncio
async def test_worker_initialization(mock_whisper_model):
    mock_class, _mock_instance = mock_whisper_model

    worker = PersistentWhisperWorker(model_size="tiny", keep_warm=True)
    await worker.initialize()

    mock_class.assert_called_once()
    assert worker._model is not None


@pytest.mark.asyncio
async def test_worker_lazy_load(mock_whisper_model):
    mock_class, _mock_instance = mock_whisper_model

    worker = PersistentWhisperWorker(model_size="tiny", keep_warm=False)
    # Shouldn't load on init
    await worker.initialize()
    mock_class.assert_not_called()

    # helper func
    def my_inference(model):
        return "result"

    # Should load on inference
    res = await worker.run_inference(my_inference)

    mock_class.assert_called_once()
    assert res == "result"


@pytest.mark.asyncio
async def test_worker_unload(mock_whisper_model):
    _mock_class, _mock_instance = mock_whisper_model

    worker = PersistentWhisperWorker(model_size="tiny", keep_warm=True)
    await worker.initialize()
    assert worker._model is not None

    await worker.unload()
    assert worker._model is None


def test_worker_sync_init(mock_whisper_model):
    mock_class, _mock_instance = mock_whisper_model

    worker = PersistentWhisperWorker(model_size="tiny", keep_warm=True)
    worker.initialize_sync()

    mock_class.assert_called_once()
    assert worker._model is not None
