
"""
Servicio de Transcripción de Archivos (SOTA 2026).

Este módulo maneja la extracción y transcripción de audio desde diversos formatos
de archivo. Optimizado para rendimiento extremo siguiendo filosofía "do more with less".

Optimizaciones implementadas:
- Async FFmpeg: asyncio subprocess para I/O no bloqueante
- Streaming PCM: Extracción directa a memoria sin archivos temporales
- Timing metrics: Logging detallado de cada fase para profiling
- Zero-copy: Reutilización del modelo Whisper via PersistentWorker
"""

from __future__ import annotations

import asyncio
import subprocess
import time
from pathlib import Path

import numpy as np

from v2m.config import config
from v2m.core.logging import logger
from v2m.infrastructure.persistent_model import PersistentWhisperWorker

# Lazy import for BatchedInferencePipeline (reduces startup time)
_batched_pipeline = None


def _get_batched_pipeline(model):
    """Lazily create BatchedInferencePipeline wrapper."""
    global _batched_pipeline
    if _batched_pipeline is None:
        from faster_whisper import BatchedInferencePipeline

        _batched_pipeline = BatchedInferencePipeline(model)
    return _batched_pipeline


# Extensiones de audio que no necesitan extracción
AUDIO_EXTENSIONS = frozenset({".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac", ".aiff"})

# Extensiones de video que necesitan extracción de audio
VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".mkv", ".avi", ".webm"})

# Timeouts optimizados (segundos)
FFMPEG_TIMEOUT_VIDEO = 300  # 5 min para video
FFMPEG_TIMEOUT_AUDIO = 120  # 2 min para audio


