"""SOTA 2026 Streaming Transcriber con arquitectura Producer-Consumer.

Este módulo implementa un sistema de transcripción streaming basado en segmentos que:
1. Desacopla la ingesta de audio (Producer) del procesamiento VAD/Whisper (Consumer)
2. Usa asyncio.Queue para amortiguar la latencia de inferencia sin perder audio
3. Usa VAD Silero para detectar límites de habla/silencio
4. Hace commit de segmentos en 800ms de silencio (seguro para prosodia española)
5. Inyecta ventana de contexto de 200 caracteres para continuidad
"""

import asyncio
import logging
import time
from collections import deque

import numpy as np

# Importar torch a nivel de módulo para evitar overhead en hot-path
try:
    import torch

    _TORCH_AVAILABLE = True
except ImportError:
    torch = None
    _TORCH_AVAILABLE = False

try:
    from silero_vad import load_silero_vad

    _SILERO_AVAILABLE = True
except ImportError:
    load_silero_vad = None
    _SILERO_AVAILABLE = False

from v2m.shared.config import config
from v2m.shared.interfaces import SessionManagerInterface as SessionManager
from v2m.features.audio.recorder import AudioRecorder
from v2m.features.transcription.persistent_model import PersistentWhisperWorker

logger = logging.getLogger(__name__)

# Constantes de configuración de streaming
CONTEXT_WINDOW_CHARS = 200  # Ventana deslizante para inyección de prompt
PROVISIONAL_INTERVAL = 0.5  # Intervalo entre inferencias provisionales (segundos)
PRE_ROLL_CHUNKS = 3  # Mantener últimos 3 chunks (~300ms) para no cortar palabras
MIN_SEGMENT_DURATION = 0.5  # Segundos de habla requeridos para commit
DEFAULT_SILENCE_COMMIT_MS = 1000  # Duración de silencio por defecto para trigger commit
CONTEXT_RESET_MS = 3000  # Resetear contexto si silencio excede esto (previene alucinaciones)
HEARTBEAT_INTERVAL = 2.0  # Intervalo de heartbeat en segundos


