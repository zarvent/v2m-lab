"""
SOTA 2026 Streaming Transcriber with Commit & Flush Architecture.

This module implements a segment-based streaming transcription system that:
1. Uses VAD to detect speech/silence boundaries
2. Commits segments on 800ms silence (Spanish prosody safe)
3. Clears audio buffer after each commit (Zero-Leak)
4. Injects 200-char context window for continuity
"""

import asyncio
import logging
import time
from typing import Optional

import numpy as np
from silero_vad import load_silero_vad

from v2m.config import config
from v2m.core.client_session import ClientSessionManager as SessionManager
from v2m.infrastructure.audio.recorder import AudioRecorder
from v2m.infrastructure.persistent_model import PersistentWhisperWorker

logger = logging.getLogger(__name__)

# Constants for optimizations
# Streaming behavior defaults (can be overridden via config)
CONTEXT_WINDOW_CHARS = 200  # Sliding window for prompt injection
PROVISIONAL_INTERVAL = 0.5  # Interval between provisional inferences
PRE_ROLL_CHUNKS = 3  # Keep last 3 chunks (~300ms) to avoid cutting words
MIN_SEGMENT_DURATION = 0.5  # Seconds of speech required to commit
DEFAULT_SILENCE_COMMIT_MS = 1000  # Default silence duration to trigger commit
CONTEXT_RESET_MS = 3000  # Reset context if silence exceeds this (prevents hallucinations)


