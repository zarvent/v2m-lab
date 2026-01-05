# Este archivo es parte de voice2machine.
#
# voice2machine es software libre: puedes redistribuirlo y/o modificarlo
# bajo los términos de la Licencia Pública General GNU publicada por
# la Free Software Foundation, ya sea la versión 3 de la Licencia, o
# (a tu elección) cualquier versión posterior.
#
# voice2machine se distribuye con la esperanza de que sea útil,
# pero SIN NINGUNA GARANTÍA; ni siquiera la garantía implícita de
# COMERCIABILIDAD o IDONEIDAD PARA UN PROPÓSITO PARTICULAR. Consulta la
# Licencia Pública General GNU para más detalles.
#
# Deberías haber recibido una copia de la Licencia Pública General GNU
# junto con voice2machine. Si no, consulta <https://www.gnu.org/licenses/>.

"""
Módulo de Grabación de Audio.

Esta clase actúa como un fachada (Facade/Strangler Fig) para abstraer la complejidad
de la captura de audio en tiempo real. Implementa una estrategia de fallback robusta:
intenta usar el motor optimizado en Rust y retrocede a Python (sounddevice) si es necesario.

Características (SOTA 2026):
    - Motor Rust (cpal + ringbuf) para captura Lock-Free y GIL-Free.
    - Buffer pre-allocado en Python para evitar realocaciones O(n).
    - Gestión automática de hilos y limpieza de recursos.
    - Manejo resiliente de `PortAudio` faltante.
"""

import threading
import wave
from pathlib import Path

import numpy as np

from v2m.core.logging import logger
from v2m.domain.errors import RecordingError

# --- IMPORTACIÓN CONDICIONAL DE MOTORES DE AUDIO ---

# 1. Motor Rust (Prioridad Alta)
try:
    from v2m_engine import AudioRecorder as RustAudioRecorder

    HAS_RUST_ENGINE = True
    logger.info("🚀 Motor de audio Rust (v2m_engine) cargado correctamente")
except ImportError:
    HAS_RUST_ENGINE = False
    # No logueamos advertencia aquí para no spammear en tests si no es necesario

# 2. Motor Python (Fallback)
try:
    import sounddevice as sd

    HAS_SOUNDDEVICE = True
except (ImportError, OSError) as e:
    # Capturamos OSError porque sounddevice lanza esto si libportaudio no existe
    HAS_SOUNDDEVICE = False
    sd = None  # type: ignore
    logger.warning(
        f"⚠️ SoundDevice no disponible (PortAudio faltante?): {e}. "
        "La grabación fallará si no se usa el motor Rust."
    )


