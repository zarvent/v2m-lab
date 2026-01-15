#!/usr/bin/env python3
"""
Transcribe voz al portapapeles - Ultra-rápido, local y preciso.

Flujo: Grabación → Transcripción → Portapapeles → Limpieza
Rendimiento: Arranque en frío ~1.5s (carga del modelo), ejecuciones posteriores <500ms de inferencia.

Uso:
    python transcribe_to_clipboard.py          # Presiona Enter para detener
    python transcribe_to_clipboard.py -t 10    # Parada automática tras 10 segundos
    python transcribe_to_clipboard.py -m turbo  # Usa un modelo específico
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

# -----------------------------------------------------------------------------
# Configuración
# -----------------------------------------------------------------------------
DEFAULT_MODEL = "turbo"  # El modelo más rápido con excelente precisión (2024+)
DEFAULT_DEVICE = "cuda" if shutil.which("nvidia-smi") else "cpu"
DEFAULT_COMPUTE_TYPE = "float16" if DEFAULT_DEVICE == "cuda" else "int8"
SAMPLE_RATE = 16000  # Whisper requiere 16kHz
CHANNELS = 1

# -----------------------------------------------------------------------------
# Importaciones diferidas (Lazy loading) para un arranque más rápido
# -----------------------------------------------------------------------------
_model: "WhisperModel | None" = None


def _get_model(model_name: str) -> "WhisperModel":
    """Carga el modelo de forma perezosa (on-demand) en el primer uso."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        _model = WhisperModel(
            model_name,
            device=DEFAULT_DEVICE,
            compute_type=DEFAULT_COMPUTE_TYPE,
            cpu_threads=os.cpu_count() or 4,
        )
    return _model


def _get_clipboard_cmd() -> list[str]:
    """Detecta el backend del portapapeles: Wayland (wl-copy) o X11 (xclip)."""
    if os.environ.get("WAYLAND_DISPLAY"):
        if shutil.which("wl-copy"):
            return ["wl-copy"]
    if shutil.which("xclip"):
        return ["xclip", "-selection", "clipboard"]
    raise RuntimeError("No se encontró una herramienta de portapapeles. Instala xclip o wl-copy.")


def record_audio(duration: float | None = None) -> bytes:
    """
    Graba audio desde el micrófono predeterminado.

    Si 'duration' es None, graba hasta que se presiona Enter.
    Devuelve los bytes PCM crudos (16-bit, mono, 16kHz).
    """
    import numpy as np
    import sounddevice as sd

    frames: list[np.ndarray] = []
    stop_flag = False

    def callback(indata: np.ndarray, _frames: int, _time: object, _status: object) -> None:
        if not stop_flag:
            frames.append(indata.copy())

    print("🎙️  Grabando... (Presiona Enter para detener)" if duration is None else f"🎙️  Grabando por {duration}s...")

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        callback=callback,
        blocksize=1024,
    )

    with stream:
        if duration is not None:
            time.sleep(duration)
        else:
            # Esperar la tecla Enter (hacerlo no-bloqueante requeriría hilos o asincronía)
            input()
        stop_flag = True

    if not frames:
        return b""

    audio = np.concatenate(frames, axis=0).flatten()

    # Convertir float32 [-1, 1] a int16 para el formato WAV
    audio_int16 = (audio * 32767).astype(np.int16)
    return audio_int16.tobytes()


def save_wav(pcm_data: bytes, path: Path) -> None:
    """Escribe los datos PCM en un archivo WAV."""
    import wave

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit = 2 bytes
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_data)


def transcribe(audio_path: Path, model_name: str, language: str | None = None) -> str:
    """Transcribe un archivo de audio usando faster-whisper."""
    t0 = time.perf_counter()
    model = _get_model(model_name)

    segments, info = model.transcribe(
        str(audio_path),
        language=language,
        vad_filter=True,  # Omitir silencios para mayor velocidad
        vad_parameters={"min_silence_duration_ms": 300},
        beam_size=1,  # Búsqueda codiciosa (greedy) para máxima velocidad de inferencia
        word_timestamps=False,
    )

    text = " ".join(seg.text.strip() for seg in segments)
    elapsed = time.perf_counter() - t0

    print(f"⚡ Transcrito en {elapsed:.2f}s | Idioma detectado: {info.language} ({info.language_probability:.0%})")
    return text


def copy_to_clipboard(text: str) -> None:
    """Copia el texto al portapapeles del sistema."""
    cmd = _get_clipboard_cmd()
    subprocess.run(cmd, input=text.encode(), check=True)
    print(f"📋 Copiado al portapapeles: {text[:80]}{'...' if len(text) > 80 else ''}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Graba voz, transcribe localmente y copia al portapapeles.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-t", "--time", type=float, help="Duración de la grabación en segundos (por defecto: parada manual)")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, help=f"Modelo de Whisper (por defecto: {DEFAULT_MODEL})")
    parser.add_argument("-l", "--language", default=None, help="Código de idioma (ej. 'en', 'es'). Autodetectado si se omite.")
    parser.add_argument("-k", "--keep", action="store_true", help="Mantener el archivo de audio tras la transcripción")
    args = parser.parse_args()

    # 1. Grabar
    pcm_data = record_audio(args.time)
    if not pcm_data:
        print("❌ No se grabó audio.")
        return 1

    # 2. Guardar en un WAV temporal
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = Path(tmp.name)

    save_wav(pcm_data, audio_path)

    try:
        # 3. Transcribir
        text = transcribe(audio_path, args.model, args.language)
        if not text.strip():
            print("❌ No se detectó habla.")
            return 1

        # 4. Copiar al portapapeles
        copy_to_clipboard(text.strip())
        return 0

    finally:
        # 5. Limpieza (a menos que se use --keep)
        if not args.keep and audio_path.exists():
            audio_path.unlink()


if __name__ == "__main__":
    sys.exit(main())
