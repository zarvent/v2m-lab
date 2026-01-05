#!/usr/bin/env python3

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
Benchmark de Latencia End-to-End para Voice2Machine.

Herramienta de análisis de rendimiento que desglosa la latencia del sistema
en componentes individuales para identificar cuellos de botella.

Métricas clave:
    1. Cold Start: Tiempo de carga inicial del contenedor DI y modelos.
    2. Whisper: Tiempo de inferencia de transcripción (CPU/GPU).
    3. Audio Buffer: Overhead de manipulación de arrays numpy.
    4. E2E: Latencia total estimada percibida por el usuario.

Uso:
    python scripts/benchmark_latency.py [--iterations N] [--skip-whisper]
"""

import sys
import time
import argparse
import statistics
from pathlib import Path
from typing import List
from dataclasses import dataclass, field

# Inyectar src al path para importar módulos internos
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend" / "src"))

import numpy as np


@dataclass
class BenchmarkResult:
    """DTO para almacenar estadísticas de rendimiento."""
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
        """Percentil 95 (latencia de cola)."""
        if not self.times_ms:
            return 0
        sorted_times = sorted(self.times_ms)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]


def generate_test_audio(duration_sec: float = 3.0, sample_rate: int = 16000) -> np.ndarray:
    """
    Genera audio sintético para pruebas de estrés.
    Crea un patrón de Silencio-Ruido-Silencio para simular habla real.
    """
    total_samples = int(duration_sec * sample_rate)
    audio = np.zeros(total_samples, dtype=np.float32)

    # Simular ráfaga de voz
    voice_start = int(0.3 * sample_rate)
    voice_end = int(1.5 * sample_rate)
    voice_samples = voice_end - voice_start

    # Ruido modulado por envolvente sinusoidal
    noise = np.random.randn(voice_samples).astype(np.float32) * 0.3
    envelope = np.sin(np.linspace(0, np.pi, voice_samples)) ** 2
    audio[voice_start:voice_end] = noise * envelope

    return audio


def benchmark_whisper(iterations: int = 5) -> BenchmarkResult:
    """Mide el rendimiento puro del motor de transcripción."""
    from v2m.infrastructure.whisper_transcription_service import WhisperTranscriptionService

    result = BenchmarkResult(name="Inferencia Whisper")
    audio = generate_test_audio(duration_sec=3.0)

    # Instanciar servicio (aislado)
    service = WhisperTranscriptionService()

    # Warmup: Carga de modelo en GPU/CPU
    print("  Cargando modelo Whisper...")
    start_load = time.perf_counter()
    try:
        _ = service.model
    except Exception as e:
        print(f"  ⚠️  Whisper no disponible: {e}")
        return result
    load_time = (time.perf_counter() - start_load) * 1000
    print(f"  Modelo cargado en {load_time:.0f}ms")

    # Bucle de inferencia
    for i in range(iterations):
        start = time.perf_counter()

        # Transcripción directa (bypass de grabación)
        segments, _ = service.model.transcribe(
            audio,
            language="es",
            beam_size=2,
            best_of=2,
            vad_filter=False # Desactivar VAD para medir solo Whisper
        )
        # Consumir generador para forzar cómputo
        _ = " ".join([s.text for s in segments])

        elapsed_ms = (time.perf_counter() - start) * 1000
        result.times_ms.append(elapsed_ms)

    return result


def benchmark_audio_buffer(iterations: int = 20) -> BenchmarkResult:
    """Mide la latencia de manipulación de buffers de audio."""
    from v2m.infrastructure.audio.recorder import AudioRecorder

    result = BenchmarkResult(name="Gestión Buffer Audio")

    sample_rate = 16000
    duration = 5.0
    chunk_size = 1024
    total_samples = int(duration * sample_rate)

    for i in range(iterations):
        recorder = AudioRecorder(sample_rate=sample_rate)

        # Simular estado interno sucio
        recorder._recording = True
        test_audio = np.random.randn(total_samples).astype(np.float32) * 0.1

        # Simular llenado de buffer por chunks (comportamiento de PortAudio)
        for j in range(0, len(test_audio), chunk_size):
            chunk = test_audio[j:j+chunk_size]
            end_pos = recorder._write_pos + len(chunk)
            if end_pos <= recorder.max_samples:
                # Escritura directa en numpy array pre-allocado
                if recorder._buffer is not None:
                    recorder._buffer[recorder._write_pos:end_pos] = chunk
                recorder._write_pos = end_pos

        # Medir operación crítica: Corte y copia del buffer al detener
        start = time.perf_counter()
        recorder._recording = False
        if recorder._buffer is not None:
            _ = recorder._buffer[:recorder._write_pos].copy()

        elapsed_ms = (time.perf_counter() - start) * 1000
        result.times_ms.append(elapsed_ms)

    return result


def benchmark_cold_start() -> BenchmarkResult:
    """Mide el tiempo de arranque en frío (importación de dependencias pesadas)."""
    result = BenchmarkResult(name="Cold Start (DI Container)")

    start = time.perf_counter()

    # Forzar recarga limpia del contenedor de inyección de dependencias
    import importlib
    if 'v2m.core.di.container' in sys.modules:
        del sys.modules['v2m.core.di.container']

    from v2m.core.di import container as container_module
    importlib.reload(container_module)

    elapsed_ms = (time.perf_counter() - start) * 1000
    result.times_ms.append(elapsed_ms)

    return result


def print_results(results: List[BenchmarkResult]):
    """Renderiza tabla de resultados en consola."""
    print("\n" + "=" * 70)
    print("📊 INFORME DE LATENCIA")
    print("=" * 70)
    print(f"{'Métrica':<30} {'Media':>10} {'Std':>10} {'Min':>10} {'P95':>10}")
    print("-" * 70)

    total_mean = 0
    for r in results:
        if r.times_ms:
            print(f"{r.name:<30} {r.mean:>9.1f}ms {r.std:>9.1f}ms {r.min:>9.1f}ms {r.p95:>9.1f}ms")
            total_mean += r.mean
        else:
            print(f"{r.name:<30} {'N/A':>10} {'N/A':>10} {'N/A':>10} {'N/A':>10}")

    print("-" * 70)
    print(f"{'TOTAL ACUMULADO':<30} {total_mean:>9.1f}ms")
    print("=" * 70)

    # Heurística de calidad
    if total_mean < 200:
        print("✅ Latencia EXCELENTE (<200ms)")
    elif total_mean < 500:
        print("⚠️  Latencia ACEPTABLE (200-500ms)")
    else:
        print("🚨 Latencia CRÍTICA (>500ms) - Optimización requerida")


def main():
    parser = argparse.ArgumentParser(description="Suite de benchmarking para V2M")
    parser.add_argument("--iterations", "-n", type=int, default=10,
                        help="Repeticiones por prueba (para validez estadística)")
    parser.add_argument("--skip-whisper", action="store_true",
                        help="Saltar prueba de Whisper (ahorra tiempo si no hay GPU)")
    args = parser.parse_args()

    print("🚀 Iniciando Benchmark Voice2Machine")
    print(f"   Configuración: {args.iterations} iters/prueba")
    print()

    results = []

    # 1. Cold Start
    print("1️⃣  Midiendo Cold Start...")
    results.append(benchmark_cold_start())

    # 2. Audio Buffer
    print("2️⃣  Midiendo Manipulación de Audio...")
    results.append(benchmark_audio_buffer(iterations=args.iterations))

    # 3. Whisper
    if not args.skip_whisper:
        print("3️⃣  Midiendo Inferencia Whisper...")
        results.append(benchmark_whisper(iterations=min(args.iterations, 5)))

    # Reporte final
    print_results(results)


if __name__ == "__main__":
    main()
