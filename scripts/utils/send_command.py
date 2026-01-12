#!/usr/bin/env python3
"""
Standalone IPC client for voice2machine.
Designed to minimize startup latency for keyboard shortcuts.
"""

import sys
import socket
import json
import os
import struct

def get_socket_path():
    """Discover socket path using XDG standard or default fallback."""
    # 1. Check environment variable
    if "V2M_SOCKET_PATH" in os.environ:
        return os.environ["V2M_SOCKET_PATH"]

    # 2. Check XDG_RUNTIME_DIR (always prefer, same logic as daemon)
    xdg_runtime = os.environ.get("XDG_RUNTIME_DIR")
    if xdg_runtime:
        return os.path.join(xdg_runtime, "v2m", "v2m.sock")

    # 3. Fallback to /tmp
    uid = os.getuid()
    path = f"/tmp/v2m_{uid}/v2m.sock"
    return path

def send_command(cmd, payload=None):
    socket_path = get_socket_path()

    if not os.path.exists(socket_path):
        # Print error in JSON format so caller can parse it if needed, or just stderr
        print(f"Error: Socket not found at {socket_path}", file=sys.stderr)
        sys.exit(1)

    try:
        # Create socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(socket_path)

        # Prepare request
        request = {"cmd": cmd, "data": payload}
        msg_bytes = json.dumps(request).encode("utf-8")

        # Send (4-byte length prefix + payload)
        sock.sendall(struct.pack(">I", len(msg_bytes)))
        sock.sendall(msg_bytes)

        # Receive header (4-byte length)
        header = sock.recv(4)
        if not header:
            print("Error: Incomplete response (no header)", file=sys.stderr)
            sys.exit(1)

        resp_len = struct.unpack(">I", header)[0]

        # Receive body
        resp_data = b""
        while len(resp_data) < resp_len:
            chunk = sock.recv(resp_len - len(resp_data))
            if not chunk:
                break
            resp_data += chunk

        sock.close()

        # Print raw JSON response for the shell script to parse
        print(resp_data.decode("utf-8"))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: send_command.py <COMMAND> [PAYLOAD_JSON]", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    payload = None
    if len(sys.argv) > 2:
        try:
            payload = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            # If not JSON, treat as raw text for convenience (e.g. PROCESS_TEXT "some text")
            payload = {"text": " ".join(sys.argv[2:])}

    send_command(cmd, payload)
