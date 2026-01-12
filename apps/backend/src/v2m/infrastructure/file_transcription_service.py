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

"""
Servicio de Transcripción de Archivos (SOTA 2026).

Este módulo maneja la extracción y transcripción de audio desde diversos formatos
de archivo. Optimizado para rendimiento extremo siguiendo filosofía "do more with less".

Optimizaciones implementadas:
- Async FFmpeg: asyncio subprocess para I/O no bloqueante
- Streaming PCM: Extracción directa a memoria sin archivos temporales
- Timing metrics: Logging detallado de cada fase para profiling
- Zero-copy: Reutilización del modelo Whisper ya cargado

Formatos soportados:
- Video: MP4, M4A (video), MOV, MKV, AVI, WEBM
- Audio: WAV, MP3, FLAC, OGG, M4A (audio), AAC, AIFF
"""

from __future__ import annotations

import asyncio
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from v2m.config import config
from v2m.core.logging import logger

if TYPE_CHECKING:
    from v2m.infrastructure.whisper_transcription_service import WhisperTranscriptionService

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

    Performance Philosophy (極限最適化):
    - Cada ms cuenta: timing metrics en cada fase
    - Zero disk I/O: streaming directo a memoria
    - Single model: reutiliza instancia Whisper del daemon
    """

    __slots__ = ("_transcription_service", "_ffmpeg_available", "_ffmpeg_version")

    def __init__(self, transcription_service: WhisperTranscriptionService) -> None:
        """
        Inicializa el servicio.

        Args:
            transcription_service: Servicio de transcripción Whisper existente.
        """
        self._transcription_service = transcription_service
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

        Para archivos de video, extrae el audio primero usando FFmpeg.
        Para archivos de audio, los normaliza directamente.

        Args:
            file_path: Ruta al archivo a transcribir.

        Returns:
            Texto transcrito.

        Raises:
            FileNotFoundError: Si el archivo no existe.
            ValueError: Si el formato no es soportado.
            RuntimeError: Si FFmpeg no está disponible para videos.
        """
        # Ejecutar versión async en un nuevo event loop si no hay uno activo
        try:
            loop = asyncio.get_running_loop()
            # Ya estamos en un loop - esto no debería pasar con el executor
            return asyncio.run_coroutine_threadsafe(
                self._transcribe_file_async(file_path), loop
            ).result()
        except RuntimeError:
            # No hay loop - crear uno nuevo (caso normal desde executor)
            return asyncio.run(self._transcribe_file_async(file_path))

    async def _transcribe_file_async(self, file_path: str) -> str:
        """
        Transcribe audio desde un archivo (async implementation).

        Args:
            file_path: Ruta al archivo a transcribir.

        Returns:
            Texto transcrito.
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
                raise RuntimeError(
                    "FFmpeg es requerido para archivos de video. "
                    "Instalar con: sudo apt install ffmpeg"
                )
            audio_data = await self._extract_audio_async(path, is_video=True)

        elif suffix in AUDIO_EXTENSIONS:
            audio_data = await self._extract_audio_async(path, is_video=False)

        else:
            raise ValueError(
                f"formato no soportado: {suffix}. "
                f"Soportados: {', '.join(sorted(AUDIO_EXTENSIONS | VIDEO_EXTENSIONS))}"
            )

        extraction_time = time.perf_counter() - extraction_start
        duration_secs = len(audio_data) / 16000
        logger.info(f"⏱️ extracción: {extraction_time:.2f}s ({duration_secs:.1f}s audio)")

        # --- Fase 2: Transcripción con Whisper ---
        transcription_start = time.perf_counter()
        text = self._transcribe_audio_data(audio_data)
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
        """
        Extrae/normaliza audio usando FFmpeg con async subprocess.

        Args:
            file_path: Ruta al archivo.
            is_video: True si es un archivo de video.

        Returns:
            Array numpy con datos de audio float32 a 16kHz mono.
        """
        timeout = FFMPEG_TIMEOUT_VIDEO if is_video else FFMPEG_TIMEOUT_AUDIO
        action = "extrayendo de video" if is_video else "normalizando"
        logger.debug(f"🎵 {action}: {file_path.name}")

        # Comando FFmpeg optimizado: 16kHz mono PCM f32le directo a stdout
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-i", str(file_path),
            "-vn",  # Sin video
            "-acodec", "pcm_f32le",  # PCM 32-bit float (nativo para Whisper)
            "-ar", "16000",  # 16kHz (requerido por Whisper)
            "-ac", "1",  # Mono
            "-f", "f32le",  # Formato raw sin header
            "pipe:1",  # Output a stdout
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

        except asyncio.TimeoutError as e:
            raise RuntimeError(f"timeout {action} ({timeout}s)") from e

        if proc.returncode != 0:
            stderr_text = stderr.decode().strip()
            raise RuntimeError(f"error ffmpeg: {stderr_text}")

        audio_data = np.frombuffer(stdout, dtype=np.float32)
        return audio_data

    def _transcribe_audio_data(self, audio_data: np.ndarray) -> str:
        """
        Transcribe datos de audio usando el modelo Whisper.

        SOTA 2026: Usa BatchedInferencePipeline para archivos largos (>30s)
        para maximizar utilización de GPU (~3x speedup).

        Args:
            audio_data: Array numpy float32 a 16kHz mono.

        Returns:
            Texto transcrito.
        """
        duration = len(audio_data) / 16000

        # Usar el modelo Whisper existente del servicio de transcripción
        model = self._transcription_service.model
        whisper_config = config.transcription.whisper

        # Configurar idioma
        lang = whisper_config.language
        if lang == "auto":
            lang = None

        # OPTIMIZATION: Use batched inference for long files (>30s)
        # BatchedInferencePipeline provides ~3x speedup by maximizing GPU utilization
        use_batched = duration > 30.0

        if use_batched:
            logger.debug(f"🚀 usando batched inference ({duration:.0f}s audio)")
            pipeline = _get_batched_pipeline(model)
            segments, info = pipeline.transcribe(
                audio_data,
                language=lang,
                task="transcribe",
                beam_size=whisper_config.beam_size,
                temperature=whisper_config.temperature,
                vad_filter=whisper_config.vad_filter,
                vad_parameters=(
                    whisper_config.vad_parameters.model_dump()
                    if whisper_config.vad_filter
                    else None
                ),
                batch_size=16,  # Optimal for RTX 3060 6GB VRAM
            )
        else:
            # Standard inference for short files (lower overhead)
            segments, info = model.transcribe(
                audio_data,
                language=lang,
                task="transcribe",
                beam_size=whisper_config.beam_size,
                best_of=whisper_config.best_of,
                temperature=whisper_config.temperature,
                vad_filter=whisper_config.vad_filter,
                vad_parameters=(
                    whisper_config.vad_parameters.model_dump()
                    if whisper_config.vad_filter
                    else None
                ),
            )

        if lang is None:
            logger.info(
                f"🌐 idioma detectado: {info.language} ({info.language_probability:.0%})"
            )

        # Unir segmentos eficientemente
        text = " ".join(segment.text.strip() for segment in segments)
        return text

