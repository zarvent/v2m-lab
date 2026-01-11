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
Servicio de Transcripción de Archivos.

Este módulo maneja la extracción y transcripción de audio desde diversos formatos
de archivo. Utiliza FFmpeg para extracción de audio de contenedores de video
(MP4, MOV, etc.) y faster-whisper para la transcripción.

Formatos soportados:
- Video: MP4, M4A (video), MOV, MKV, AVI, WEBM
- Audio: WAV, MP3, FLAC, OGG, M4A (audio), AAC, AIFF

SOTA 2026: Utiliza extracción PCM en streaming para minimizar I/O de disco.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from v2m.config import config
from v2m.core.logging import logger

if TYPE_CHECKING:
    from v2m.infrastructure.whisper_transcription_service import WhisperTranscriptionService

# Extensiones de audio que no necesitan extracción
AUDIO_EXTENSIONS = frozenset({".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac", ".aiff"})

# Extensiones de video que necesitan extracción de audio
VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".mkv", ".avi", ".webm"})

# Tiempo máximo para procesamiento de archivos (5 minutos)
FFMPEG_TIMEOUT = 300


class FileTranscriptionService:
    """
    Servicio para transcripción de archivos de audio/video.

    Utiliza FFmpeg para normalizar/extraer audio y el modelo Whisper existente
    para la transcripción. Diseñado para reutilizar el modelo ya cargado en memoria.
    """

    def __init__(self, transcription_service: WhisperTranscriptionService) -> None:
        """
        Inicializa el servicio.

        Args:
            transcription_service: Servicio de transcripción Whisper existente.
        """
        self._transcription_service = transcription_service
        self._ffmpeg_available: bool = self._check_ffmpeg()

    def _check_ffmpeg(self) -> bool:
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
            return True
        except FileNotFoundError:
            logger.warning("ffmpeg no encontrado - extracción de video deshabilitada")
            return False
        except subprocess.CalledProcessError as e:
            logger.warning(f"ffmpeg error: {e}")
            return False
        except subprocess.TimeoutExpired:
            logger.warning("ffmpeg timeout durante verificación")
            return False

    def transcribe_file(self, file_path: str) -> str:
        """
        Transcribe audio desde un archivo.

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
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"archivo no encontrado: {file_path}")

        suffix = path.suffix.lower()
        logger.info(f"procesando archivo: {path.name} ({suffix})")

        if suffix in VIDEO_EXTENSIONS:
            if not self._ffmpeg_available:
                raise RuntimeError(
                    "FFmpeg es requerido para archivos de video. "
                    "Instalar con: sudo apt install ffmpeg"
                )
            audio_data = self._extract_audio_from_video(path)

        elif suffix in AUDIO_EXTENSIONS:
            audio_data = self._load_and_normalize_audio(path)

        else:
            raise ValueError(
                f"formato no soportado: {suffix}. "
                f"Soportados: {', '.join(sorted(AUDIO_EXTENSIONS | VIDEO_EXTENSIONS))}"
            )

        return self._transcribe_audio_data(audio_data)

    def _extract_audio_from_video(self, video_path: Path) -> np.ndarray:
        """
        Extrae audio de video usando FFmpeg (streaming a memoria).

        Args:
            video_path: Ruta al archivo de video.

        Returns:
            Array numpy con datos de audio float32 a 16kHz mono.
        """
        logger.info(f"extrayendo audio de video: {video_path.name}")

        # Comando FFmpeg: extraer audio como 16kHz mono PCM f32le
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vn",  # Sin video
            "-acodec", "pcm_f32le",  # PCM 32-bit float
            "-ar", "16000",  # 16kHz para Whisper
            "-ac", "1",  # Mono
            "-f", "f32le",  # Formato raw
            "-loglevel", "error",
            "pipe:1",  # Output a stdout
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=FFMPEG_TIMEOUT,
            )
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"timeout extrayendo audio ({FFMPEG_TIMEOUT}s)") from e

        if result.returncode != 0:
            stderr = result.stderr.decode().strip()
            raise RuntimeError(f"error ffmpeg: {stderr}")

        audio_data = np.frombuffer(result.stdout, dtype=np.float32)
        duration = len(audio_data) / 16000
        logger.info(f"audio extraído: {duration:.1f}s")

        return audio_data

    def _load_and_normalize_audio(self, audio_path: Path) -> np.ndarray:
        """
        Carga archivo de audio y normaliza a formato Whisper.

        Args:
            audio_path: Ruta al archivo de audio.

        Returns:
            Array numpy con datos de audio float32 a 16kHz mono.
        """
        logger.info(f"cargando audio: {audio_path.name}")

        # Usar FFmpeg para normalizar cualquier formato a 16kHz mono f32
        cmd = [
            "ffmpeg",
            "-i", str(audio_path),
            "-acodec", "pcm_f32le",
            "-ar", "16000",
            "-ac", "1",
            "-f", "f32le",
            "-loglevel", "error",
            "pipe:1",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=120,  # 2 minutos para audio
            )
        except subprocess.TimeoutExpired as e:
            raise RuntimeError("timeout cargando audio (120s)") from e

        if result.returncode != 0:
            stderr = result.stderr.decode().strip()
            raise RuntimeError(f"error ffmpeg: {stderr}")

        audio_data = np.frombuffer(result.stdout, dtype=np.float32)
        duration = len(audio_data) / 16000
        logger.info(f"audio cargado: {duration:.1f}s")

        return audio_data

    def _transcribe_audio_data(self, audio_data: np.ndarray) -> str:
        """
        Transcribe datos de audio usando el modelo Whisper.

        Args:
            audio_data: Array numpy float32 a 16kHz mono.

        Returns:
            Texto transcrito.
        """
        duration = len(audio_data) / 16000
        logger.info(f"transcribiendo {duration:.1f}s de audio...")

        # Usar el modelo Whisper existente del servicio de transcripción
        model = self._transcription_service.model
        whisper_config = config.transcription.whisper

        # Configurar idioma
        lang = whisper_config.language
        if lang == "auto":
            lang = None

        segments, info = model.transcribe(
            audio_data,
            language=lang,
            task="transcribe",
            beam_size=whisper_config.beam_size,
            best_of=whisper_config.best_of,
            temperature=whisper_config.temperature,
            vad_filter=whisper_config.vad_filter,
            vad_parameters=whisper_config.vad_parameters.model_dump() if whisper_config.vad_filter else None,
        )

        if lang is None:
            logger.info(f"idioma detectado: {info.language} ({info.language_probability:.0%})")

        # Unir segmentos
        text = " ".join(segment.text.strip() for segment in segments)
        logger.info(f"transcripción completa: {len(text)} caracteres")

        return text
