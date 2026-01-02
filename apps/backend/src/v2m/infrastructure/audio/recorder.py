# This file is part of voice2machine.
#
# voice2machine is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# voice2machine is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with voice2machine.  If not, see <https://www.gnu.org/licenses/>.

import threading
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

from v2m.core.logging import logger
from v2m.domain.errors import RecordingError

# Intenta importar el motor de audio Rust
try:
    from v2m_engine import AudioRecorder as RustAudioRecorder

    HAS_RUST_ENGINE = True
    logger.info("🚀 motor de audio rust v2m_engine cargado correctamente")
except ImportError:
    HAS_RUST_ENGINE = False
    logger.warning("⚠️ motor de audio rust no disponible usando fallback python")


class AudioRecorder:
    """
    CLASE RESPONSABLE DE LA GRABACIÓN DE AUDIO

    esta clase actúa como fachada ("Strangler Fig Pattern") para modernizar el stack de audio.
    elige automáticamente entre dos motores:

    1. **MOTOR RUST (V2M_ENGINE)** - [PREDETERMINADO]
       - **State of the Art (2026)**: Utiliza `cpal` + `ringbuf` (SPSC).
       - **Lock-Free**: El hilo de audio es 'Wait-Free', garantizando cero bloqueos (glitch-free).
       - **GIL-Free**: La captura ocurre fuera del Global Interpreter Lock de Python.
       - **Zero-Copy**: Intercambio de datos eficiente con NumPy.

    2. **MOTOR PYTHON (SOUNDDEVICE)** - [FALLBACK]
       - Se activa automáticamente si falla Rust (ej. hardware no soportado o error de driver).
       - Utiliza `sounddevice` (PortAudio wrapper) con buffers pre-allocados.

    OPTIMIZACIONES
    - buffer pre-allocado en modo fallback para evitar reallocaciones O(n) -> O(1).
    - arquitectura resiliente: si Rust falla, el usuario no nota interrupción.
    """

    # tamaño del chunk en samples coincide con sounddevice default ~1024
    CHUNK_SIZE = 1024

    def __init__(
        self, sample_rate: int = 16000, channels: int = 1, max_duration_sec: int = 600, device_index: int | None = None
    ):
        """
        INICIALIZA EL GRABADOR DE AUDIO

        ARGS:
            sample_rate: frecuencia de muestreo en hz
            channels: número de canales de audio
            max_duration_sec: duración máxima de grabación en segundos default 10 min
            device_index: índice del dispositivo de audio a usar (solo soportado en modo Python)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.device_index = device_index
        self._recording = False

        # Estado para el motor Rust
        self._rust_recorder: RustAudioRecorder | None = None

        # Estado para el motor Python (fallback)
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()
        self._buffer: np.ndarray | None = None
        self._write_pos = 0
        self.max_samples = max_duration_sec * sample_rate

        if HAS_RUST_ENGINE and device_index is None:
            try:
                self._rust_recorder = RustAudioRecorder(sample_rate, channels)
                logger.debug("usando motor de grabación rust")
                return
            except Exception as e:
                logger.error(f"error inicializando motor rust: {e} - cayendo a python")

        # Inicialización del fallback Python (buffer pre-allocado)
        self._buffer = self._allocate_buffer()

    def _allocate_buffer(self) -> np.ndarray:
        """Allocate pre-allocated buffer based on channel configuration."""
        if self.channels > 1:
            return np.zeros((self.max_samples, self.channels), dtype=np.float32)
        return np.zeros(self.max_samples, dtype=np.float32)

    def _empty_audio_array(self) -> np.ndarray:
        """Return empty audio array with correct shape for channel configuration."""
        if self.channels > 1:
            return np.array([], dtype=np.float32).reshape(0, self.channels)
        return np.array([], dtype=np.float32)

    def _save_wav(self, audio_data: np.ndarray, save_path: Path):
        """Save audio data to WAV file."""
        audio_int16 = (audio_data * 32767).astype(np.int16)
        with wave.open(str(save_path), "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())

    def _get_audio_slice(self, num_samples: int) -> np.ndarray:
        """Extract audio slice from buffer based on channel configuration."""
        if self.channels > 1:
            return self._buffer[:num_samples, :]
        return self._buffer[:num_samples]

    def start(self):
        """
        INICIA LA GRABACIÓN DE AUDIO

        RAISES:
            RecordingError: si la grabación ya está en progreso o falla al iniciar el stream
        """
        if self._recording:
            raise RecordingError("grabación ya en progreso")

        self._recording = True

        # --- CAMINO DE EJECUCIÓN RUST ---
        if self._rust_recorder:
            try:
                self._rust_recorder.start()
                logger.info("grabación iniciada (rust engine)")
                return
            except Exception as e:
                logger.error(f"fallo en motor rust, intentando fallback a python: {e}")
                # No lanzamos error aquí, permitimos que continúe al fallback Python
                # pero primero debemos resetear el estado de grabación si rust lo dejó sucio
                self._rust_recorder = None  # Deshabilitamos rust para esta instancia

        # --- CAMINO DE EJECUCIÓN PYTHON (FALLBACK) ---
        # Aseguramos que _buffer está inicializado si falló rust
        if self._buffer is None:
            self._buffer = self._allocate_buffer()

        self._write_pos = 0  # reiniciar posición del buffer

        def callback(indata: np.ndarray, frames: int, time, status):
            if status:
                logger.warning(f"estado de la grabación de audio {status}")

            with self._lock:
                if not self._recording:
                    return

                # calcular cuántos samples podemos escribir
                samples_to_write = min(frames, self.max_samples - self._write_pos)

                if samples_to_write > 0:
                    # escritura zero-copy al buffer pre-allocado flatten inline
                    end_pos = self._write_pos + samples_to_write

                    if self.channels > 1:
                        self._buffer[self._write_pos : end_pos, :] = indata[:samples_to_write, :]
                    else:
                        self._buffer[self._write_pos : end_pos] = indata[:samples_to_write, 0]

                    self._write_pos = end_pos

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=callback,
                dtype="float32",
                device=self.device_index,
                blocksize=self.CHUNK_SIZE,
            )
            self._stream.start()
            logger.info("grabación de audio iniciada (python fallback)")
        except Exception as e:
            self._recording = False
            if self._stream:
                self._stream.close()
                self._stream = None
            raise RecordingError(f"falló al iniciar la grabación {e}") from e

    def stop(self, save_path: Path | None = None, return_data: bool = True, copy_data: bool = True) -> np.ndarray:
        """
        DETIENE LA GRABACIÓN Y DEVUELVE EL AUDIO CAPTURADO

        ARGS:
            save_path: ruta opcional para guardar el audio como archivo wav
            return_data: si es True retorna el audio grabado
            copy_data: si es True retorna una copia del buffer (seguro)

        RETURNS:
            el audio grabado como un array de numpy float32
        """
        if not self._recording:
            raise RecordingError("no hay grabación en curso")

        self._recording = False

        # --- CAMINO DE EJECUCIÓN RUST ---
        if self._rust_recorder:
            try:
                # El método stop de Rust devuelve directamente el numpy array
                audio_view = self._rust_recorder.stop()
                recorded_samples = len(audio_view)
                logger.info(f"grabación detenida (rust engine): {recorded_samples} samples")

                # Manejo de guardado a disco
                if save_path:
                    self._save_wav(audio_view, save_path)

                if not return_data:
                    return self._empty_audio_array()

                # Rust devuelve un nuevo array (ya es una copia/nueva ref),
                # pero si el usuario pidió copy_data=True explícitamente y queremos ser paranoicos
                if copy_data:
                    return audio_view.copy()

                return audio_view
            except Exception as e:
                logger.error(f"error deteniendo grabación rust: {e}")
                raise RecordingError(f"error deteniendo rust: {e}") from e

        # --- CAMINO DE EJECUCIÓN PYTHON ---
        with self._lock:
            recorded_samples = self._write_pos

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        logger.info(f"grabación detenida (python): {recorded_samples} samples")

        if recorded_samples == 0:
            return self._empty_audio_array()

        audio_view = self._get_audio_slice(recorded_samples)

        if save_path:
            self._save_wav(audio_view, save_path)

        if not return_data:
            return self._empty_audio_array()

        if copy_data:
            return audio_view.copy()

        return audio_view
