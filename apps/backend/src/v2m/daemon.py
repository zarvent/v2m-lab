
"""
Demonio Voice2Machine.

Este módulo implementa el proceso demonio en segundo plano que mantiene el modelo Whisper
en memoria y escucha comandos IPC a través de un socket Unix.

El demonio es responsable de:
    - Mantener el modelo de transcripción precargado para una respuesta rápida.
    - Procesar comandos IPC de los clientes (frontend, CLI).
    - Despachar comandos al CommandBus (patrón CQRS).
    - Gestionar el ciclo de vida del servicio.
"""

import asyncio
import atexit
import contextlib
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


from v2m.application.commands import (
    GetConfigCommand,
    PauseDaemonCommand,
    ProcessTextCommand,
    ResumeDaemonCommand,
    StartRecordingCommand,
    StopRecordingCommand,
    TranscribeFileCommand,
    TranslateTextCommand,
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
    Clase principal del Demonio que gestiona el ciclo de vida y las comunicaciones IPC.
    """

    def __init__(self) -> None:
        """
        Inicializa la instancia del Demonio.
        """
        self.running = False
        self.socket_path = Path(SOCKET_PATH)
        # Cumplimiento con XDG_RUNTIME_DIR
        from v2m.utils.paths import get_secure_runtime_dir

        self.pid_file = get_secure_runtime_dir() / "v2m_daemon.pid"
        self.command_bus = container.get_command_bus()

        # Limpieza de procesos huérfanos de ejecuciones previas
        self._cleanup_orphaned_processes()

        # Limpieza de bandera de grabación si existe (recuperación de errores)
        if config.paths.recording_flag.exists():
            logger.warning("limpiando bandera de grabación huérfana")
            config.paths.recording_flag.unlink()

        # Registrar limpieza al salir
        atexit.register(self._cleanup_resources)

        # Monitor del sistema
        self.system_monitor = SystemMonitor()
        self.paused = False

    async def _send_response(self, writer: asyncio.StreamWriter, response: IPCResponse) -> None:
        """
        Auxiliar para enviar una respuesta JSON enmarcada al cliente.
        """
        try:
            resp_bytes = response.to_json().encode("utf-8")
            resp_len = len(resp_bytes)
            writer.write(resp_len.to_bytes(HEADER_SIZE, byteorder="big") + resp_bytes)
            await writer.drain()
        except Exception as e:
            logger.error(f"fallo al enviar respuesta: {e}")
            # Cerrar conexión en error crítico
            writer.close()

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """
        Maneja las conexiones entrantes de clientes IPC.
        Soporta conexiones persistentes y streaming de eventos.
        """
        # Registrar sesión para streaming (Events)
        if hasattr(container, "client_session_manager") and container.client_session_manager:
            await container.client_session_manager.register(writer)

        try:
            while True:
                response: IPCResponse
                cmd_name = "unknown"

                try:
                    # Leer cabecera de 4 bytes (big endian)
                    try:
                        header_data = await reader.readexactly(HEADER_SIZE)
                    except asyncio.IncompleteReadError:
                        # Cliente cerró la conexión (EOF normal)
                        break

                    length = int.from_bytes(header_data, byteorder="big")

                    if length > MAX_PAYLOAD_SIZE:
                        # Detect raw JSON (protocol mismatch): if header decodes to '{...'
                        # it means client sent raw JSON without 4-byte length prefix
                        try:
                            header_ascii = header_data.decode("ascii", errors="ignore")
                            if header_ascii.startswith("{"):
                                logger.error(
                                    f"protocolo incorrecto: cliente envió JSON sin prefijo de longitud. "
                                    f"Header bytes: {header_data.hex()} = '{header_ascii}'"
                                )
                            else:
                                logger.warning(f"carga rechazada: {length} bytes > límite de {MAX_PAYLOAD_SIZE}")
                        except Exception:
                            logger.warning(f"carga rechazada: {length} bytes > límite de {MAX_PAYLOAD_SIZE}")

                        response = IPCResponse(
                            status="error", error="protocolo IPC inválido: use prefijo de longitud de 4 bytes"
                        )
                        await self._send_response(writer, response)
                        # Error de protocolo irrecuperable, cerrar conexión
                        break

                    payload_data = await reader.readexactly(length)
                    message = payload_data.decode("utf-8").strip()

                except asyncio.IncompleteReadError:
                    logger.warning("lectura incompleta del payload")
                    break
                except Exception as e:
                    logger.error(f"error leyendo mensaje ipc: {e}")
                    break

                logger.debug(f"ipc: {message[:100]}")

                # Parsear JSON
                try:
                    req = IPCRequest.from_json(message)
                    cmd_name = req.cmd
                    data = req.data or {}
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"json inválido, rechazando: {e}")
                    response = IPCResponse(status="error", error=f"formato JSON inválido: {e!s}")
                    await self._send_response(writer, response)
                    continue

                try:
                    if cmd_name == IPCCommand.START_RECORDING:
                        if self.paused:
                            response = IPCResponse(status="error", error="el demonio está pausado")
                        else:
                            await self.command_bus.dispatch(StartRecordingCommand())
                            response = IPCResponse(
                                status="success", data={"state": "recording", "message": "grabación iniciada"}
                            )

                    elif cmd_name == IPCCommand.STOP_RECORDING:
                        if self.paused:
                            response = IPCResponse(status="error", error="el demonio está pausado")
                        else:
                            result = await self.command_bus.dispatch(StopRecordingCommand())
                            if result:
                                response = IPCResponse(
                                    status="success", data={"state": "idle", "transcription": result}
                                )
                            else:
                                response = IPCResponse(status="error", error="no se detectó voz")

                    elif cmd_name == IPCCommand.PROCESS_TEXT:
                        if self.paused:
                            response = IPCResponse(status="error", error="el demonio está pausado")
                        else:
                            text = data.get("text")
                            if not text:
                                response = IPCResponse(status="error", error="falta data.text en la carga útil")
                            else:
                                result = await self.command_bus.dispatch(ProcessTextCommand(text))
                                response = IPCResponse(status="success", data={"refined_text": result, "state": "idle"})

                    elif cmd_name == IPCCommand.TRANSLATE_TEXT:
                        if self.paused:
                            response = IPCResponse(status="error", error="el demonio está pausado")
                        else:
                            text = data.get("text")
                            target_lang = data.get("target_lang", "en")
                            if not text:
                                response = IPCResponse(status="error", error="falta data.text en la carga útil")
                            else:
                                result = await self.command_bus.dispatch(TranslateTextCommand(text, target_lang))
                                response = IPCResponse(status="success", data={"refined_text": result, "state": "idle"})

                    elif cmd_name == IPCCommand.UPDATE_CONFIG:
                        updates = data.get("updates")
                        if not updates:
                            response = IPCResponse(status="error", error="falta data.updates en la carga útil")
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
                        state = (
                            "paused"
                            if self.paused
                            else ("recording" if config.paths.recording_flag.exists() else "idle")
                        )
                        metrics = self.system_monitor.get_system_metrics()
                        response = IPCResponse(status="success", data={"state": state, "telemetry": metrics})

                    elif cmd_name == IPCCommand.SHUTDOWN:
                        self.running = False
                        response = IPCResponse(status="success", data={"message": "SHUTTING_DOWN"})

                    elif cmd_name == IPCCommand.TRANSCRIBE_FILE:
                        if self.paused:
                            response = IPCResponse(status="error", error="el demonio está pausado")
                        else:
                            file_path = data.get("file_path")
                            if not file_path:
                                response = IPCResponse(status="error", error="falta data.file_path en la carga útil")
                            else:
                                logger.info(f"transcribiendo archivo: {file_path}")
                                result = await self.command_bus.dispatch(TranscribeFileCommand(file_path))
                                response = IPCResponse(
                                    status="success", data={"state": "idle", "transcription": result}
                                )

                    elif cmd_name == IPCCommand.TOGGLE_RECORDING:
                        if self.paused:
                            response = IPCResponse(status="error", error="el demonio está pausado")
                        else:
                            # Verificar estado (si existe la bandera, estamos grabando)
                            is_recording = config.paths.recording_flag.exists()
                            if is_recording:
                                result = await self.command_bus.dispatch(StopRecordingCommand())
                                if result:
                                    response = IPCResponse(
                                        status="success", data={"state": "idle", "transcription": result}
                                    )
                                else:
                                    response = IPCResponse(status="error", error="no se detectó voz")
                            else:
                                await self.command_bus.dispatch(StartRecordingCommand())
                                response = IPCResponse(
                                    status="success", data={"state": "recording", "message": "grabación iniciada"}
                                )

                    else:
                        logger.warning(f"comando desconocido: {cmd_name}")
                        response = IPCResponse(status="error", error=f"comando desconocido: {cmd_name}")

                except Exception as e:
                    logger.error(f"error manejando comando {cmd_name}: {e}")
                    response = IPCResponse(status="error", error=str(e))

                await self._send_response(writer, response)

                if cmd_name == IPCCommand.SHUTDOWN:
                    self.stop()
                    break

        except Exception as e:
            logger.error(f"error en bucle de cliente: {e}")
        finally:
            # Limpiar sesión
            if hasattr(container, "client_session_manager") and container.client_session_manager:
                await container.client_session_manager.unregister()

            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()

    async def start_server(self) -> None:
        """
        Inicia el servidor socket Unix.
        """
        if self.socket_path.exists():
            # Verificar si el socket está realmente vivo
            try:
                _reader, writer = await asyncio.open_unix_connection(str(self.socket_path))
                writer.close()
                await writer.wait_closed()
                logger.error("el demonio ya está en ejecución")
                sys.exit(1)
            except (ConnectionRefusedError, FileNotFoundError):
                # El socket existe pero nadie escucha, seguro de eliminar
                self.socket_path.unlink()

        server = await asyncio.start_unix_server(self.handle_client, str(self.socket_path))

        self.pid_file.write_text(str(os.getpid()))
        logger.info(f"demonio escuchando en {self.socket_path} (pid: {os.getpid()})")

        self.running = True

        async with server:
            await server.serve_forever()

    def _cleanup_orphaned_processes(self) -> None:
        """
        Limpia procesos v2m huérfanos.

        Termina otras instancias de v2m, libera VRAM y limpia archivos residuales.
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

                    # Criterios de identificación
                    is_v2m_module = any(marker in cmdline_str for marker in ["v2m.daemon", "v2m.main", "-m v2m"])
                    is_v2m_binary = proc_name == "v2m"

                    if is_v2m_module or is_v2m_binary:
                        proc.kill()
                        with contextlib.suppress(psutil.TimeoutExpired):
                            proc.wait(timeout=3)
                        killed_count += 1

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            if killed_count > 0:
                logger.info(f"🧹 total: {killed_count} proceso(s) zombie eliminado(s)")

                # Liberar VRAM
                try:
                    if torch and torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        torch.cuda.synchronize()
                except Exception:
                    pass

            # Limpiar archivos residuales
            residual_files = [
                self.pid_file,
                self.socket_path,
                config.paths.recording_flag,
            ]
            for f in residual_files:
                if f.exists():
                    try:
                        f.unlink()
                        logger.debug(f"🧹 archivo residual eliminado: {f}")
                    except Exception:
                        pass

        except Exception as e:
            logger.warning(f"error durante la limpieza: {e}")

    def _cleanup_resources(self) -> None:
        """
        Limpia recursos al salir (atexit).
        """
        try:
            logger.info("🧹 limpiando recursos del demonio...")

            # Liberar VRAM
            try:
                if torch and torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    logger.info("✅ vram liberada")
            except Exception as e:
                logger.debug(f"no se pudo liberar vram: {e}")

            # Eliminar socket
            if self.socket_path.exists():
                self.socket_path.unlink()
                logger.info("✅ socket eliminado")

            # Eliminar archivo pid
            if self.pid_file.exists():
                self.pid_file.unlink()
                logger.info("✅ archivo pid eliminado")
        except Exception as e:
            logger.error(f"error durante la limpieza: {e}")

    def stop(self) -> None:
        """
        Detiene el demonio y libera recursos.
        """
        logger.info("deteniendo demonio...")
        self._cleanup_resources()
        sys.exit(0)

    def run(self) -> None:
        """
        Ejecuta el bucle principal del demonio.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        def signal_handler():
            logger.info("señal recibida, apagando...")
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
