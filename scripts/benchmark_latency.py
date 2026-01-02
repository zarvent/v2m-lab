#!/usr/bin/env python3

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
Benchmark de latencia End-to-End para voice2machine.

Mide:
1. Cold Start: Tiempo de carga del daemon y modelos
2. Inferencia Whisper: Tiempo de transcripción (GPU/CPU)
3. VAD: Tiempo de procesamiento de silencios (ONNX vs PyTorch)
4. Gemini: Latencia de red al LLM
5. E2E: Latencia total desde STOP_RECORDING hasta clipboard

Uso:
    python scripts/benchmark_latency.py [--iterations N] [--audio-file PATH]
"""

import sys
import time
import argparse
import statistics
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend" / "src"))

import numpy as np


@dataclass
class BenchmarkResult:
    """Resultado de un benchmark individual."""
    name: str
    times_ms: List[float] = field(default_factory=list)

    @property
    def mean(self) -> float:
        return statistics.mean(self.times_ms) if self.times_ms else 0

    @property
    def std(self) -> float:
        return statistics.stdev(self.times_ms) if len(self.times_ms) > 1 else 0

    @property
    def min(self) -> float:
        return min(self.times_ms) if self.times_ms else 0

    @property
    def max(self) -> float:
        return max(self.times_ms) if self.times_ms else 0

    @property
    def p95(self) -> float:
        if not self.times_ms:
            return 0
        sorted_times = sorted(self.times_ms)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]


def generate_test_audio(duration_sec: float = 3.0, sample_rate: int = 16000) -> np.ndarray:
    """Genera audio de prueba sintético (ruido blanco + silencios)."""
    total_samples = int(duration_sec * sample_rate)

    # Crear audio con patrón: silencio - ruido - silencio - ruido - silencio
    audio = np.zeros(total_samples, dtype=np.float32)

    # Segmento de "voz" (ruido con envolvente)
    voice_start = int(0.3 * sample_rate)
    voice_end = int(1.5 * sample_rate)
    voice_samples = voice_end - voice_start

    # Ruido con envolvente para simular habla
    noise = np.random.randn(voice_samples).astype(np.float32) * 0.3
    envelope = np.sin(np.linspace(0, np.pi, voice_samples)) ** 2
    audio[voice_start:voice_end] = noise * envelope

    # Segundo segmento
    voice_start2 = int(2.0 * sample_rate)
    voice_end2 = int(2.8 * sample_rate)
    voice_samples2 = voice_end2 - voice_start2
    noise2 = np.random.randn(voice_samples2).astype(np.float32) * 0.25
    envelope2 = np.sin(np.linspace(0, np.pi, voice_samples2)) ** 2
    audio[voice_start2:voice_end2] = noise2 * envelope2

    return audio


def benchmark_vad(iterations: int = 10) -> BenchmarkResult:
    """Benchmark del servicio VAD."""
    from v2m.infrastructure.vad_service import VADService

    result = BenchmarkResult(name="VAD Processing")
    audio = generate_test_audio(duration_sec=5.0)

    # Warmup
    vad = VADService(prefer_onnx=True)
    try:
        vad.load_model()
    except Exception as e:
        print(f"  ⚠️  VAD no disponible: {e}")
        return result

    print(f"  Backend VAD: {vad._backend}")

    # Benchmark
    for i in range(iterations):
        # Reset estados para medición limpia
        if vad._backend == 'onnx':
            vad._reset_onnx_states()

        start = time.perf_counter()
        _ = vad.process(audio.copy())
        elapsed_ms = (time.perf_counter() - start) * 1000
        result.times_ms.append(elapsed_ms)

    return result


def benchmark_whisper(iterations: int = 5) -> BenchmarkResult:
    """Benchmark de transcripción Whisper."""
    from v2m.infrastructure.whisper_transcription_service import WhisperTranscriptionService
    from v2m.infrastructure.vad_service import VADService

    result = BenchmarkResult(name="Whisper Transcription")
    audio = generate_test_audio(duration_sec=3.0)

    # Crear servicio
    vad = VADService(prefer_onnx=True)
    service = WhisperTranscriptionService(vad_service=vad)

    # Warmup (carga modelo)
    print("  Cargando modelo Whisper...")
    start_load = time.perf_counter()
    try:
        _ = service.model
    except Exception as e:
        print(f"  ⚠️  Whisper no disponible: {e}")
        return result
    load_time = (time.perf_counter() - start_load) * 1000
    print(f"  Modelo cargado en {load_time:.0f}ms")

    # Benchmark (solo inferencia, sin grabación)
    for i in range(iterations):
        start = time.perf_counter()

        # Simular transcripción directa del audio
        segments, _ = service.model.transcribe(
            audio,
            language="es",
            beam_size=2,
            best_of=2,
            vad_filter=False
        )
        # Consumir generador
        text = " ".join([s.text for s in segments])

        elapsed_ms = (time.perf_counter() - start) * 1000
        result.times_ms.append(elapsed_ms)

    return result


def benchmark_audio_buffer(iterations: int = 20) -> BenchmarkResult:
    """Benchmark del buffer de audio (concatenación)."""
    from v2m.infrastructure.audio.recorder import AudioRecorder

    result = BenchmarkResult(name="Audio Buffer (stop)")

    # Simular grabación de 5 segundos
    sample_rate = 16000
    duration = 5.0
    chunk_size = 1024
    total_samples = int(duration * sample_rate)

    for i in range(iterations):
        recorder = AudioRecorder(sample_rate=sample_rate)

        # Simular escritura al buffer (sin stream real)
        recorder._recording = True
        test_audio = np.random.randn(total_samples).astype(np.float32) * 0.1

        # Escribir en chunks como haría el callback
        for j in range(0, len(test_audio), chunk_size):
            chunk = test_audio[j:j+chunk_size]
            end_pos = recorder._write_pos + len(chunk)
            if end_pos <= recorder.max_samples:
                recorder._buffer[recorder._write_pos:end_pos] = chunk
                recorder._write_pos = end_pos

        # Medir tiempo de stop (extracción del buffer)
        start = time.perf_counter()
        recorder._recording = False
        audio_out = recorder._buffer[:recorder._write_pos]
        elapsed_ms = (time.perf_counter() - start) * 1000
        result.times_ms.append(elapsed_ms)

    return result


def benchmark_cold_start() -> BenchmarkResult:
    """Mide el tiempo de cold start (importación del container)."""
    result = BenchmarkResult(name="Cold Start (container)")

    # Solo una medición porque es destructiva
    start = time.perf_counter()

    # Forzar reimportación
    import importlib
    if 'v2m.core.di.container' in sys.modules:
        del sys.modules['v2m.core.di.container']

    from v2m.core.di import container as container_module
    importlib.reload(container_module)

    elapsed_ms = (time.perf_counter() - start) * 1000
    result.times_ms.append(elapsed_ms)

    return result


def print_results(results: List[BenchmarkResult]):
    """Imprime resultados en formato tabla."""
    print("\n" + "=" * 70)
    print("📊 RESULTADOS DEL BENCHMARK")
    print("=" * 70)
    print(f"{'Componente':<30} {'Mean':>10} {'Std':>10} {'Min':>10} {'P95':>10}")
    print("-" * 70)

    total_mean = 0
    for r in results:
        if r.times_ms:
            print(f"{r.name:<30} {r.mean:>9.1f}ms {r.std:>9.1f}ms {r.min:>9.1f}ms {r.p95:>9.1f}ms")
            total_mean += r.mean
        else:
            print(f"{r.name:<30} {'N/A':>10} {'N/A':>10} {'N/A':>10} {'N/A':>10}")

    print("-" * 70)
    print(f"{'TOTAL ESTIMADO':<30} {total_mean:>9.1f}ms")
    print("=" * 70)

    # Evaluación
    if total_mean < 100:
        print("✅ Objetivo de <100ms ALCANZADO")
    elif total_mean < 200:
        print("⚠️  Latencia aceptable pero mejorable")
    else:
        print("🚨 Latencia excesiva - revisar optimizaciones")


def main():
    parser = argparse.ArgumentParser(description="Benchmark de latencia v2m")
    parser.add_argument("--iterations", "-n", type=int, default=10,
                        help="Número de iteraciones por benchmark")
    parser.add_argument("--skip-whisper", action="store_true",
                        help="Omitir benchmark de Whisper (lento)")
    args = parser.parse_args()

    print("🚀 Iniciando benchmark de latencia voice2machine")
    print(f"   Iteraciones: {args.iterations}")
    print()

    results = []

    # 1. Cold Start
    print("1️⃣  Benchmark: Cold Start...")
    results.append(benchmark_cold_start())

    # 2. Audio Buffer
    print("2️⃣  Benchmark: Audio Buffer...")
    results.append(benchmark_audio_buffer(iterations=args.iterations))

    # 3. VAD
    print("3️⃣  Benchmark: VAD...")
    results.append(benchmark_vad(iterations=args.iterations))

    # 4. Whisper
    if not args.skip_whisper:
        print("4️⃣  Benchmark: Whisper Transcription...")
        results.append(benchmark_whisper(iterations=min(args.iterations, 5)))

    # Resultados
    print_results(results)


if __name__ == "__main__":
    main()
