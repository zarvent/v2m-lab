import threading
import wave
from pathlib import Path

import numpy as np

try:
    import sounddevice as sd
except OSError:
    sd = None

from v2m.shared.logging import logger
from v2m.shared.errors import RecordingError

# Intenta importar el motor de audio Rust
try:
    from v2m_engine import AudioRecorder as RustAudioRecorder

    HAS_RUST_ENGINE = True
    logger.info("🚀 motor de audio rust v2m_engine cargado correctamente")
except ImportError:
    HAS_RUST_ENGINE = False
    logger.warning("⚠️ motor de audio rust no disponible usando fallback python")


class AudioRecorder:
    """Clase responsable de la grabación de audio.

    Implementa el patrón de fachada ("Strangler Fig") para modernizar el stack de audio,
    seleccionando automáticamente entre dos motores para garantizar estabilidad y rendimiento.

    Motores soportados:
    1. **Motor Rust (v2m_engine)** - [Predeterminado]
       - **State of the Art (2026)**: Utiliza `cpal` + `ringbuf` (SPSC).
       - **Lock-Free**: El hilo de audio es 'Wait-Free', garantizando cero bloqueos (glitch-free).
       - **GIL-Free**: La captura ocurre fuera del Global Interpreter Lock de Python.
       - **Zero-Copy**: Intercambio de datos eficiente con NumPy.

    2. **Motor Python (sounddevice)** - [Fallback]
       - Se activa automáticamente si falla Rust (ej. hardware no soportado o error de driver).
       - Utiliza `sounddevice` (PortAudio wrapper) con buffers pre-allocados.

    Optimizaciones:
    - Buffer pre-allocado en modo fallback para evitar reallocaciones O(n) -> O(1).
    - Arquitectura resiliente: si Rust falla, el usuario no nota interrupción.
    """

    # Tamaño del chunk en samples (coincide con sounddevice default ~1024)
    CHUNK_SIZE = 1024

    def __init__(
        self, sample_rate: int = 16000, channels: int = 1, max_duration_sec: int = 600, device_index: int | None = None
    ):
        """Inicializa el grabador de audio.

        Args:
            sample_rate: Frecuencia de muestreo en Hz.
            channels: Número de canales de audio.
            max_duration_sec: Duración máxima de grabación en segundos. Defecto: 10 min.
            device_index: Índice del dispositivo de audio a usar (solo soportado en modo Python).
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

        if sd is None:
            logger.warning("sounddevice no está disponible (PortAudio no encontrado)")

        # Inicialización del fallback Python (buffer pre-allocado)
        self._buffer = self._allocate_buffer()

    def _allocate_buffer(self) -> np.ndarray:
        """Asigna un buffer pre-allocado basado en la configuración de canales."""
        if self.channels > 1:
            return np.zeros((self.max_samples, self.channels), dtype=np.float32)
        return np.zeros(self.max_samples, dtype=np.float32)

    def _empty_audio_array(self) -> np.ndarray:
        """Retorna un array de audio vacío con la forma correcta."""
        if self.channels > 1:
            return np.array([], dtype=np.float32).reshape(0, self.channels)
        return np.array([], dtype=np.float32)

    def _save_wav(self, audio_data: np.ndarray, save_path: Path):
        """Guarda los datos de audio en un archivo WAV."""
        audio_int16 = (audio_data * 32767).astype(np.int16)
        with wave.open(str(save_path), "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())

    def _get_audio_slice(self, num_samples: int) -> np.ndarray:
        """Extrae un segmento de audio del buffer."""
        if self.channels > 1:
            return self._buffer[:num_samples, :]
        return self._buffer[:num_samples]

    def start(self):
        """Inicia la grabación de audio.

        Raises:
            RecordingError: Si la grabación ya está en progreso o falla al iniciar el stream.
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
            if sd is None:
                raise OSError("PortAudio library not found")
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
        """Detiene la grabación y devuelve el audio capturado.

        Args:
            save_path: Ruta opcional para guardar el audio como archivo WAV.
            return_data: Si es True retorna el audio grabado.
            copy_data: Si es True retorna una copia del buffer (seguro).

        Returns:
            np.ndarray: El audio grabado como un array de numpy float32.
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

    # =========================================================================
    # STREAMING METHODS (delegate to Rust engine)
    # =========================================================================

    async def wait_for_data(self) -> None:
        """Wait asynchronously for new audio data to be available.

        This method delegates to the Rust engine's wait_for_data() which uses
        tokio::Notify for efficient async waiting without polling.

        Raises:
            RuntimeError: If using Python fallback (streaming not supported) or not recording.
        """
        if not self._rust_recorder:
            raise RuntimeError("wait_for_data requires Rust engine (Python fallback does not support streaming)")
        if not self._recording:
            raise RuntimeError("not recording")

        # Rust wait_for_data returns an awaitable
        await self._rust_recorder.wait_for_data()

    def read_chunk(self) -> "np.ndarray":
        """Read available audio data from the ring buffer.

        Returns all samples currently in the buffer without blocking.
        Used for streaming transcription where we process audio incrementally.

        Returns:
            np.ndarray: Audio samples as float32 numpy array.

        Raises:
            RuntimeError: If using Python fallback (streaming not supported) or not recording.
        """
        if not self._rust_recorder:
            raise RuntimeError("read_chunk requires Rust engine (Python fallback does not support streaming)")
        if not self._recording:
            return np.array([], dtype=np.float32)

        return self._rust_recorder.read_chunk()