class StreamingTranscriber:
    def __init__(
        self,
        worker: PersistentWhisperWorker,
        session_manager: SessionManager,
        recorder: AudioRecorder,
    ):
        self.worker = worker
        self.session_manager = session_manager
        self.recorder = recorder
        self._stop_event = asyncio.Event()
        self._streaming_task: Optional[asyncio.Task] = None

        # Buffer management (Zero-Leak)
        self._audio_buffer: list[np.ndarray] = []  # Kept for legacy ref, unused in loop
        self._pre_roll_buffer: list[np.ndarray] = []
        self._context_window: str = ""

        # Load config-driven parameters
        vad_config = config.transcription.whisper.vad_parameters
        self._silence_commit_ms = getattr(vad_config, 'min_silence_duration_ms', DEFAULT_SILENCE_COMMIT_MS)
        self._speech_threshold = vad_config.threshold  # Silero Probability Threshold (e.g. 0.4)

        # Load Silero VAD (SOTA 2026)
        try:
            self._vad_model = load_silero_vad(onnx=True)
            logger.info("✅ Silero VAD (ONNX) cargado para segmentación de alta precisión")
        except Exception as e:
            logger.error(f"❌ Error cargando Silero VAD: {e}. Usando fallback de energía.")
            self._vad_model = None
        # Context carry-over (200-char sliding window)
        self._context_window: str = ""

        # Silence tracking for segment commits
        self._silence_start: float | None = None

        # Pre-roll buffer to avoid cutting off speech start
        self._pre_roll_buffer: list[np.ndarray] = []

    async def start(self) -> None:
        """Starts the streaming transcription loop."""
        if self._streaming_task and not self._streaming_task.done():
            logger.warning("Streaming already active")
            return

        if not self.recorder:
            logger.error("No recorder provided to StreamingTranscriber")
            raise RuntimeError("No recorder")

        self.recorder.start()
        self._stop_event.clear()
        self._context_window = ""
        self._silence_start = None
        self._streaming_task = asyncio.create_task(self._loop())
        logger.info("Streaming started (SOTA 2026 Commit & Flush)")

    async def stop(self) -> str:
        """Stops streaming and returns final transcription."""
        if not self._streaming_task:
            return ""

        logger.info("Stopping streaming...")
        self._stop_event.set()

        result = ""
        try:
            result = await self._streaming_task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
        finally:
            self.recorder.stop()
            self._streaming_task = None

        return result

    def _detect_speech_silero(self, chunk: np.ndarray, threshold: float = 0.4) -> bool:
        """Use Silero VAD (ONNX) to detect speech probability."""
        if self._vad_model is None:
            return self._detect_speech_energy(chunk, 0.015)

        try:
            # Silero ONNX expects (Batch, Time) -> (1, N)
            if chunk.ndim == 1:
                chunk = chunk[np.newaxis, :]

            if chunk.shape[1] < 512:
                # Too small for reliable VAD, skip or assume silence?
                # Accumulate? For now just use energy fallback if small.
                return self._detect_speech_energy(chunk.flatten(), 0.015)

            speech_prob = self._vad_model(chunk, 16000)
            # speech_prob can be tensor or float.
            if hasattr(speech_prob, 'item'):
                val = speech_prob.item()
            else:
                val = speech_prob

            # logger.debug(f"VAD Prob: {val:.3f}")
            return val > threshold
        except Exception as e:
            logger.warning(f"Silero VAD error: {e}")
            return self._detect_speech_energy(chunk.flatten(), 0.015)

    def _detect_speech_energy(self, chunk: np.ndarray, threshold: float = 0.015) -> bool:
        """Fallback energy-based VAD."""
        if len(chunk) == 0:
            return False
        energy = np.sqrt(np.mean(chunk**2))
        return energy > threshold


    async def _loop(self) -> str:
        """
        SOTA 2026: Segment-based streaming with context carry-over.

        Flow:
        1. Accumulate audio chunks while speech detected
        2. On 800ms silence → COMMIT (final inference) → FLUSH buffer
        3. Carry context (last 200 chars) to next segment
        """
        all_final_text: list[str] = []
        current_segment_audio: list[np.ndarray] = []
        segment_duration = 0.0
        last_provisional_time = time.time()
        provisional_text = ""

        try:
            while not self._stop_event.is_set():
                # Non-blocking wait for data
                await self.recorder.wait_for_data()
                chunk = self.recorder.read_chunk()

                if len(chunk) == 0:
                    continue

                # Maintain pre-roll buffer (captures speech starts)
                self._pre_roll_buffer.append(chunk)
                if len(self._pre_roll_buffer) > PRE_ROLL_CHUNKS:
                    self._pre_roll_buffer.pop(0)

                # VAD Detection (Silero)
                is_speech = self._detect_speech_silero(chunk, self._speech_threshold)

                # Context Reset Logic (Anti-Hallucination)
                if self._silence_start:
                    silence_prob = (time.time() - self._silence_start) * 1000
                    if silence_prob > CONTEXT_RESET_MS and self._context_window:
                        # Clear context if silence is too long (new topic likely)
                        # logger.debug(f"Resetting context window (Silence > {CONTEXT_RESET_MS}ms)")
                        self._context_window = ""

                if is_speech and not current_segment_audio:
                    # Speech started - prepend pre-roll buffer
                    current_segment_audio.extend(self._pre_roll_buffer)
                    segment_duration = sum(len(c) / 16000 for c in current_segment_audio)
                elif is_speech:
                    # Continuing speech
                    current_segment_audio.append(chunk)
                    segment_duration += len(chunk) / 16000
                elif current_segment_audio:
                    # Silence with active segment - still accumulate
                    current_segment_audio.append(chunk)
                    segment_duration += len(chunk) / 16000

                # Provisional inference during speech
                if is_speech:
                    self._silence_start = None
                    now = time.time()
                    if (
                        now - last_provisional_time > PROVISIONAL_INTERVAL
                        and segment_duration > MIN_SEGMENT_DURATION
                    ):
                        last_provisional_time = now
                        text = await self._infer_provisional(current_segment_audio)
                        if text and text != provisional_text:
                            provisional_text = text
                            await self.session_manager.emit_event(
                                "transcription_update",
                                {"text": text, "final": False},
                            )
                elif current_segment_audio:
                    # Track silence duration (only when we have audio)
                    if self._silence_start is None:
                        self._silence_start = time.time()

                    silence_ms = (time.time() - self._silence_start) * 1000

                    # COMMIT if silence > threshold AND we have enough audio
                    if (
                        silence_ms > self._silence_commit_ms
                        and segment_duration > MIN_SEGMENT_DURATION
                    ):
                        logger.debug(
                            f"Committing segment: {segment_duration:.2f}s "
                            f"(silence: {silence_ms:.0f}ms)"
                        )

                        final_text = await self._infer_final(current_segment_audio)
                        if final_text:
                            all_final_text.append(final_text)
                            self._update_context_window(final_text)
                            await self.session_manager.emit_event(
                                "transcription_update",
                                {"text": final_text, "final": True},
                            )

                        # FLUSH - Zero-Leak buffer clear
                        current_segment_audio.clear()
                        segment_duration = 0.0
                        provisional_text = ""
                        self._silence_start = None

            # Final commit on stop (if any audio remains)
            if current_segment_audio and segment_duration > MIN_SEGMENT_DURATION:
                logger.debug(f"Final commit on stop: {segment_duration:.2f}s")
                final_text = await self._infer_final(current_segment_audio)
                if final_text:
                    all_final_text.append(final_text)
                    self._update_context_window(final_text)
                    await self.session_manager.emit_event(
                        "transcription_update",
                        {"text": final_text, "final": True},
                    )

            return " ".join(all_final_text)

        except Exception as e:
            logger.error(f"Streaming loop error: {e}")
            return " ".join(all_final_text) if all_final_text else ""

    def _detect_speech_energy(self, chunk: np.ndarray, threshold: float = 0.01) -> bool:
        """
        Simple energy-based speech detection.

        For production, integrate Silero VAD v5 here for better accuracy.
        """
        if len(chunk) == 0:
            return False
        energy = np.sqrt(np.mean(chunk**2))
        return energy > threshold

    def _build_context_prompt(self) -> str:
        """
        Build context prompt from sliding window.

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
            self._context_window = (
                self._context_window + " " + clean_text
            )[-CONTEXT_WINDOW_CHARS:]

    async def _infer_provisional(self, audio_chunks: list[np.ndarray]) -> str:
        """
        Fast provisional inference for real-time feedback.

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
        """
        High-quality final inference for committed segments.

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
