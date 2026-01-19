
"""
Protocolo de Comunicación Inter-Procesos (IPC) para Voice2Machine.

Este módulo define el protocolo de comunicación entre el cliente y el demonio
utilizando un socket Unix para una comunicación local eficiente y segura.

Protocolo V2.0 (JSON):
    La comunicación es síncrona tipo Request-Response utilizando mensajes
    JSON estructurados para prevenir inyección de comandos.

    1. El cliente abre una conexión al socket Unix.
    2. Envía un `IPCRequest` serializado en JSON (con framing).
    3. El demonio procesa el comando.
    4. El demonio responde con un `IPCResponse` en JSON (con framing).
    5. La conexión se cierra.

Estructura de Mensajes:
    - Request: `{"cmd": "COMMAND", "data": {...}}`
    - Response: `{"status": "success|error", "data": {...}, "error": "..."}`
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

# SOTA 2026: orjson is 3-10x faster than stdlib json
try:
    import orjson

    _USE_ORJSON = True
except ImportError:
    import json

    _USE_ORJSON = False

# Límite de payload para prevenir ataques de Denegación de Servicio (DoS)
# por agotamiento de memoria. 1MB es suficiente para texto largo.
MAX_PAYLOAD_SIZE = 1024 * 1024  # 1MB


class IPCCommand(str, Enum):
    """
    Enumeración de los comandos IPC disponibles.

    Define los comandos que pueden ser enviados desde el cliente al demonio
    para controlar su comportamiento. Hereda de `str` para permitir
    comparación directa y serialización JSON.

    Atributos:
        START_RECORDING: Inicia la captura de audio.
        STOP_RECORDING: Detiene la grabación y transcribe.
        PROCESS_TEXT: Procesa texto con el LLM (refinamiento).
        TRANSLATE_TEXT: Traduce texto usando el LLM.
        PING: Verificación de latido (Heartbeat).
        SHUTDOWN: Apagado ordenado del demonio.
        GET_STATUS: Solicita estado y telemetría actual.
        UPDATE_CONFIG: Actualiza la configuración en caliente.
        GET_CONFIG: Solicita la configuración actual.
        PAUSE_DAEMON: Pausa el procesamiento (no graba ni transcribe).
        RESUME_DAEMON: Reanuda el procesamiento normal.
    """

    START_RECORDING = "START_RECORDING"
    STOP_RECORDING = "STOP_RECORDING"
    PROCESS_TEXT = "PROCESS_TEXT"
    TRANSLATE_TEXT = "TRANSLATE_TEXT"
    PING = "PING"
    SHUTDOWN = "SHUTDOWN"
    GET_STATUS = "GET_STATUS"
    UPDATE_CONFIG = "UPDATE_CONFIG"
    GET_CONFIG = "GET_CONFIG"
    PAUSE_DAEMON = "PAUSE_DAEMON"
    RESUME_DAEMON = "RESUME_DAEMON"
    TRANSCRIBE_FILE = "TRANSCRIBE_FILE"
    TOGGLE_RECORDING = "TOGGLE_RECORDING"


# =============================================================================
# PROTOCOLO JSON SEGURO (v2.0)
# =============================================================================


@dataclass(slots=True)
class IPCRequest:
    """
    Mensaje de Solicitud (Request) del Cliente al Demonio (JSON).

    Encapsula el comando y sus datos en un objeto estructurado,
    eliminando vulnerabilidades de inyección de comandos y facilitando
    el tipado fuerte.

    Atributos:
        cmd: Nombre del comando (ej: "PROCESS_TEXT").
        data: Diccionario opcional con parámetros del comando.

    Ejemplo:
        ```python
        req = IPCRequest(cmd="PROCESS_TEXT", data={"text": "hola"})
        json_str = req.to_json()
        # '{"cmd": "PROCESS_TEXT", "data": {"text": "hola"}}'
        ```
    """

    cmd: str
    data: dict[str, Any] | None = None

    def to_json(self) -> str:
        """Serializa el request a cadena JSON."""
        payload = {"cmd": self.cmd, "data": self.data}
        if _USE_ORJSON:
            return orjson.dumps(payload).decode("utf-8")
        return json.dumps(payload, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "IPCRequest":
        """
        Deserializa una cadena JSON a un objeto IPCRequest.

        Raises:
            json.JSONDecodeError: Si el JSON es inválido.
            KeyError: Si falta el campo obligatorio 'cmd'.
        """
        obj = orjson.loads(json_str) if _USE_ORJSON else json.loads(json_str)
        return cls(cmd=obj["cmd"], data=obj.get("data"))


@dataclass(slots=True)
class IPCResponse:
    """
    Mensaje de Respuesta (Response) del Demonio al Cliente (JSON).

    Proporciona respuestas estructuradas con estado explícito,
    eliminando el parsing frágil basado en cadenas de texto.

    Atributos:
        status: "success" o "error".
        data: Payload de datos en caso de éxito (opcional).
        error: Mensaje descriptivo en caso de fallo (opcional).

    Ejemplo:
        ```python
        resp = IPCResponse(status="error", error="no se detectó voz")
        # '{"status": "error", "data": null, "error": "no se detectó voz"}'
        ```
    """

    status: str  # "success" | "error"
    data: dict[str, Any] | None = None
    error: str | None = None

    def to_json(self) -> str:
        """Serializa el response a cadena JSON."""
        payload = {"status": self.status, "data": self.data, "error": self.error}
        if _USE_ORJSON:
            return orjson.dumps(payload).decode("utf-8")
        return json.dumps(payload, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "IPCResponse":
        """Deserializa una cadena JSON a un objeto IPCResponse."""
        obj = orjson.loads(json_str) if _USE_ORJSON else json.loads(json_str)
        return cls(status=obj["status"], data=obj.get("data"), error=obj.get("error"))


def get_socket_path() -> str:
    """
    Retorna la ruta del socket usando XDG_RUNTIME_DIR si está disponible.

    Garantiza que el socket se cree en un directorio seguro y temporal
    propiedad del usuario, siguiendo los estándares de freedesktop.org.
    """
    from v2m.utils.paths import get_secure_runtime_dir

    return str(get_secure_runtime_dir() / "v2m.sock")


# Ruta del socket (Evaluada al importar el módulo)
SOCKET_PATH = get_socket_path()

HEADER_SIZE = 4


async def send_ipc_message(writer, message: IPCResponse) -> None:
    """Helper para enviar mensaje IPC con framing."""
    resp_bytes = message.to_json().encode("utf-8")
    resp_len = len(resp_bytes)
    writer.write(resp_len.to_bytes(HEADER_SIZE, byteorder="big") + resp_bytes)
    await writer.drain()
