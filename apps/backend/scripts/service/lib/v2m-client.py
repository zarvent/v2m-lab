#!/usr/bin/env python3
"""
v2m-client.py - Ultra-Fast IPC Client for V2M Daemon
SOTA 2026: Single-purpose, zero-dependency, sub-10ms latency

Usage:
    v2m-client.py toggle          # Toggle recording state
    v2m-client.py status          # Get daemon status
    v2m-client.py <json_command>  # Send raw JSON command
"""
import json
import os
import socket
import struct
import sys
from pathlib import Path

# Protocol constants
HEADER_SIZE = 4
TIMEOUT_SEC = 10
MAX_RESPONSE = 65536


def get_socket_path() -> str:
    """Resolve v2m socket path using XDG spec."""
    xdg = os.environ.get("XDG_RUNTIME_DIR")
    if xdg:
        return f"{xdg}/v2m/v2m.sock"
    return f"/tmp/v2m_{os.getuid()}/v2m.sock"


def send_command(cmd: str, data: dict | None = None) -> dict:
    """
    Send command to v2m daemon and return parsed response.

    Protocol: [4-byte big-endian length][UTF-8 JSON payload]
    """
    payload = json.dumps({"cmd": cmd, "data": data or {}}).encode("utf-8")
    sock_path = get_socket_path()

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT_SEC)

    try:
        sock.connect(sock_path)

        # Send: header + payload
        sock.sendall(struct.pack(">I", len(payload)) + payload)

        # Receive: header
        header = sock.recv(HEADER_SIZE)
        if len(header) < HEADER_SIZE:
            return {"status": "error", "error": "Incomplete response header"}

        # Receive: body
        body_len = struct.unpack(">I", header)[0]
        if body_len > MAX_RESPONSE:
            return {"status": "error", "error": f"Response too large: {body_len}"}

        body = sock.recv(body_len)
        return json.loads(body.decode("utf-8"))

    except FileNotFoundError:
        return {"status": "error", "error": "daemon_not_running"}
    except ConnectionRefusedError:
        return {"status": "error", "error": "daemon_not_responding"}
    except socket.timeout:
        return {"status": "error", "error": "timeout"}
    except json.JSONDecodeError as e:
        return {"status": "error", "error": f"Invalid JSON: {e}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        sock.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: v2m-client.py <command> [data_json]", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1].upper()

    # Shorthand commands
    shortcuts = {
        "TOGGLE": "TOGGLE_RECORDING",
        "START": "START_RECORDING",
        "STOP": "STOP_RECORDING",
        "STATUS": "GET_STATUS",
        "PING": "PING",
    }
    cmd = shortcuts.get(cmd, cmd)

    # Optional data argument
    data = None
    if len(sys.argv) > 2:
        try:
            data = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            print(f"Invalid JSON data: {sys.argv[2]}", file=sys.stderr)
            sys.exit(1)

    result = send_command(cmd, data)
    print(json.dumps(result, ensure_ascii=False))

    # Exit code based on status
    if result.get("status") == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
