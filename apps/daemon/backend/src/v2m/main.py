
"""
Punto de Entrada Principal para Voice2Machine.

Este módulo actúa como un lanzador unificado que puede operar en dos modos:

1. **Modo Demonio** (`--daemon`): Inicia el proceso persistente en segundo plano.
2. **Modo Cliente** (`<COMANDO>`): Envía comandos IPC al demonio en ejecución.

Ejemplos:
    Iniciar el demonio:
        python -m v2m.main --daemon

    Enviar comandos:
        python -m v2m.main START_RECORDING
        python -m v2m.main STOP_RECORDING
"""

import argparse
import asyncio
import sys

from v2m.client import send_command
from v2m.core.ipc_protocol import IPCCommand
from v2m.core.logging import logger
from v2m.utils.env import configure_gpu_environment


def _setup_uvloop() -> None:
    """
    Configura uvloop como el bucle de eventos si está disponible.
    Optimiza el rendimiento de I/O asíncrono en sistemas *nix.
    """
    try:
        import uvloop

        uvloop.install()
        logger.debug("uvloop habilitado")
    except ImportError:
        pass


def main() -> None:
    """
    Función principal que procesa argumentos y ejecuta el modo apropiado.
    """
    parser = argparse.ArgumentParser(description="Punto de Entrada Principal de Voice2Machine")

    parser.add_argument("--daemon", action="store_true", help="Iniciar el proceso demonio en primer plano")
    parser.add_argument("command", nargs="?", choices=[e.value for e in IPCCommand], help="Comando IPC a enviar")
    parser.add_argument("payload", nargs="*", help="Carga útil opcional para el comando")

    args = parser.parse_args()

    if args.daemon:
        _setup_uvloop()
        configure_gpu_environment()

        from v2m.daemon import Daemon

        logger.info("iniciando demonio voice2machine...")
        daemon = Daemon()
        daemon.run()
    elif args.command:
        # Modo Cliente
        try:
            full_command = args.command
            if args.payload:
                full_command += " " + " ".join(args.payload)

            response = asyncio.run(send_command(full_command))
            print(response)
        except Exception as e:
            print(f"error enviando comando: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
