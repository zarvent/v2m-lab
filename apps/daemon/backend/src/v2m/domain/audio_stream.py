"""DEPRECATED: Protocolos de audio stream no usados en producción.

Estos tipos fueron diseñados para RustAudioStream que fue reemplazado
por la arquitectura Producer-Consumer en streaming_transcriber.py.

Se mantiene para compatibilidad con tests existentes.
Programado para eliminación en v2.0.
"""

import warnings
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

import numpy as np

warnings.warn(
    "v2m.domain.audio_stream está deprecado y será eliminado en v2.0.",
    DeprecationWarning,
    stacklevel=2,
)


@dataclass(slots=True, frozen=True)
class VADChunk:
    """DEPRECATED: Chunk de audio con timestamp para VAD."""

    timestamp: float
    audio: np.ndarray  # float32 array


class AudioStreamPort(Protocol):
    """DEPRECATED: Protocolo de stream de audio async."""

    def __aiter__(self) -> AsyncIterator[VADChunk]: ...
