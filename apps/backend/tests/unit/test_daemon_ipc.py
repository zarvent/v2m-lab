import asyncio
import contextlib
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

from v2m.client import send_command
from v2m.daemon import Daemon


@pytest.fixture
def mock_daemon(monkeypatch, tmp_path):
    # Mock socket path in all modules that import it
    socket_path = tmp_path / "v2m.sock"
    monkeypatch.setattr("v2m.daemon.SOCKET_PATH", str(socket_path))
    monkeypatch.setattr("v2m.client.SOCKET_PATH", str(socket_path))
    monkeypatch.setattr("v2m.core.ipc_protocol.SOCKET_PATH", str(socket_path))

    # Mock container and command bus
    mock_bus = AsyncMock()
    mock_container = MagicMock()
    mock_container.get_command_bus.return_value = mock_bus

    # Mock ClientSessionManager with async methods (refactor Phase 3)
    mock_session_manager = AsyncMock()
    mock_session_manager.register = AsyncMock()
    mock_session_manager.unregister = AsyncMock()
    mock_container.client_session_manager = mock_session_manager

    # Patch dependencies in daemon.py
    monkeypatch.setattr("v2m.daemon.container", mock_container)

    # Patch cleaning methods to avoid side effects
    monkeypatch.setattr(Daemon, "_cleanup_orphaned_processes", lambda self: None)
    monkeypatch.setattr(Daemon, "_cleanup_resources", lambda self: None)

    # Patch sys.exit to avoid killing the test runner
    monkeypatch.setattr(sys, "exit", lambda code: None)

    # Create daemon instance
    daemon = Daemon()
    daemon.socket_path = socket_path  # Update instance socket path
    return daemon, mock_bus


@pytest.mark.asyncio
async def test_large_payload_truncation(mock_daemon):
    """
    Test that large payloads are correctly received with the fix.
    Uses JSON protocol v2.0 (IPCRequest format).
    """
    daemon, mock_bus = mock_daemon

    # Configure mock to return a result (so daemon sends valid JSON response)
    mock_bus.dispatch.return_value = "texto refinado de prueba"

    # Start server in background task
    server_task = asyncio.create_task(daemon.start_server())

    # Give server time to start
    await asyncio.sleep(0.1)

    # Create a large payload > 4096 bytes
    large_text = "A" * 5000

    # Use JSON protocol v2.0
    _response = await send_command("PROCESS_TEXT", {"text": large_text})

    # Stop server
    daemon.stop()
    server_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await server_task

    # Verify dispatch
    assert mock_bus.dispatch.called
    args, _ = mock_bus.dispatch.call_args
    cmd_obj = args[0]

    # Check if text is fully received
    # The command parser now extracts text from data.text (JSON)
    assert len(cmd_obj.text) == 5000, f"Payload truncated! Expected 5000, got {len(cmd_obj.text)}"


@pytest.mark.asyncio
async def test_command_injection_prevention(mock_daemon):
    """
    Test that command injection via newlines is prevented by JSON protocol.
    Malicious input like "text\\nSTOP_RECORDING" should be treated as data, not commands.
    """
    daemon, mock_bus = mock_daemon

    # Configure mock to return a result
    mock_bus.dispatch.return_value = "texto procesado"

    # Start server
    server_task = asyncio.create_task(daemon.start_server())
    await asyncio.sleep(0.1)

    # Malicious payload with embedded command
    malicious_text = "hola\nSTOP_RECORDING\nadios"

    # Use JSON protocol v2.0
    _response = await send_command("PROCESS_TEXT", {"text": malicious_text})

    # Stop server
    daemon.stop()
    server_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await server_task

    # Verify only ONE command was dispatched (PROCESS_TEXT)
    # NOT two commands (PROCESS_TEXT + STOP_RECORDING)
    assert mock_bus.dispatch.call_count == 1, (
        f"Command injection! Expected 1 dispatch, got {mock_bus.dispatch.call_count}"
    )

    # Verify the text contains the newlines as data
    args, _ = mock_bus.dispatch.call_args
    cmd_obj = args[0]
    assert "\n" in cmd_obj.text, "Newlines should be preserved as data"
    assert cmd_obj.text == malicious_text, "Text should match exactly"
