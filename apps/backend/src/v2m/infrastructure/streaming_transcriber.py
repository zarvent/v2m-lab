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

import numpy as np

from v2m.config import config
from v2m.core.client_session import ClientSessionManager
from v2m.infrastructure.persistent_model import PersistentWhisperWorker

logger = logging.getLogger(__name__)

# Streaming behavior defaults (can be overridden via config)
DEFAULT_SILENCE_COMMIT_MS = 800  # Spanish prosody safe threshold
MIN_SEGMENT_DURATION = 0.5  # Minimum audio before inference (seconds)
PROVISIONAL_INTERVAL = 0.5  # Interval between provisional inferences
CONTEXT_WINDOW_CHARS = 200  # Max chars for context (avoids 224-token limit)
PRE_ROLL_CHUNKS = 3  # Keep last N chunks to avoid cutting speech start


class StreamingTranscriber:
    """
    SOTA 2026 Segment-based Streaming Transcriber.

    Implements Commit & Flush architecture:
    - Accumulates audio until VAD detects 800ms silence
    - Commits segment with final inference
    - Flushes buffer (zero memory leak)
    - Carries context to next segment via initial_prompt
    """

    def __init__(
        self,
        worker: PersistentWhisperWorker,
        session_manager: ClientSessionManager,
        recorder=None,
    ):
        self.worker = worker
        self.session_manager = session_manager
        self.recorder = recorder

        # Load config-driven parameters
        vad_config = config.transcription.whisper.vad_parameters
        self._silence_commit_ms = getattr(vad_config, 'min_silence_duration_ms', DEFAULT_SILENCE_COMMIT_MS)
        self._speech_threshold = getattr(vad_config, 'threshold', 0.3)

        # Task management
        self._streaming_task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

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
        try:
            final_text = await self._streaming_task
            return final_text
        except asyncio.CancelledError:
            return ""
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            return ""
        finally:
            self.recorder.stop()
            self._streaming_task = None

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

                # Check for speech using energy-based detection
                is_speech = self._detect_speech_energy(chunk, self._speech_threshold)

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
