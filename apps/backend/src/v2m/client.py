
"""
Cliente de Línea de Comandos para Comunicarse con el Demonio V2M.

Este módulo proporciona funcionalidades para enviar comandos al demonio
de Voice2Machine a través de un socket Unix. Es la interfaz principal para
interactuar con el servicio desde scripts externos, terminales o interfaces de usuario.

Protocolo V2.0 (JSON):
    Request:  {"cmd": "COMMAND", "data": {...}}
    Response: {"status": "success|error", "data": {...}, "error": "..."}

Ejemplos:
    Uso desde línea de comandos:
        python -m v2m.client START_RECORDING
        python -m v2m.client STOP_RECORDING
        python -m v2m.client PING
        python -m v2m.client PROCESS_TEXT "texto a refinar"

    Uso programático:
        ```python
        import asyncio
        from v2m.client import send_command

        response = asyncio.run(send_command("PING"))
        print(response)
        ```
"""

import argparse
import asyncio
import sys

from v2m.core.ipc_protocol import SOCKET_PATH, IPCCommand, IPCRequest, IPCResponse


async def send_command(cmd: str, data: dict | None = None) -> IPCResponse:
    """
    Envía un comando al demonio a través de un socket Unix (Protocolo JSON V2.0).

    Establece una conexión asíncrona con el socket del demonio, envía el
    comando como JSON estructurado y espera una respuesta JSON.
    Maneja el protocolo de encuadre (framing) de 4 bytes para asegurar la integridad del mensaje.

    Args:
        cmd: Nombre del comando (ej. "START_RECORDING", "PROCESS_TEXT").
        data: Carga útil opcional con datos del comando.

    Returns:
        IPCResponse: Objeto con estado, datos y/o error.

    Raises:
        SystemExit: Si el demonio no está corriendo (FileNotFoundError)
            o rechaza la conexión (ConnectionRefusedError).
    """
    try:
        reader, writer = await asyncio.open_unix_connection(SOCKET_PATH)

        # Construir request JSON
        request = IPCRequest(cmd=cmd, data=data)
        message_bytes = request.to_json().encode("utf-8")

        # Protocolo de framing: 4 bytes longitud (big endian) + payload
        length = len(message_bytes)
        writer.write(length.to_bytes(4, byteorder="big"))
        writer.write(message_bytes)
        await writer.drain()

        # Leer header: 4 bytes (big endian int32)
        # Previene lectura de basura o falta de sincronización
        header = await reader.readexactly(4)
        response_length = int.from_bytes(header, byteorder="big")

        # Leer payload exacto según longitud indicada en header
        response_data = await reader.readexactly(response_length)
        response_json = response_data.decode("utf-8")

        writer.close()
        await writer.wait_closed()

        return IPCResponse.from_json(response_json)

    except FileNotFoundError:
        print("error: el demonio no está corriendo. inícialo con 'python -m v2m.daemon'", file=sys.stderr)
        sys.exit(1)
    except ConnectionRefusedError:
        print("error: conexión rechazada. el demonio podría estar inactivo", file=sys.stderr)
        sys.exit(1)
    except asyncio.IncompleteReadError:
        print("error: conexión interrumpida. respuesta incompleta del demonio", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """
    Punto de Entrada para el Cliente de Línea de Comandos.

    Analiza los argumentos de la línea de comandos, construye el mensaje
    JSON estructurado y lo envía al demonio. Imprime la respuesta procesada.
    """
    parser = argparse.ArgumentParser(description="Cliente de Dictado Voice2Machine (Protocolo JSON V2.0)")
    parser.add_argument("command", choices=[e.value for e in IPCCommand], help="Comando IPC a enviar al demonio")
    parser.add_argument("payload", nargs="*", help="Texto opcional para comandos como PROCESS_TEXT")

    args = parser.parse_args()

    # Construir data según el comando
    data = None
    if args.command == IPCCommand.PROCESS_TEXT and args.payload:
        data = {"text": " ".join(args.payload)}

    response = asyncio.run(send_command(args.command, data))

    # Output legible para el usuario
    if response.status == "success":
        if response.data:
            # Mostrar el valor más relevante según el contexto
            if "transcription" in response.data:
                print(response.data["transcription"])
            elif "refined_text" in response.data:
                print(response.data["refined_text"])
            elif "state" in response.data:
                print(f"ESTADO: {response.data['state']}")
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
