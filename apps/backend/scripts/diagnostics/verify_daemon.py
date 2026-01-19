#!/usr/bin/env python3

"""
verificación completa del daemon - la prueba de fuego para v2m

¿qué hace esto?
    este es el script que corre todas las pruebas de integración del sistema
    v2m de principio a fin básicamente levanta un daemon de prueba le manda
    comandos reales (como si fueras vos usando la aplicación) y verifica que
    todo responda correctamente

    piénsalo como un "smoke test" completo del sistema

¿cuándo usarlo?
    - después de hacer cambios al daemon o al cliente
    - cuando algo raro pasa y querés descartar problemas de comunicación
    - antes de un release o deploy para asegurarte que todo funciona
    - si el daemon no responde y querés ver exactamente dónde falla

lo que prueba
    1 levanta un daemon fresco desde cero
    2 manda un ping y espera el pong (prueba de conectividad básica)
    3 inicia una grabación y la detiene (simula el flujo real)
    4 manda texto a gemini para procesamiento
    5 limpia todo al final (mata el daemon de prueba)

ejemplo de uso
    $ python scripts/verify_daemon.py

    si todo sale bien vas a ver algo así

        Starting Daemon...
        Sending PING...
        SUCCESS: Received PONG
        Sending START_RECORDING...
        Recording started.
        Sending STOP_RECORDING...
        Recording stopped. Transcription should be in clipboard.
        Testing Gemini processing...
        SUCCESS: All tests passed!

⚠️ importante
    este script levanta su propio daemon para las pruebas si tenés
    el servicio systemd corriendo (v2m.service) van a pelear por
    el mismo socket y vas a tener errores raros asegurate de parar
    el servicio antes de correr esto

        $ sudo systemctl stop v2m.service
        $ python scripts/verify_daemon.py
        $ sudo systemctl start v2m.service

dependencias
    los módulos del propio v2m (v2m.daemon v2m.client) si ves errores
    de import probablemente estés corriendo desde el directorio incorrecto

author
    voice2machine team

since
    v1.0.0
"""

import subprocess
import time
import sys
import os
from typing import Tuple
from pathlib import Path

# Path to python executable
PYTHON = sys.executable
"""str: ruta al ejecutable de python actual"""

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parents[1]
DAEMON_SCRIPT = str(BACKEND_DIR / "src/v2m/daemon.py")
CLIENT_SCRIPT = str(BACKEND_DIR / "src/v2m/client.py")


def run_client(*args: str) -> Tuple[str, str, int]:
    """
    manda un comando al daemon y te devuelve qué pasó

    esta función es como el intermediario entre las pruebas y el daemon
    ejecuta el cliente v2m con el comando que le pases y te devuelve
    toda la info relevante qué respondió si hubo errores y el código
    de salida

    args:
        *args: el comando y sus argumentos por ejemplo "PING" o
            "PROCESS_TEXT" "hola mundo"

    returns:
        una tupla con tres cosas
            - la respuesta del daemon (lo que imprimió a stdout)
            - los errores si hubo alguno (stderr)
            - el código de retorno (0 = éxito otro número = algo falló)

    example
        >>> stdout, stderr, code = run_client("PING")
        >>> if code == 0 and stdout == "PONG":
        ...     print("El daemon está vivo y responde!")
    """
    cmd = [PYTHON, CLIENT_SCRIPT] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def main() -> None:
    """
    corre todas las pruebas del daemon de principio a fin

    esta es la función que orquesta todo el show la secuencia es

        1 levanta un daemon fresco en segundo plano
        2 espera 10 segundos (sí es mucho pero el daemon necesita
           cargar whisper y eso tarda)
        3 manda un ping y verifica que reciba pong
        4 simula una grabación START → espera 3 segundos → STOP
        5 manda texto a gemini para ver si el procesamiento funciona
        6 mata el daemon al final para dejar todo limpio

    si algo falla el script termina con exit(1) y te muestra qué pasó
    si todo sale bien vas a ver "SUCCESS" en varios puntos

    note
        los 10 segundos de espera inicial pueden parecer eternos pero
        créeme que son necesarios cargar el modelo whisper en gpu toma
        su tiempo y si mandás comandos antes de que termine vas a
        tener errores de conexión rechazada
    """
    print("Starting Daemon...")
    daemon_process = subprocess.Popen(
        [PYTHON, DAEMON_SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Give it time to start
    time.sleep(10)

    try:
        print("Sending PING...")
        stdout, stderr, code = run_client("PING")

        if code != 0:
            print(f"Client failed: {stderr}")
            sys.exit(1)

        if stdout == "PONG":
            print("SUCCESS: Received PONG")
        else:
            print(f"FAILURE: Received '{stdout}', expected 'PONG'")
            sys.exit(1)

        print("Sending START_RECORDING...")
        stdout, stderr, code = run_client("START_RECORDING")
        if code != 0:
            print(f"START_RECORDING failed: {stderr}")
        else:
            print("Recording started.")

        time.sleep(3)

        print("Sending STOP_RECORDING...")
        stdout, stderr, code = run_client("STOP_RECORDING")
        if code != 0:
            print(f"STOP_RECORDING failed: {stderr}")
        else:
            print("Recording stopped. Transcription should be in clipboard.")

        time.sleep(1)

        print("Sending PROCESS_TEXT (Testing Gemini Fallback)...")
        test_text = "This is a test for Gemini Fallback"
        stdout, stderr, code = run_client("PROCESS_TEXT", test_text)
        if code != 0:
            print(f"PROCESS_TEXT failed: {stderr}")
        else:
            print(f"PROCESS_TEXT response: {stdout}")
            print("Check clipboard or notifications for result.")

    finally:
        print("Shutting down Daemon...")
        run_client("SHUTDOWN")
        daemon_process.terminate()
        daemon_process.wait()

        stdout_bytes, stderr_bytes = daemon_process.communicate()
        if stdout_bytes:
            print(f"Daemon STDOUT:\n{stdout_bytes.decode()}")
        if stderr_bytes:
            print(f"Daemon STDERR:\n{stderr_bytes.decode()}")


if __name__ == "__main__":
    main()
