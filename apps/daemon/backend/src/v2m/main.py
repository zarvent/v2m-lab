"""Punto de Entrada Principal para Voice2Machine (SOTA 2026).

Este módulo inicia el servidor FastAPI con Uvicorn, reemplazando el sistema
IPC manual basado en sockets Unix.

Modos de operación:
    1. **Servidor** (default): `python -m v2m.main` → Inicia FastAPI en localhost:8765
    2. **Cliente CLI**: `python -m v2m.main toggle` → Envía comando via HTTP

El servidor expone endpoints REST que cualquier Junior puede probar con curl:
    curl -X POST http://localhost:8765/toggle
    curl http://localhost:8765/status

Para desarrollo:
    uvicorn v2m.api.app:app --reload --host 127.0.0.1 --port 8765
"""

import argparse
import sys

from v2m.shared.logging import logger
from v2m.shared.utils.env import configure_gpu_environment

# Puerto por defecto para el servidor HTTP
DEFAULT_PORT = 8765
DEFAULT_HOST = "127.0.0.1"


def _setup_uvloop() -> None:
    """Configura uvloop como el bucle de eventos si está disponible.

    Optimiza el rendimiento de I/O asíncrono en sistemas *nix, proporcionando
    hasta 2-4x mejor throughput en operaciones de networking.

    Note:
        Solo tiene efecto en Linux/macOS. En Windows se ignora silenciosamente.
    """
    try:
        import uvloop

        uvloop.install()
        logger.debug("uvloop habilitado")
    except ImportError:
        pass


def _run_server(host: str, port: int) -> None:
    """Inicia el servidor FastAPI con Uvicorn.

    Args:
        host: Dirección IP o hostname para bind (ej. '127.0.0.1', '0.0.0.0').
        port: Puerto TCP para escuchar (ej. 8765).

    Note:
        El servidor se ejecuta en modo síncrono (blocking). Para desarrollo,
        use uvicorn directamente con --reload.
    """
    import uvicorn

    logger.info(f"🚀 Iniciando V2M Server en http://{host}:{port}")
    logger.info(f"📚 Documentación disponible en http://{host}:{port}/docs")

    uvicorn.run(
        "v2m.api.app:app",
        host=host,
        port=port,
        log_level="info",
        # Desactivar reload en producción - activar con --reload para desarrollo
    )


def _send_http_command(command: str, port: int) -> None:
    """Envía un comando HTTP al servidor V2M.

    Args:
        command: Nombre del comando (toggle, start, stop, status, health).
        port: Puerto donde el servidor está escuchando.

    Raises:
        SystemExit: Si el comando es desconocido o el servidor no responde.
    """
    import requests

    base_url = f"http://127.0.0.1:{port}"

    # Mapeo de comandos CLI a endpoints HTTP
    endpoint_map = {
        "toggle": ("POST", "/toggle"),
        "start": ("POST", "/start"),
        "stop": ("POST", "/stop"),
        "status": ("GET", "/status"),
        "health": ("GET", "/health"),
    }

    if command.lower() not in endpoint_map:
        print(f"Comando desconocido: {command}")
        print(f"Comandos disponibles: {', '.join(endpoint_map.keys())}")
        sys.exit(1)

    method, path = endpoint_map[command.lower()]
    url = f"{base_url}{path}"

    try:
        response = requests.post(url, timeout=30) if method == "POST" else requests.get(url, timeout=5)

        response.raise_for_status()
        print(response.json())

    except requests.ConnectionError:
        print(f"❌ No se pudo conectar al servidor en {base_url}")
        print("   Asegúrate de que el daemon esté corriendo: python -m v2m.main")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def main() -> None:
    """Función principal que procesa argumentos y ejecuta el modo apropiado.

    Determina si actuar como servidor (sin argumentos) o como cliente CLI
    (con comando). El modo servidor inicia FastAPI; el modo cliente envía
    requests HTTP al servidor existente.
    """
    parser = argparse.ArgumentParser(
        description="Voice2Machine - Transcripción de voz local con Whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python -m v2m.main              # Inicia el servidor
  python -m v2m.main toggle       # Inicia/detiene grabación
  python -m v2m.main status       # Muestra estado del daemon

  curl -X POST http://localhost:8765/toggle  # Alternativa con curl
        """,
    )

    parser.add_argument(
        "command",
        nargs="?",
        choices=["toggle", "start", "stop", "status", "health"],
        help="Comando a enviar al servidor (si está corriendo)",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host para el servidor (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Puerto para el servidor (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="(Deprecated) Alias para iniciar el servidor",
    )

    args = parser.parse_args()

    if args.command:
        # Modo Cliente: enviar comando HTTP
        _send_http_command(args.command, args.port)
    else:
        # Modo Servidor: iniciar FastAPI
        _setup_uvloop()
        configure_gpu_environment()
        _run_server(args.host, args.port)


if __name__ == "__main__":
    main()
