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
PUNTO DE ENTRADA PRINCIPAL PARA LA APLICACIÓN VOICE2MACHINE

este módulo actúa como un lanzador unificado que puede operar en dos modos

    1 **modo daemon** (``--daemon``) inicia el proceso persistente que
       mantiene el modelo whisper en memoria y escucha comandos ipc

    2 **modo cliente** (``<COMMAND>``) envía comandos al daemon en
       ejecución a través de socket unix

EJEMPLOS DE USO
    iniciar el daemon proceso en primer plano::

        python -m v2m.main --daemon

    enviar comandos al daemon::

        python -m v2m.main START_RECORDING
        python -m v2m.main STOP_RECORDING
        python -m v2m.main PING
        python -m v2m.main SHUTDOWN

    procesar texto con llm::

        python -m v2m.main PROCESS_TEXT "texto a refinar"

NOTE
    para uso en producción se recomienda ejecutar el daemon como servicio
    systemd ver ``scripts/install_service.py`` para más detalles
"""
import argparse
import asyncio
import sys

from v2m.client import send_command
from v2m.core.ipc_protocol import IPCCommand
from v2m.core.logging import logger


def _setup_uvloop() -> None:
    """
    CONFIGURA UVLOOP COMO EVENT LOOP SI ESTÁ DISPONIBLE

    uvloop es 2-4x más rápido que el asyncio loop estándar
    si no está instalado usa el loop estándar sin error
    """
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        logger.debug("uvloop habilitado para mejor rendimiento")
    except ImportError:
        pass  # uvloop no instalado usar loop estándar


def main() -> None:
    """
    FUNCIÓN PRINCIPAL QUE PROCESA ARGUMENTOS Y EJECUTA EL MODO APROPIADO

    analiza los argumentos de línea de comandos para determinar si debe
    iniciar el servicio en segundo plano daemon o actuar como cliente
    enviando comandos ipc

    ARGUMENTOS CLI
        --daemon: si está presente inicia el daemon en primer plano
            el proceso no se bifurca no fork permitiendo ver logs
            directamente para ejecutar en segundo plano usar nohup
            o un gestor de servicios como systemd

        command: comando ipc a enviar si no se usa --daemon
            valores válidos ``START_RECORDING`` ``STOP_RECORDING``
            ``PING`` ``SHUTDOWN`` ``PROCESS_TEXT``

        payload: argumentos adicionales para el comando opcional
            solo aplicable a comandos que requieren datos adicionales
            como ``PROCESS_TEXT``

    RETURNS:
        none en modo daemon nunca retorna ejecuta indefinidamente
        en modo cliente termina después de enviar el comando

    RAISES:
        SystemExit: con código 1 si no se proporcionan argumentos o
            si hay un error de comunicación con el daemon

    EXAMPLE
        desde python::

            from v2m.main import main
            import sys

            sys.argv = ['v2m', '--daemon']
            main()  # inicia daemon
    """
    parser = argparse.ArgumentParser(description="punto de entrada principal de voice2machine")

    # argumento para iniciar como demonio
    parser.add_argument("--daemon", action="store_true", help="inicia el proceso del daemon en segundo plano")

    # argumento para enviar comandos modo cliente
    parser.add_argument("command", nargs="?", choices=[e.value for e in IPCCommand], help="comando ipc para enviar")
    parser.add_argument("payload", nargs="*", help="carga útil opcional para el comando")

    args = parser.parse_args()

    if args.daemon:
        # habilitar uvloop para el daemon mejora rendimiento ipc
        _setup_uvloop()

        from v2m.daemon import Daemon
        logger.info("iniciando daemon de voice2machine...")
        daemon = Daemon()
        daemon.run()
    elif args.command:
        # modo cliente
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
