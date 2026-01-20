from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(slots=True, frozen=True)
class VADChunk:
    timestamp: float
    audio: np.ndarray  # float32 array


class AudioStreamPort(Protocol):
    def __aiter__(self) -> AsyncIterator[VADChunk]: ...
