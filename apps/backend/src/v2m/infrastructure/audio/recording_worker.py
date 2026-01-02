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
script worker para grabación de audio en proceso independiente

este script se utiliza para ejecutar la grabación de audio en un proceso
separado aislando la captura de audio del proceso principal de la aplicación
esto ayuda a evitar problemas de bloqueo por el gil y mejora la estabilidad
"""

import argparse
import signal
import sys
import time
from pathlib import Path

# añadir src a la ruta para permitir importaciones
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from v2m.infrastructure.audio.recorder import AudioRecorder

# configurar el manejo de señales
stop_requested = False

def signal_handler(sig, frame):
    """
    manejador de señales para detener la grabación limpiamente
    """
    global stop_requested
    stop_requested = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    """
    punto de entrada para el worker de grabación independiente

    este script se ejecuta como un proceso separado para aislar la grabación de audio
    del proceso principal evitando bloqueos y problemas de gil
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, required=True, help="Ruta del archivo de salida")
    args = parser.parse_args()

    recorder = AudioRecorder()
    try:
        recorder.start()
        print("grabación iniciada", flush=True)
    except Exception as e:
        print(f"error al iniciar la grabación {e}", file=sys.stderr)
        sys.exit(1)

    while not stop_requested:
        time.sleep(0.1)

    print("deteniendo la grabación...", flush=True)
    # optimización: return_data=False evita copia innecesaria del buffer
    recorder.stop(save_path=Path(args.output), return_data=False)
    print(f"guardado en {args.output}", flush=True)

if __name__ == "__main__":
    main()
