
"""
Script worker para grabación de audio en proceso independiente.

Este script se utiliza para ejecutar la grabación de audio en un proceso
separado, aislando la captura de audio del proceso principal de la aplicación.
Esto ayuda a evitar problemas de bloqueo por el Global Interpreter Lock (GIL)
y mejora la estabilidad general del sistema.
"""

import argparse
import signal
import sys
import time
from pathlib import Path

# Añadir src a la ruta para permitir importaciones
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from v2m.infrastructure.audio.recorder import AudioRecorder

# Configurar el manejo de señales
stop_requested = False


def signal_handler(sig, frame):
    """
    Manejador de señales para detener la grabación limpiamente.
    """
    global stop_requested
    stop_requested = True


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def main():
    """
    Punto de entrada para el worker de grabación independiente.

    Este script se ejecuta como un proceso separado para aislar la grabación de audio
    del proceso principal.
    """
    parser = argparse.ArgumentParser(description="Worker de Grabación de Audio V2M")
    parser.add_argument("--output", type=str, required=True, help="Ruta del archivo de salida")
    args = parser.parse_args()

    recorder = AudioRecorder()
    try:
        recorder.start()
        print("grabación iniciada", flush=True)
    except Exception as e:
        print(f"error al iniciar la grabación: {e}", file=sys.stderr)
        sys.exit(1)

    while not stop_requested:
        time.sleep(0.1)

    print("deteniendo la grabación...", flush=True)
    # Optimización: return_data=False evita copia innecesaria del buffer de memoria
    # a la memoria del proceso Python, ya que solo necesitamos guardar a disco.
    recorder.stop(save_path=Path(args.output), return_data=False)
    print(f"guardado en {args.output}", flush=True)


if __name__ == "__main__":
    main()