class FileTranscriptionService:
    """
    Servicio para transcripción de archivos de audio/video.

    Utiliza FFmpeg para normalizar/extraer audio y el modelo Whisper existente
    para la transcripción. Diseñado para reutilizar el modelo ya cargado en memoria.
    """

    __slots__ = ("_ffmpeg_available", "_ffmpeg_version", "worker")

    def __init__(self, worker: PersistentWhisperWorker) -> None:
        """
        Inicializa el servicio.

        Args:
            worker: Worker persistente que contiene el modelo Whisper.
        """
        self.worker = worker
        self._ffmpeg_available, self._ffmpeg_version = self._check_ffmpeg()

    def _check_ffmpeg(self) -> tuple[bool, str]:
        """Verifica si FFmpeg está disponible en el sistema."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=True,
                timeout=5,
            )
            version_line = result.stdout.decode().split("\n")[0]
            logger.info(f"ffmpeg detectado: {version_line[:50]}")
            return True, version_line[:50]
        except FileNotFoundError:
            logger.warning("ffmpeg no encontrado - extracción de video deshabilitada")
            return False, ""
        except subprocess.CalledProcessError as e:
            logger.warning(f"ffmpeg error: {e}")
            return False, ""
        except subprocess.TimeoutExpired:
            logger.warning("ffmpeg timeout durante verificación")
            return False, ""

    def transcribe_file(self, file_path: str) -> str:
        """
        Transcribe audio desde un archivo (sync wrapper para async).
        """
        # Ejecutar versión async
        try:
            loop = asyncio.get_running_loop()
            return asyncio.run_coroutine_threadsafe(self._transcribe_file_async(file_path), loop).result()
        except RuntimeError:
            return asyncio.run(self._transcribe_file_async(file_path))

    async def _transcribe_file_async(self, file_path: str) -> str:
        """
        Transcribe audio desde un archivo (async implementation).
        """
        total_start = time.perf_counter()
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"archivo no encontrado: {file_path}")

        suffix = path.suffix.lower()
        file_size_mb = path.stat().st_size / (1024 * 1024)
        logger.info(f"📂 procesando: {path.name} ({suffix}, {file_size_mb:.1f}MB)")

        # --- Fase 1: Extracción de Audio ---
        extraction_start = time.perf_counter()

        if suffix in VIDEO_EXTENSIONS:
            if not self._ffmpeg_available:
                raise RuntimeError("FFmpeg es requerido para archivos de video. Instalar con: sudo apt install ffmpeg")
            audio_data = await self._extract_audio_async(path, is_video=True)

        elif suffix in AUDIO_EXTENSIONS:
            audio_data = await self._extract_audio_async(path, is_video=False)

        else:
            raise ValueError(
                f"formato no soportado: {suffix}. Soportados: {', '.join(sorted(AUDIO_EXTENSIONS | VIDEO_EXTENSIONS))}"
            )

        extraction_time = time.perf_counter() - extraction_start
        duration_secs = len(audio_data) / 16000
        logger.info(f"⏱️ extracción: {extraction_time:.2f}s ({duration_secs:.1f}s audio)")

        # --- Fase 2: Transcripción con Whisper ---
        transcription_start = time.perf_counter()
        # Await the async transcription wrapper
        text = await self._transcribe_audio_data_async(audio_data)
        transcription_time = time.perf_counter() - transcription_start

        # --- Metrics Finales ---
        total_time = time.perf_counter() - total_start
        rtf = transcription_time / duration_secs if duration_secs > 0 else 0

        logger.info(
            f"✅ transcripción completa: {len(text)} chars | "
            f"total: {total_time:.2f}s | "
            f"whisper: {transcription_time:.2f}s | "
            f"RTF: {rtf:.2f}x"
        )

        return text

    async def _extract_audio_async(self, file_path: Path, *, is_video: bool) -> np.ndarray:
        """Extrae/normaliza audio usando FFmpeg con async subprocess."""
        timeout = FFMPEG_TIMEOUT_VIDEO if is_video else FFMPEG_TIMEOUT_AUDIO
        action = "extrayendo de video" if is_video else "normalizando"
        logger.debug(f"🎵 {action}: {file_path.name}")

        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(file_path),
            "-vn",
            "-acodec",
            "pcm_f32le",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-f",
            "f32le",
            "pipe:1",
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )

        except TimeoutError as e:
            raise RuntimeError(f"timeout {action} ({timeout}s)") from e

        if proc.returncode != 0:
            stderr_text = stderr.decode().strip()
            raise RuntimeError(f"error ffmpeg: {stderr_text}")

        audio_data = np.frombuffer(stdout, dtype=np.float32)
        return audio_data

    async def _transcribe_audio_data_async(self, audio_data: np.ndarray) -> str:
        """
        Transcribe datos de audio usando el modelo Whisper via PersistentWorker.
        """
        duration = len(audio_data) / 16000
        whisper_config = config.transcription.whisper

        use_batched = duration > 30.0

        # Define the inference function to run on the worker thread
        def _inference(model):
            lang = whisper_config.language
            if lang == "auto":
                lang = None

            if use_batched:
                pipeline = _get_batched_pipeline(model)
                segments, info = pipeline.transcribe(
                    audio_data,
                    language=lang,
                    task="transcribe",
                    beam_size=whisper_config.beam_size,
                    temperature=whisper_config.temperature,
                    vad_filter=whisper_config.vad_filter,
                    vad_parameters=(whisper_config.vad_parameters.model_dump() if whisper_config.vad_filter else None),
                    batch_size=16,
                )
            else:
                segments, info = model.transcribe(
                    audio_data,
                    language=lang,
                    task="transcribe",
                    beam_size=whisper_config.beam_size,
                    best_of=whisper_config.best_of,
                    temperature=whisper_config.temperature,
                    vad_filter=whisper_config.vad_filter,
                    vad_parameters=(whisper_config.vad_parameters.model_dump() if whisper_config.vad_filter else None),
                )

            # Materialize generator in executor
            seg_list = list(segments)
            return seg_list, info

        # Execute using worker
        logger.debug(f"🚀 enviando a worker (batched={use_batched})")
        segments, info = await self.worker.run_inference(_inference)

        if info.language_probability:
            logger.info(f"🌐 idioma detectado: {info.language} ({info.language_probability:.0%})")

        text = " ".join(segment.text.strip() for segment in segments)
        return text