class AudioRecorder:
    """
    Grabador de audio de alto rendimiento con estrategia dual (Rust/Python).

    Motores:
    1. **Rust (Preferido)**: Bajo nivel, sin GIL, sin locks en el hot-path de audio.
    2. **Python (Fallback)**: Basado en PortAudio, robusto y ampliamente compatible.
    """

    # Tamaño del chunk de audio (coincide con defecto de sounddevice/ALSA)
    CHUNK_SIZE = 1024

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        max_duration_sec: int = 600,
        device_index: int | None = None,
    ):
        """
        Inicializa el grabador de audio.

        Args:
            sample_rate: Frecuencia de muestreo (Hz). Whisper requiere 16000.
            channels: Número de canales (mono=1, estéreo=2).
            max_duration_sec: Límite de seguridad para el buffer (evita OOM).
            device_index: Índice del dispositivo de audio (solo modo Python).
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.device_index = device_index
        self._recording = False

        # Estado del motor Rust
        self._rust_recorder: RustAudioRecorder | None = None

        # Estado del motor Python
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()
        self._buffer: np.ndarray | None = None
        self._write_pos = 0
        self.max_samples = max_duration_sec * sample_rate

        # Intento de inicialización del motor Rust
        if HAS_RUST_ENGINE and device_index is None:
            try:
                self._rust_recorder = RustAudioRecorder(sample_rate, channels)
                logger.debug("Usando motor de grabación Rust")
                return
            except Exception as e:
                logger.error(f"Error inicializando motor Rust: {e} - Cayendo a Python")

        # Inicialización del buffer para modo Python (Pre-allocation)
        # Solo si sounddevice está disponible, para evitar crash en entornos sin audio
        if HAS_SOUNDDEVICE:
            self._buffer = self._allocate_buffer()

    def _allocate_buffer(self) -> np.ndarray:
        """Reserva memoria contigua para el buffer de audio."""
        if self.channels > 1:
            return np.zeros((self.max_samples, self.channels), dtype=np.float32)
        return np.zeros(self.max_samples, dtype=np.float32)

    def _empty_audio_array(self) -> np.ndarray:
        """Retorna un array vacío con la forma correcta."""
        if self.channels > 1:
            return np.array([], dtype=np.float32).reshape(0, self.channels)
        return np.array([], dtype=np.float32)

    def _save_wav(self, audio_data: np.ndarray, save_path: Path):
        """Exporta los datos de audio a formato WAV estándar."""
        # Conversión float32 (-1.0 a 1.0) -> int16
        audio_int16 = (audio_data * 32767).astype(np.int16)
        with wave.open(str(save_path), "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())

    def _get_audio_slice(self, num_samples: int) -> np.ndarray:
        """Obtiene la porción válida del buffer grabado."""
        if self._buffer is None:
            return self._empty_audio_array()
        if self.channels > 1:
            return self._buffer[:num_samples, :]
        return self._buffer[:num_samples]

    def start(self):
        """
        Inicia la captura de audio.

        Raises:
            RecordingError: Si la grabación ya está activa o el dispositivo falla.
        """
        if self._recording:
            raise RecordingError("Grabación ya en progreso")

        self._recording = True

        # --- MOTOR RUST ---
        if self._rust_recorder:
            try:
                self._rust_recorder.start()
                logger.info("Grabación iniciada (Motor Rust)")
                return
            except Exception as e:
                logger.error(f"Fallo en motor Rust, activando fallback Python: {e}")
                self._rust_recorder = None  # Deshabilitar permanentemente

        # --- MOTOR PYTHON ---
        if not HAS_SOUNDDEVICE:
            self._recording = False
            raise RecordingError(
                "No se puede iniciar grabación: Motor Rust falló y PortAudio no está disponible."
            )

        if self._buffer is None:
            self._buffer = self._allocate_buffer()

        self._write_pos = 0  # Resetear puntero de escritura

        def callback(indata: np.ndarray, frames: int, time, status):
            """Callback de audio en tiempo real (invocado por hilo C de PortAudio)."""
            if status:
                logger.warning(f"Estado de audio: {status}")

            with self._lock:
                if not self._recording or self._buffer is None:
                    return

                # Calcular espacio disponible para evitar Buffer Overflow
                samples_to_write = min(frames, self.max_samples - self._write_pos)

                if samples_to_write > 0:
                    end_pos = self._write_pos + samples_to_write
                    # Copia eficiente (slice assignment)
                    if self.channels > 1:
                        self._buffer[self._write_pos : end_pos, :] = indata[
                            :samples_to_write, :
                        ]
                    else:
                        self._buffer[self._write_pos : end_pos] = indata[
                            :samples_to_write, 0
                        ]
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
            logger.info("Grabación iniciada (Motor Python)")
        except Exception as e:
            self._recording = False
            if self._stream:
                self._stream.close()
                self._stream = None
            raise RecordingError(f"Fallo al iniciar grabación: {e}") from e

    def stop(
        self,
        save_path: Path | None = None,
        return_data: bool = True,
        copy_data: bool = True,
    ) -> np.ndarray:
        """
        Detiene la grabación y retorna los datos capturados.

        Args:
            save_path: Si se proporciona, guarda el audio en disco (WAV).
            return_data: Si es False, retorna un array vacío (ahorra memoria si solo se guarda).
            copy_data: Si es True, retorna una copia segura de los datos.

        Returns:
            np.ndarray: Audio en formato float32.
        """
        if not self._recording:
            raise RecordingError("No hay grabación en curso")

        self._recording = False

        # --- MOTOR RUST ---
        if self._rust_recorder:
            try:
                audio_view = self._rust_recorder.stop()
                recorded_samples = len(audio_view)
                logger.info(
                    f"Grabación detenida (Rust): {recorded_samples} muestras capturadas"
                )

                if save_path:
                    self._save_wav(audio_view, save_path)

                if not return_data:
                    return self._empty_audio_array()

                if copy_data:
                    return audio_view.copy()

                return audio_view
            except Exception as e:
                logger.error(f"Error deteniendo motor Rust: {e}")
                raise RecordingError(f"Fallo crítico en motor de audio: {e}") from e

        # --- MOTOR PYTHON ---
        if not HAS_SOUNDDEVICE:
            # Caso raro: se inició (supuestamente) pero ahora no está disponible?
            return self._empty_audio_array()

        with self._lock:
            recorded_samples = self._write_pos

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        logger.info(
            f"Grabación detenida (Python): {recorded_samples} muestras capturadas"
        )

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
