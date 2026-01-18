#!/usr/bin/env python3
"""
Script de verificación para el command TRANSCRIBE_FILE del backend.
Genera un archivo de audio de prueba y lo envía al demonio para transcripción.
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Agregar el directorio src al path para importar módulos de v2m si fuera necesario
# pero vamos a usar socket raw para minimizar dependencias de importación
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

SOCKET_PATH_ENV = os.environ.get("V2M_SOCKET_PATH")

def get_socket_path():
    if SOCKET_PATH_ENV:
        return SOCKET_PATH_ENV

    # Intentar descubrir como en lib.rs / ipc_protocol.py
    uid = os.getuid()
    xdg_runtime = os.environ.get("XDG_RUNTIME_DIR")
    if xdg_runtime:
        return Path(xdg_runtime) / "v2m/v2m.sock"
    return Path(f"/tmp/v2m_{uid}/v2m.sock")

async def send_command(cmd, data=None):
    socket_path = get_socket_path()
    if not os.path.exists(socket_path):
        print(f"Error: Socket no encontrado en {socket_path}")
        return None

    try:
        reader, writer = await asyncio.open_unix_connection(str(socket_path))

        payload = {"cmd": cmd, "data": data}
        msg = json.dumps(payload).encode("utf-8")

        # Header 4 bytes length
        writer.write(len(msg).to_bytes(4, byteorder="big"))
        writer.write(msg)
        await writer.drain()

        # Read response
        header = await reader.readexactly(4)
        resp_len = int.from_bytes(header, byteorder="big")
        resp_data = await reader.readexactly(resp_len)

        response = json.loads(resp_data.decode("utf-8"))
        writer.close()
        await writer.wait_closed()
        return response

    except Exception as e:
        print(f"Error IPC: {e}")
        return None

def create_test_audio(path):
    # Generar un tono de 1kHZ de 2 segundos
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=1000:duration=2",
        "-ar", "16000",
        "-ac", "1",
        str(path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    print(f"Archivo de prueba creado: {path}")

async def main():
    print("=== Verificación de Export Backend ===")

    # 1. Verificar socket
    sock = get_socket_path()
    print(f"Socket: {sock}")
    if not os.path.exists(sock):
        print("❌ Daemon no está corriendo. Inicia 'python -m v2m.daemon' primero.")
        sys.exit(1)

    # 2. Ping
    resp = await send_command("PING")
    if resp and resp.get("status") == "success":
        print("✅ PING exitoso")
    else:
        print(f"❌ Fallo PING: {resp}")
        sys.exit(1)

    # 3. Test Audio File
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        create_test_audio(tmp_path)

        print(f"Enviando comando TRANSCRIBE_FILE con {tmp_path}...")
        # Esperamos que Whisper procese. Puede tardar un poco si no está cargado.
        resp = await send_command("TRANSCRIBE_FILE", {"file_path": str(tmp_path)})

        if resp and resp.get("status") == "success":
            print("✅ Transcripción exitosa (Status OK)")
            print(f"Resultado: {resp.get('data')}")
        else:
            print(f"❌ Fallo Transcripción: {resp}")
            sys.exit(1)

    finally:
        if tmp_path.exists():
            os.unlink(tmp_path)

if __name__ == "__main__":
    asyncio.run(main())
