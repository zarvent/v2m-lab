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
Voice2Machine Daemon.

This module implements the background daemon process that keeps the Whisper model
in memory and listens for IPC commands via a Unix socket.

The daemon is responsible for:
    - Maintaining the transcription model preloaded.
    - Processing IPC commands from clients.
    - Dispatching commands to the CommandBus.
    - Managing the service lifecycle.
"""

import asyncio
import atexit
import json
import os
import signal
import sys
from pathlib import Path

import psutil

try:
    import torch
except ImportError:
    torch = None

import contextlib

from v2m.application.commands import (
    GetConfigCommand,
    PauseDaemonCommand,
    ProcessTextCommand,
    ResumeDaemonCommand,
    StartRecordingCommand,
    StopRecordingCommand,
    UpdateConfigCommand,
)
from v2m.config import config
from v2m.core.di.container import container
from v2m.core.ipc_protocol import MAX_PAYLOAD_SIZE, SOCKET_PATH, IPCCommand, IPCRequest, IPCResponse
from v2m.core.logging import logger
from v2m.infrastructure.system_monitor import SystemMonitor

HEADER_SIZE = 4


class Daemon:
    """
    Main Daemon class managing lifecycle and IPC communications.
    """

    def __init__(self) -> None:
        """
        Initializes the Daemon instance.
        """
        self.running = False
        self.socket_path = Path(SOCKET_PATH)
        # XDG_RUNTIME_DIR compliance
        from v2m.utils.paths import get_secure_runtime_dir

        self.pid_file = get_secure_runtime_dir() / "v2m_daemon.pid"
        self.command_bus = container.get_command_bus()

        # Cleanup orphaned processes from previous runs
        self._cleanup_orphaned_processes()

        # Cleanup recording flag if it exists (error recovery)
        if config.paths.recording_flag.exists():
            logger.warning("cleaning up orphaned recording flag")
            config.paths.recording_flag.unlink()

        # Register cleanup on exit
        atexit.register(self._cleanup_resources)

        # System monitor
        self.system_monitor = SystemMonitor()
        self.paused = False

    async def _send_response(self, writer: asyncio.StreamWriter, response: IPCResponse) -> None:
        """
        Helper to send a framed JSON response to the client.
        """
        try:
            resp_bytes = response.to_json().encode("utf-8")
            resp_len = len(resp_bytes)
            writer.write(resp_len.to_bytes(HEADER_SIZE, byteorder="big") + resp_bytes)
            await writer.drain()
        except Exception as e:
            logger.error(f"failed to send response: {e}")
        finally:
            writer.close()

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """
        Handles incoming IPC client connections.
        """
        response: IPCResponse
        cmd_name = "unknown"

        try:
            # Read 4-byte header (big endian)
            header_data = await reader.readexactly(HEADER_SIZE)
            length = int.from_bytes(header_data, byteorder="big")

            if length > MAX_PAYLOAD_SIZE:
                logger.warning(f"payload rejected: {length} bytes > {MAX_PAYLOAD_SIZE} limit")
                response = IPCResponse(
                    status="error", error=f"payload exceeds limit of {MAX_PAYLOAD_SIZE // (1024 * 1024)}MB"
                )
                await self._send_response(writer, response)
                return

            payload_data = await reader.readexactly(length)
            message = payload_data.decode("utf-8").strip()
        except asyncio.IncompleteReadError:
            logger.warning("incomplete read from client")
            writer.close()
            await writer.wait_closed()
            return
        except Exception as e:
            logger.error(f"error reading ipc message: {e}")
            writer.close()
            await writer.wait_closed()
            return

        logger.info(f"ipc message received: {message[:200]}...")

        # Parse JSON
        try:
            req = IPCRequest.from_json(message)
            cmd_name = req.cmd
            data = req.data or {}
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"invalid json, rejecting: {e}")
            response = IPCResponse(status="error", error=f"invalid JSON format: {e!s}")
            await self._send_response(writer, response)
            return

        try:
            if cmd_name == IPCCommand.START_RECORDING:
                if self.paused:
                    response = IPCResponse(status="error", error="daemon is paused")
                else:
                    await self.command_bus.dispatch(StartRecordingCommand())
                    response = IPCResponse(
                        status="success", data={"state": "recording", "message": "recording started"}
                    )

            elif cmd_name == IPCCommand.STOP_RECORDING:
                if self.paused:
                    response = IPCResponse(status="error", error="daemon is paused")
                else:
                    result = await self.command_bus.dispatch(StopRecordingCommand())
                    if result:
                        response = IPCResponse(status="success", data={"state": "idle", "transcription": result})
                    else:
                        response = IPCResponse(status="error", error="no voice detected")

            elif cmd_name == IPCCommand.PROCESS_TEXT:
                if self.paused:
                    response = IPCResponse(status="error", error="daemon is paused")
                else:
                    text = data.get("text")
                    if not text:
                        response = IPCResponse(status="error", error="missing data.text in payload")
                    else:
                        result = await self.command_bus.dispatch(ProcessTextCommand(text))
                        response = IPCResponse(status="success", data={"refined_text": result})

            elif cmd_name == IPCCommand.UPDATE_CONFIG:
                updates = data.get("updates")
                if not updates:
                    response = IPCResponse(status="error", error="missing data.updates in payload")
                else:
                    result = await self.command_bus.dispatch(UpdateConfigCommand(updates))
                    response = IPCResponse(status="success", data=result)

            elif cmd_name == IPCCommand.GET_CONFIG:
                result = await self.command_bus.dispatch(GetConfigCommand())
                response = IPCResponse(status="success", data={"config": result})

            elif cmd_name == IPCCommand.PAUSE_DAEMON:
                await self.command_bus.dispatch(PauseDaemonCommand())
                self.paused = True
                response = IPCResponse(status="success", data={"state": "paused"})

            elif cmd_name == IPCCommand.RESUME_DAEMON:
                await self.command_bus.dispatch(ResumeDaemonCommand())
                self.paused = False
                response = IPCResponse(status="success", data={"state": "running"})

            elif cmd_name == IPCCommand.PING:
                response = IPCResponse(status="success", data={"message": "PONG"})

            elif cmd_name == IPCCommand.GET_STATUS:
                state = "paused" if self.paused else ("recording" if config.paths.recording_flag.exists() else "idle")
                metrics = self.system_monitor.get_system_metrics()
                response = IPCResponse(status="success", data={"state": state, "telemetry": metrics})

            elif cmd_name == IPCCommand.SHUTDOWN:
                self.running = False
                response = IPCResponse(status="success", data={"message": "SHUTTING_DOWN"})

            else:
                logger.warning(f"unknown command: {cmd_name}")
                response = IPCResponse(status="error", error=f"unknown command: {cmd_name}")

        except Exception as e:
            logger.error(f"error handling command {cmd_name}: {e}")
            response = IPCResponse(status="error", error=str(e))

        await self._send_response(writer, response)

        if cmd_name == IPCCommand.SHUTDOWN:
            self.stop()

    async def start_server(self) -> None:
        """
        Starts the Unix socket server.
        """
        if self.socket_path.exists():
            # Check if socket is actually alive
            try:
                _reader, writer = await asyncio.open_unix_connection(str(self.socket_path))
                writer.close()
                await writer.wait_closed()
                logger.error("daemon is already running")
                sys.exit(1)
            except (ConnectionRefusedError, FileNotFoundError):
                # Socket exists but no one listening, safe to remove
                self.socket_path.unlink()

        server = await asyncio.start_unix_server(self.handle_client, str(self.socket_path))

        self.pid_file.write_text(str(os.getpid()))
        logger.info(f"daemon listening on {self.socket_path} (pid: {os.getpid()})")

        self.running = True

        async with server:
            await server.serve_forever()

    def _cleanup_orphaned_processes(self) -> None:
        """
        Cleans up orphaned v2m processes.

        Terminates other v2m instances, releases VRAM, and cleans up residual files.
        """
        current_pid = os.getpid()
        killed_count = 0

        try:
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if proc.pid == current_pid:
                        continue

                    cmdline = proc.info["cmdline"] or []
                    cmdline_str = " ".join(cmdline)
                    proc_name = (proc.info["name"] or "").lower()

                    # Identification criteria
                    is_v2m_module = any(marker in cmdline_str for marker in ["v2m.daemon", "v2m.main", "-m v2m"])
                    is_v2m_binary = proc_name == "v2m"

                    if is_v2m_module or is_v2m_binary:
                        logger.warning(f"🧹 killing orphaned v2m process pid {proc.pid}: {cmdline_str[:50]}...")
                        proc.kill()
                        with contextlib.suppress(psutil.TimeoutExpired):
                            proc.wait(timeout=3)
                        killed_count += 1
                        logger.info(f"✅ process {proc.pid} killed")

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            if killed_count > 0:
                logger.info(f"🧹 total: {killed_count} zombie process(s) killed")

                # Release VRAM
                try:
                    if torch and torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        torch.cuda.synchronize()
                except Exception:
                    pass

            # Clean residual files
            residual_files = [
                self.pid_file,
                self.socket_path,
                config.paths.recording_flag,
            ]
            for f in residual_files:
                if f.exists():
                    try:
                        f.unlink()
                        logger.debug(f"🧹 residual file removed: {f}")
                    except Exception:
                        pass

        except Exception as e:
            logger.warning(f"error during cleanup: {e}")

    def _cleanup_resources(self) -> None:
        """
        Cleans up resources on exit (atexit).
        """
        try:
            logger.info("🧹 cleaning up daemon resources...")

            # Release VRAM
            try:
                if torch and torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    logger.info("✅ vram released")
            except Exception as e:
                logger.debug(f"could not release vram: {e}")

            # Remove socket
            if self.socket_path.exists():
                self.socket_path.unlink()
                logger.info("✅ socket removed")

            # Remove pid file
            if self.pid_file.exists():
                self.pid_file.unlink()
                logger.info("✅ pid file removed")
        except Exception as e:
            logger.error(f"error during cleanup: {e}")

    def stop(self) -> None:
        """
        Stops the daemon and releases resources.
        """
        logger.info("stopping daemon...")
        self._cleanup_resources()
        sys.exit(0)

    def run(self) -> None:
        """
        Runs the daemon main loop.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        def signal_handler():
            logger.info("signal received, shutting down...")
            self.stop()

        loop.add_signal_handler(signal.SIGINT, signal_handler)
        loop.add_signal_handler(signal.SIGTERM, signal_handler)

        try:
            loop.run_until_complete(self.start_server())
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()


if __name__ == "__main__":
    daemon = Daemon()
    daemon.run()