class StreamingTranscriber:
    """Transcriptor de streaming con arquitectura Producer-Consumer.

    El Producer (ingesta de audio) corre en una tarea separada del Consumer
    (VAD + Whisper), permitiendo que el audio se acumule en una cola si
    la inferencia tarda más de lo esperado. Esto elimina buffer overruns.
    """

    def __init__(
        self,
        worker: PersistentWhisperWorker,
        session_manager: SessionManager,
        recorder: AudioRecorder,
    ):
        self.worker = worker
        self.session_manager = session_manager
        self.recorder = recorder

        # Control de ciclo de vida
        self._stop_event = asyncio.Event()
        self._producer_task: asyncio.Task | None = None
        self._consumer_task: asyncio.Task | None = None

        # Cola de audio (Producer → Consumer)
        # maxsize=0 significa infinita - el Consumer se pondrá al día
        self._audio_queue: asyncio.Queue[np.ndarray] = asyncio.Queue()

        # Buffer de pre-roll (captura inicio de habla)
        self._pre_roll_buffer: deque[np.ndarray] = deque(maxlen=PRE_ROLL_CHUNKS)

        # Contexto deslizante para continuidad
        self._context_window: str = ""

        # Parámetros de VAD desde config
        vad_config = config.transcription.whisper.vad_parameters
        self._silence_commit_ms = getattr(vad_config, "min_silence_duration_ms", DEFAULT_SILENCE_COMMIT_MS)
        self._speech_threshold = vad_config.threshold

        # Rate limiting para errores de VAD
        self._last_vad_error_time = 0.0

        # Cargar modelo Silero VAD (SOTA 2026)
        self._vad_model = None
        if _SILERO_AVAILABLE:
            try:
                self._vad_model = load_silero_vad(onnx=True)
                logger.info("✅ Silero VAD (ONNX) cargado para segmentación de alta precisión")
            except Exception as e:
                logger.warning(f"⚠️ Error cargando Silero VAD: {e}. Usando fallback de energía.")
        else:
            logger.warning("⚠️ silero-vad no disponible. Usando fallback de energía.")

    async def start(self) -> None:
        """Inicia el loop de transcripción streaming (Producer-Consumer)."""
        if self._producer_task and not self._producer_task.done():
            logger.warning("Streaming ya activo")
            return

        if not self.recorder:
            logger.error("No se proporcionó recorder a StreamingTranscriber")
            raise RuntimeError("No recorder")

        self.recorder.start()
        self._stop_event.clear()
        self._context_window = ""

        # Limpiar cola por si hay datos residuales
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        # Lanzar tareas Producer y Consumer en paralelo
        self._producer_task = asyncio.create_task(self._audio_producer_loop(), name="audio-producer")
        self._consumer_task = asyncio.create_task(self._audio_consumer_loop(), name="audio-consumer")

        logger.info("🚀 Streaming iniciado (Arquitectura Producer-Consumer)")

    async def stop(self) -> str:
        """Detiene streaming y retorna transcripción final."""
        if not self._consumer_task:
            return ""

        logger.info("Deteniendo streaming...")
        self._stop_event.set()

        # Detener grabación primero para que Producer termine
        self.recorder.stop()

        result = ""
        try:
            # Esperar a que Producer termine de encolar
            if self._producer_task:
                await asyncio.wait_for(self._producer_task, timeout=2.0)
        except TimeoutError:
            logger.warning("Timeout esperando Producer, cancelando...")
            if self._producer_task:
                self._producer_task.cancel()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error deteniendo Producer: {e}")

        try:
            # Esperar a que Consumer procese cola restante y retorne resultado
            if self._consumer_task:
                result = await asyncio.wait_for(self._consumer_task, timeout=10.0)
        except TimeoutError:
            logger.warning("Timeout esperando Consumer, cancelando...")
            if self._consumer_task:
                self._consumer_task.cancel()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error deteniendo Consumer: {e}")

        self._producer_task = None
        self._consumer_task = None

        return result if result else ""

    # =========================================================================
    # PRODUCER: Solo lee audio de Rust y lo encola (nunca se bloquea)
    # =========================================================================

    async def _audio_producer_loop(self) -> None:
        """Tarea Producer (Alta Prioridad).

        Su única misión es sacar datos de Rust y meterlos en la cola.
        Operación O(1) - instantánea. Nunca se bloquea en inferencia.
        """
        try:
            while not self._stop_event.is_set():
                try:
                    # Rust maneja el bloqueo eficiente (Wait-Free via tokio::Notify)
                    await self.recorder.wait_for_data()
                    chunk = self.recorder.read_chunk()

                    if len(chunk) > 0:
                        # Encolar sin bloquear (O(1))
                        self._audio_queue.put_nowait(chunk)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Producer error: {e}")
                    await asyncio.sleep(0.05)  # Back-off breve en error

        except asyncio.CancelledError:
            pass
        finally:
            logger.debug("Producer terminado")

    # =========================================================================
    # CONSUMER: Procesa VAD y Whisper a su propio ritmo
    # =========================================================================

    async def _audio_consumer_loop(self) -> str:
        """Tarea Consumer (Prioridad IA).

        Procesa VAD y Whisper a su propio ritmo. Si se atrasa,
        la cola crece pero el audio NO se pierde.
        """
        all_final_text: list[str] = []
        current_segment: list[np.ndarray] = []
        segment_duration = 0.0
        last_provisional_time = time.time()
        provisional_text = ""
        silence_start: float | None = None
        last_heartbeat_time = time.time()

        try:
            while not self._stop_event.is_set() or not self._audio_queue.empty():
                # Obtener chunk con timeout para revisar stop_event
                try:
                    chunk = await asyncio.wait_for(self._audio_queue.get(), timeout=0.1)
                except TimeoutError:
                    # Revisar heartbeat aunque no haya audio
                    now = time.time()
                    if now - last_heartbeat_time > HEARTBEAT_INTERVAL:
                        await self.session_manager.emit_event("heartbeat", {"timestamp": now, "state": "recording"})
                        last_heartbeat_time = now
                    continue

                if len(chunk) == 0:
                    continue

                now = time.time()

                # Heartbeat
                if now - last_heartbeat_time > HEARTBEAT_INTERVAL:
                    await self.session_manager.emit_event("heartbeat", {"timestamp": now, "state": "recording"})
                    last_heartbeat_time = now

                # Mantener pre-roll buffer
                self._pre_roll_buffer.append(chunk)

                # Detección VAD
                is_speech = self._detect_speech(chunk)

                # Reset de contexto si silencio muy largo (anti-alucinación)
                if silence_start:
                    silence_ms = (now - silence_start) * 1000
                    if silence_ms > CONTEXT_RESET_MS and self._context_window:
                        self._context_window = ""

                # Lógica de acumulación de segmentos
                if is_speech and not current_segment:
                    # Inicio de habla - incluir pre-roll buffer
                    current_segment.extend(self._pre_roll_buffer)
                    segment_duration = sum(len(c) / 16000 for c in current_segment)
                    silence_start = None

                elif is_speech:
                    # Continuando habla
                    current_segment.append(chunk)
                    segment_duration += len(chunk) / 16000
                    silence_start = None

                elif current_segment:
                    # Silencio con segmento activo - seguir acumulando
                    current_segment.append(chunk)
                    segment_duration += len(chunk) / 16000

                    if silence_start is None:
                        silence_start = now

                # Inferencia provisional durante habla
                if (
                    is_speech
                    and segment_duration > MIN_SEGMENT_DURATION
                    and now - last_provisional_time > PROVISIONAL_INTERVAL
                ):
                    last_provisional_time = now
                    text = await self._infer_provisional(current_segment)
                    if text and text != provisional_text:
                        provisional_text = text
                        await self.session_manager.emit_event(
                            "transcription_update",
                            {"text": text, "final": False},
                        )

                # COMMIT si silencio > threshold Y tenemos suficiente audio
                if silence_start and current_segment and segment_duration > MIN_SEGMENT_DURATION:
                    silence_ms = (now - silence_start) * 1000
                    if silence_ms > self._silence_commit_ms:
                        logger.debug(f"Commit segmento: {segment_duration:.2f}s (silencio: {silence_ms:.0f}ms)")

                        final_text = await self._infer_final(current_segment)
                        if final_text:
                            all_final_text.append(final_text)
                            self._update_context_window(final_text)
                            await self.session_manager.emit_event(
                                "transcription_update",
                                {"text": final_text, "final": True},
                            )

                        # FLUSH - limpiar buffers
                        current_segment.clear()
                        segment_duration = 0.0
                        provisional_text = ""
                        silence_start = None

            # Commit final al detener (si queda audio)
            if current_segment and segment_duration > MIN_SEGMENT_DURATION:
                logger.debug(f"Commit final al detener: {segment_duration:.2f}s")
                final_text = await self._infer_final(current_segment)
                if final_text:
                    all_final_text.append(final_text)
                    self._update_context_window(final_text)
                    await self.session_manager.emit_event(
                        "transcription_update",
                        {"text": final_text, "final": True},
                    )

            return " ".join(all_final_text)

        except asyncio.CancelledError:
            # Intentar commit de emergencia
            if current_segment and segment_duration > MIN_SEGMENT_DURATION:
                try:
                    final_text = await self._infer_final(current_segment)
                    if final_text:
                        all_final_text.append(final_text)
                except Exception:
                    pass
            return " ".join(all_final_text) if all_final_text else ""

        except Exception as e:
            logger.error(f"Consumer loop error: {e}")
            return " ".join(all_final_text) if all_final_text else ""

    # =========================================================================
    # VAD (Voice Activity Detection)
    # =========================================================================

    def _detect_speech(self, chunk: np.ndarray) -> bool:
        """Detecta habla usando Silero VAD con fallback a energía.

        Silero VAD es SOTA 2026 - ignora respiraciones, tecleo, etc.
        El fallback de energía es menos preciso pero funciona sin torch.
        """
        if self._vad_model is not None and _TORCH_AVAILABLE:
            return self._detect_speech_silero(chunk)
        return self._detect_speech_energy(chunk)

    def _detect_speech_silero(self, chunk: np.ndarray) -> bool:
        """Detección de habla con Silero VAD (ONNX)."""
        try:
            # Normalizar input
            if chunk.ndim > 1:
                chunk = chunk.flatten()

            # Mínimo 512 muestras para detección confiable
            if len(chunk) < 512:
                return self._detect_speech_energy(chunk)

            # Asegurar float32 para ONNX
            if chunk.dtype != np.float32:
                chunk = chunk.astype(np.float32)

            # Silero requiere tensor torch incluso en modo ONNX
            chunk_tensor = torch.from_numpy(chunk)

            speech_prob = self._vad_model(chunk_tensor, 16000)

            # Manejar retorno tensor o escalar
            val = speech_prob.item() if hasattr(speech_prob, "item") else float(speech_prob)

            return val > self._speech_threshold

        except Exception as e:
            now = time.time()
            if now - self._last_vad_error_time > 5.0:
                logger.warning(f"Silero VAD error: {e} (throttled)")
                self._last_vad_error_time = now
            return self._detect_speech_energy(chunk)

    def _detect_speech_energy(self, chunk: np.ndarray, threshold: float = 0.015) -> bool:
        """Fallback: detección basada en energía RMS."""
        if len(chunk) == 0:
            return False
        energy = np.sqrt(np.mean(chunk**2))
        return energy > threshold

    # =========================================================================
    # Inferencia Whisper
    # =========================================================================

    def _build_context_prompt(self) -> str:
        """Build context prompt from sliding window.

        Uses last 200 chars to avoid Whisper's 224-token limit
        which can cause looping hallucinations.
        """
        if not self._context_window:
            return ""
        return self._context_window[-CONTEXT_WINDOW_CHARS:]

    def _update_context_window(self, text: str) -> None:
        """Append to context window, keeping last 200 chars."""
        clean_text = text.strip()
        if clean_text:
            self._context_window = (self._context_window + " " + clean_text)[-CONTEXT_WINDOW_CHARS:]

    async def _infer_provisional(self, audio_chunks: list[np.ndarray]) -> str:
        """Fast provisional inference for real-time feedback.

        Uses greedy decoding (beam_size=1) for speed.
        """
        if not audio_chunks:
            return ""

        full_audio = np.concatenate(audio_chunks)
        whisper_config = config.transcription.whisper
        context_prompt = self._build_context_prompt()

        def _inference_func(model):
            segments, _ = model.transcribe(
                full_audio,
                language=whisper_config.language if whisper_config.language != "auto" else None,
                task="transcribe",
                beam_size=1,  # Greedy for speed
                best_of=1,
                temperature=0.0,
                initial_prompt=context_prompt if context_prompt else None,
                condition_on_previous_text=False,  # Avoid conflict with manual prompt
                vad_filter=True,
            )
            return list(segments)

        try:
            segments = await self.worker.run_inference(_inference_func)
            text = " ".join(s.text.strip() for s in segments if s.text)
            return text
        except Exception as e:
            logger.debug(f"Provisional inference error: {e}")
            return ""

    async def _infer_final(self, audio_chunks: list[np.ndarray]) -> str:
        """High-quality final inference for committed segments.

        Uses configured beam search and VAD parameters.
        """
        if not audio_chunks:
            return ""

        full_audio = np.concatenate(audio_chunks)
        whisper_config = config.transcription.whisper
        context_prompt = self._build_context_prompt()

        def _inference_func(model):
            vad_params = None
            if whisper_config.vad_filter:
                vad_params = whisper_config.vad_parameters.model_dump()

            segments, _info = model.transcribe(
                full_audio,
                language=whisper_config.language if whisper_config.language != "auto" else None,
                task="transcribe",
                beam_size=whisper_config.beam_size,
                best_of=whisper_config.best_of,
                temperature=whisper_config.temperature,
                initial_prompt=context_prompt if context_prompt else None,
                condition_on_previous_text=False,  # Avoid conflict with manual prompt
                vad_filter=whisper_config.vad_filter,
                vad_parameters=vad_params,
            )
            return list(segments)

        try:
            segments = await self.worker.run_inference(_inference_func)
            text = " ".join(s.text.strip() for s in segments if s.text)
            if not text:
                logger.debug("Final inference empty (VAD filtered or silence)")
            return text
        except Exception as e:
            logger.error(f"Final inference error: {e}")
            return ""
