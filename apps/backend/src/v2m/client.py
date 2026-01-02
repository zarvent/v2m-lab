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
CLIENTE DE LÍNEA DE COMANDOS PARA COMUNICARSE CON EL DAEMON DE V2M

este módulo proporciona funcionalidades para enviar comandos al daemon
de voice2machine a través de un socket unix es la forma principal de
interactuar con el servicio desde scripts externos o la terminal

PROTOCOLO V2.0 (JSON)
    request:  {"cmd": "COMMAND", "data": {...}}
    response: {"status": "success|error", "data": {...}, "error": "..."}

EJEMPLO
    uso desde línea de comandos::

        python -m v2m.client START_RECORDING
        python -m v2m.client STOP_RECORDING
        python -m v2m.client PING
        python -m v2m.client PROCESS_TEXT "texto a refinar"

    uso programático::

        import asyncio
        from v2m.client import send_command

        response = asyncio.run(send_command("PING"))
        print(response)  # IPCResponse(status='success', data={'message': 'PONG'})

NOTE
    el daemon debe estar ejecutándose antes de enviar comandos
    iniciar con ``python -m v2m.main --daemon``
"""

import argparse
import asyncio
import sys

from v2m.core.ipc_protocol import SOCKET_PATH, IPCCommand, IPCRequest, IPCResponse


async def send_command(cmd: str, data: dict = None) -> IPCResponse:
    """
    ENVÍA UN COMANDO AL DAEMON A TRAVÉS DE UN SOCKET UNIX (PROTOCOLO JSON V2.0)

    establece una conexión asíncrona con el socket del daemon envía el
    comando como JSON estructurado y espera una respuesta JSON

    ARGS:
        cmd: nombre del comando (ej "START_RECORDING", "PROCESS_TEXT")
        data: payload opcional con datos del comando

    RETURNS:
        IPCResponse con status, data y/o error

    RAISES:
        SystemExit: si el daemon no está corriendo filenotfounderror
            o rechaza la conexión connectionrefusederror

    EXAMPLE:
        verificar si el daemon está activo::

            response = await send_command("PING")
            if response.status == "success":
                print("daemon activo")

        procesar texto::

            response = await send_command("PROCESS_TEXT", {"text": "hola mundo"})
            if response.status == "success":
                print(response.data["refined_text"])
    """
    try:
        reader, writer = await asyncio.open_unix_connection(SOCKET_PATH)

        # construir request JSON
        request = IPCRequest(cmd=cmd, data=data)
        message_bytes = request.to_json().encode("utf-8")

        # protocolo de framing 4 bytes longitud big endian + payload
        length = len(message_bytes)
        writer.write(length.to_bytes(4, byteorder="big"))
        writer.write(message_bytes)
        await writer.drain()

        # leer header 4 bytes (big endian int32)
        # esto previene que leamos basura o que falte el header
        header = await reader.readexactly(4)
        response_length = int.from_bytes(header, byteorder="big")

        # leer payload exacto según longitud indicada en header
        # esto evita truncamiento de mensajes largos o lectura excesiva
        response_data = await reader.readexactly(response_length)
        response_json = response_data.decode("utf-8")

        writer.close()
        await writer.wait_closed()

        return IPCResponse.from_json(response_json)

    except FileNotFoundError:
        print("error el daemon no está corriendo inícialo con 'python -m v2m.daemon'", file=sys.stderr)
        sys.exit(1)
    except ConnectionRefusedError:
        print("error conexión rechazada el daemon podría estar muerto", file=sys.stderr)
        sys.exit(1)
    except asyncio.IncompleteReadError:
        print("error conexión interrumpida respuesta incompleta del daemon", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """
    PUNTO DE ENTRADA PARA EL CLIENTE DE LÍNEA DE COMANDOS

    analiza los argumentos de la línea de comandos construye el mensaje
    JSON estructurado y lo envía al daemon imprime la respuesta como JSON

    ARGUMENTOS CLI
        command: comando ipc a enviar requerido opciones
            ``START_RECORDING`` ``STOP_RECORDING`` ``PING``
            ``SHUTDOWN`` ``PROCESS_TEXT`` ``GET_STATUS``
        payload: texto opcional para PROCESS_TEXT

    EXAMPLE
        iniciar grabación::

            python -m v2m.client START_RECORDING

        procesar texto::

            python -m v2m.client PROCESS_TEXT "texto a refinar"

        ver estado::

            python -m v2m.client GET_STATUS
    """
    parser = argparse.ArgumentParser(description="cliente de dictado whisper (protocolo JSON v2.0)")
    parser.add_argument("command", choices=[e.value for e in IPCCommand], help="comando para enviar al daemon")
    parser.add_argument("payload", nargs="*", help="texto opcional para PROCESS_TEXT")

    args = parser.parse_args()

    # construir data según el comando
    data = None
    if args.command == IPCCommand.PROCESS_TEXT and args.payload:
        data = {"text": " ".join(args.payload)}

    response = asyncio.run(send_command(args.command, data))

    # output legible
    if response.status == "success":
        if response.data:
            # mostrar el valor más relevante
            if "transcription" in response.data:
                print(response.data["transcription"])
            elif "refined_text" in response.data:
                print(response.data["refined_text"])
            elif "state" in response.data:
                print(f"STATUS: {response.data['state']}")
            elif "message" in response.data:
                print(response.data["message"])
            else:
                print(response.to_json())
        else:
            print("OK")
    else:
        print(f"ERROR: {response.error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
