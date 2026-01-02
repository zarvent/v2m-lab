import time
import asyncio
import subprocess
import sys
from pathlib import Path
import numpy as np
import soundfile as sf
from whisper_dictation.client import send_command
from whisper_dictation.core.ipc_protocol import IPCCommand

# Configuration
TEST_AUDIO_DURATION = 5  # seconds
SAMPLE_RATE = 16000
DAEMON_SCRIPT = "src/whisper_dictation/daemon.py"
PYTHON = sys.executable

async def run_benchmark():
    print("=== End-to-End Latency Benchmark ===")

    # 1. Start Daemon
    print("Starting Daemon...")
    daemon_process = subprocess.Popen(
        [PYTHON, DAEMON_SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(10) # Wait for model load

    try:
        # 2. Warmup
        print("Warming up...")
        await send_command(IPCCommand.START_RECORDING)
        time.sleep(1)
        await send_command(IPCCommand.STOP_RECORDING)
        time.sleep(2)

        # 3. Benchmark Loop
        latencies = []
        iterations = 5

        print(f"Running {iterations} iterations...")
        for i in range(iterations):
            # Start Recording
            await send_command(IPCCommand.START_RECORDING)

            # Simulate speaking time (sleep)
            time.sleep(2)

            # Stop Recording & Measure Time
            start_time = time.time()
            await send_command(IPCCommand.STOP_RECORDING)
            end_time = time.time()

            # Note: This measures the time for the client to get "OK" from the daemon.
            # The daemon sends "OK" AFTER transcription is complete and copied to clipboard.
            # So this IS the end-to-end latency from user perspective.

            latency = (end_time - start_time) * 1000 # ms
            latencies.append(latency)
            print(f"Iteration {i+1}: {latency:.2f} ms")

            time.sleep(1) # Cooldown

        avg_latency = sum(latencies) / len(latencies)
        print(f"\nAverage Latency: {avg_latency:.2f} ms")
        print(f"Min Latency: {min(latencies):.2f} ms")
        print(f"Max Latency: {max(latencies):.2f} ms")

    finally:
        print("Shutting down...")
        await send_command(IPCCommand.SHUTDOWN)
        daemon_process.terminate()
        daemon_process.wait()

if __name__ == "__main__":
    asyncio.run(run_benchmark())
