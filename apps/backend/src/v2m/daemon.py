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
DAEMON PRINCIPAL DE VOICE2MACHINE

este módulo implementa el proceso daemon que mantiene el modelo whisper
cargado en memoria y escucha comandos ipc a través de un socket unix
el daemon es el componente central de la arquitectura responsable de

    - mantener el modelo de transcripción precargado para respuesta rápida
    - escuchar y procesar comandos ipc de los clientes
    - despachar comandos al bus de comandos (patrón cqrs)
    - gestionar el ciclo de vida del servicio

ARQUITECTURA
    el daemon utiliza asyncio para manejar múltiples conexiones de clientes
    de forma concurrente los comandos recibidos son despachados al
    ``CommandBus`` que los redirige al handler apropiado

    socket unix -> daemon -> commandbus -> handler -> servicios

EJEMPLO
    iniciar el daemon directamente::

        python -m v2m.daemon

    o a través del punto de entrada principal::

        python -m v2m.main --daemon

NOTE
    el daemon debe ejecutarse con permisos para acceder al micrófono
    y crear archivos en /tmp/
"""

import asyncio
import atexit
import json
import os
import signal
import sys
from pathlib import Path

import psutil

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


class Daemon:
    """
    CLASE PRINCIPAL DEL DAEMON QUE GESTIONA EL CICLO DE VIDA Y LAS COMUNICACIONES IPC

    el daemon es un proceso persistente diseñado para ejecutarse en segundo plano
    mantiene el modelo whisper en memoria para evitar tiempos de carga en cada
    transcripción y proporciona una interfaz ipc para recibir comandos

    ATTRIBUTES:
        running: indica si el daemon está activo y procesando comandos
        socket_path: ruta al archivo del socket unix para comunicación ipc
        command_bus: instancia del bus de comandos para despachar operaciones

    EXAMPLE
        iniciar el daemon::

            daemon = Daemon()
            daemon.run()  # bloquea hasta sigterm o sigint

    WARNING
        solo debe haber una instancia del daemon ejecutándose a la vez
        el daemon detecta instancias previas mediante el socket unix
    """
    def __init__(self) -> None:
        """
        INICIALIZA LA INSTANCIA DEL DAEMON

        configura la ruta del socket obtiene el bus de comandos del contenedor
        de inyección de dependencias y limpia archivos huérfanos de ejecuciones
        anteriores que pudieron terminar de forma inesperada

        NOTE
            si existe un archivo de bandera de grabación de una ejecución
            anterior por un error será eliminado automáticamente
        """
        self.running = False
        self.socket_path = Path(SOCKET_PATH)
        self.pid_file = Path("/tmp/v2m_daemon.pid")
        self.command_bus = container.get_command_bus()

        # limpieza de procesos zombie crítico
        self._cleanup_orphaned_processes()

        # limpiar flag de grabación si existe recuperación de error
        if config.paths.recording_flag.exists():
            logger.warning("limpiando flag de grabación huérfano")
            config.paths.recording_flag.unlink()

        # registrar limpieza automática al terminar proceso
        atexit.register(self._cleanup_resources)

        # monitor de sistema
        self.system_monitor = SystemMonitor()
        self.paused = False

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """
        MANEJA LAS CONEXIONES ENTRANTES DE CLIENTES IPC

        este método es llamado por el servidor asyncio para cada nueva conexión
        lee el mensaje del socket lo decodifica ejecuta el comando correspondiente
        y envía una respuesta al cliente

        PROTOCOLO V2.0 (JSON)
            request:  {"cmd": "COMMAND", "data": {...}}
            response: {"status": "success|error", "data": {...}, "error": "..."}

        ARGS:
            reader: flujo de lectura asíncrono para recibir datos del cliente
            writer: flujo de escritura asíncrono para enviar respuestas al cliente

        COMANDOS SOPORTADOS
            - ``START_RECORDING`` inicia la grabación de audio
            - ``STOP_RECORDING`` detiene y transcribe el audio
            - ``PROCESS_TEXT`` refina el texto con llm (data.text requerido)
            - ``PING`` verifica que el daemon esté activo responde pong
            - ``GET_STATUS`` retorna estado actual (recording|idle)
            - ``SHUTDOWN`` detiene el daemon de forma ordenada

        NOTE
            los errores durante el procesamiento de comandos son capturados
            y devueltos como respuesta estructurada sin terminar la conexión
        """
        response: IPCResponse
        cmd_name = "unknown"

        try:
            # protocolo de framing 4 bytes longitud big endian + payload
            header_data = await reader.readexactly(4)
            length = int.from_bytes(header_data, byteorder="big")

            # SECURITY FIX: validar tamaño antes de leer (previene DoS/OOM)
            if length > MAX_PAYLOAD_SIZE:
                logger.warning(f"payload rechazado: {length} bytes > {MAX_PAYLOAD_SIZE} límite")
                response = IPCResponse(
                    status="error",
                    error=f"payload excede límite de {MAX_PAYLOAD_SIZE // (1024*1024)}MB"
                )
                # FRAMING: enviar header de 4 bytes + payload
                resp_bytes = response.to_json().encode("utf-8")
                writer.write(len(resp_bytes).to_bytes(4, byteorder="big") + resp_bytes)
                await writer.drain()
                writer.close()
                return

            payload_data = await reader.readexactly(length)
            message = payload_data.decode("utf-8").strip()
        except asyncio.IncompleteReadError:
            logger.warning("lectura incompleta desde el cliente")
            return
        except Exception as e:
            logger.error(f"error leyendo mensaje ipc: {e}")
            return

        logger.info(f"mensaje ipc recibido: {message[:200]}...")  # truncar log

        # parsear JSON (protocolo v2.0)
        try:
            req = IPCRequest.from_json(message)
            cmd_name = req.cmd
            data = req.data or {}
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"json inválido, rechazando: {e}")
            response = IPCResponse(
                status="error",
                error=f"formato JSON inválido: {e!s}"
            )
            # FRAMING: enviar header de 4 bytes + payload
            resp_bytes = response.to_json().encode("utf-8")
            writer.write(len(resp_bytes).to_bytes(4, byteorder="big") + resp_bytes)
            await writer.drain()
            writer.close()
            return

        try:
            if cmd_name == IPCCommand.START_RECORDING:
                if self.paused:
                     response = IPCResponse(status="error", error="el daemon está pausado")
                else:
                    await self.command_bus.dispatch(StartRecordingCommand())
                    response = IPCResponse(status="success", data={"state": "recording", "message": "grabación iniciada"})

            elif cmd_name == IPCCommand.STOP_RECORDING:
                if self.paused:
                     response = IPCResponse(status="error", error="el daemon está pausado")
                else:
                    result = await self.command_bus.dispatch(StopRecordingCommand())
                    if result:
                        response = IPCResponse(status="success", data={"state": "idle", "transcription": result})
                    else:
                        response = IPCResponse(status="error", error="no se detectó voz en el audio")

            elif cmd_name == IPCCommand.PROCESS_TEXT:
                if self.paused:
                     response = IPCResponse(status="error", error="el daemon está pausado")
                else:
                    # SECURITY FIX: texto viene encapsulado en data, no concatenado
                    text = data.get("text")
                    if not text:
                        response = IPCResponse(status="error", error="falta data.text en el payload")
                    else:
                        result = await self.command_bus.dispatch(ProcessTextCommand(text))
                        # ProcessTextCommand siempre retorna str (fix gemini: eliminamos if redundante)
                        response = IPCResponse(status="success", data={"refined_text": result})

            elif cmd_name == IPCCommand.UPDATE_CONFIG:
                updates = data.get("updates")
                if not updates:
                     response = IPCResponse(status="error", error="falta data.updates en el payload")
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

                # Enriquecer respuesta con telemetría
                metrics = self.system_monitor.get_system_metrics()

                response = IPCResponse(status="success", data={
                    "state": state,
                    "telemetry": metrics
                })

            elif cmd_name == IPCCommand.SHUTDOWN:
                self.running = False
                response = IPCResponse(status="success", data={"message": "SHUTTING_DOWN"})

            else:
                logger.warning(f"comando desconocido: {cmd_name}")
                response = IPCResponse(status="error", error=f"comando desconocido: {cmd_name}")

        except Exception as e:
            logger.error(f"error manejando comando {cmd_name}: {e}")
            response = IPCResponse(status="error", error=str(e))

        # FRAMING: enviar header de 4 bytes con longitud + payload JSON
        # esto es CRÍTICO para que el frontend Rust pueda leer la respuesta
        response_bytes = response.to_json().encode("utf-8")
        response_len = len(response_bytes)
        writer.write(response_len.to_bytes(4, byteorder="big") + response_bytes)
        await writer.drain()
        writer.close()

        if cmd_name == IPCCommand.SHUTDOWN:
            self.stop()

    async def start_server(self) -> None:
        """
        INICIA EL SERVIDOR DE SOCKET UNIX

        verifica si existe un socket previo y determina si hay otro daemon
        activo si el socket existe pero no hay daemon escuchando lo elimina
        y crea uno nuevo

        RAISES:
            SystemExit: si ya hay otro daemon activo escuchando en el socket

        NOTE
            este método bloquea indefinidamente hasta que se llame a ``stop()``
            o se reciba una señal de terminación
        """
        if self.socket_path.exists():
            # verificar si el socket está realmente vivo
            try:
                reader, writer = await asyncio.open_unix_connection(str(self.socket_path))
                writer.close()
                await writer.wait_closed()
                logger.error("el daemon ya se está ejecutando")
                sys.exit(1)
            except (ConnectionRefusedError, FileNotFoundError):
                # el socket existe pero nadie está escuchando es seguro eliminarlo
                self.socket_path.unlink()

        server = await asyncio.start_unix_server(self.handle_client, str(self.socket_path))

        # escribir pid file para poder rastrear el proceso
        self.pid_file.write_text(str(os.getpid()))
        logger.info(f"daemon escuchando en {self.socket_path} (pid: {os.getpid()})")

        self.running = True

        # mantener el servidor en funcionamiento
        async with server:
            await server.serve_forever()

    def _cleanup_orphaned_processes(self) -> None:
        """
        LIMPIEZA AGRESIVA DE TODOS LOS PROCESOS V2M HUÉRFANOS

        esta función es crítica para la experiencia de usuario un proceso consumiendo gpu sin
        feedback claro se interpreta como malware o minería de criptomonedas

        POLÍTICA TOLERANCIA CERO PARA PROCESOS ZOMBIE
        - mata todos los procesos v2m excepto el actual
        - libera vram inmediatamente
        - limpia todos los archivos residuales
        """
        current_pid = os.getpid()
        killed_count = 0

        try:
            # fase 1 matar todos los procesos v2m excepto el actual
            # fase 1 matar todos los procesos v2m excepto el actual
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline_list = proc.info['cmdline'] or []
                    cmdline_str = ' '.join(cmdline_list)
                    proc_name = (proc.info['name'] or '').lower()

                    # CRITERIOS ESTRICTOS PARA IDENTIFICAR PROCESOS V2M:
                    # 1. Debe ser un proceso Python o el binario 'v2m'
                    # 2. Debe indicar ejecución del módulo v2m específico
                    is_python = 'python' in proc_name
                    is_v2m_binary = proc_name == 'v2m'

                    # Marcadores fuertes de que es REALMENTE la app v2m
                    # Evita falsos positivos como "vim v2m_notes.txt"
                    # Buscamos: "python -m v2m", "python -m v2m.daemon", etc.
                    is_v2m_module = any(marker in cmdline_str for marker in [
                        'v2m.daemon',
                        'v2m.main',
                        '-m v2m'
                    ])

                    if ((is_python and is_v2m_module) or is_v2m_binary):
                        # Filtros de seguridad adicionales (excluir yo mismo y herramientas dev)
                        if (proc.pid != current_pid and
                            'language_server' not in cmdline_str and
                            'jedi' not in cmdline_str and
                            'health_check' not in cmdline_str):

                            logger.warning(f"🧹 eliminando proceso v2m huérfano pid {proc.pid}: {cmdline_str[:50]}...")
                            proc.kill()
                            try:
                                proc.wait(timeout=3)
                            except psutil.TimeoutExpired:
                                pass
                            killed_count += 1
                            logger.info(f"✅ proceso {proc.pid} eliminado")

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            if killed_count > 0:
                logger.info(f"🧹 total: {killed_count} proceso(s) zombie eliminado(s)")

                # fase 2 liberar vram inmediatamente después de matar procesos
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        # forzar sincronización para liberar vram ahora
                        torch.cuda.synchronize()
                except Exception:
                    pass

            # fase 3 limpiar todos los archivos residuales
            residual_files = [
                self.pid_file,
                self.socket_path,
                Path("/tmp/v2m_recording.pid"),
            ]
            for f in residual_files:
                if f.exists():
                    try:
                        f.unlink()
                        logger.debug(f"🧹 archivo residual eliminado: {f}")
                    except Exception:
                        pass

        except Exception as e:
            logger.warning(f"error durante limpieza agresiva: {e}")

    def _cleanup_resources(self) -> None:
        """
        LIMPIA RECURSOS AL TERMINAR LLAMADO POR ATEXIT

        libera vram elimina socket y pid file para prevenir procesos zombie
        """
        try:
            logger.info("🧹 limpiando recursos del daemon...")

            # liberar vram de gpu si hay modelos cargados
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    logger.info("✅ vram liberada")
            except Exception as e:
                logger.debug(f"no se pudo liberar vram: {e}")

            # eliminar socket
            if self.socket_path.exists():
                self.socket_path.unlink()
                logger.info("✅ socket eliminado")

            # eliminar pid file
            if self.pid_file.exists():
                self.pid_file.unlink()
                logger.info("✅ pid file eliminado")
        except Exception as e:
            logger.error(f"error durante limpieza: {e}")

    def stop(self) -> None:
        """
        DETIENE EL DAEMON Y LIBERA RECURSOS

        realiza una limpieza ordenada eliminando el archivo del socket unix
        y terminando el proceso este método es llamado automáticamente al
        recibir señales sigint o sigterm o al procesar el comando shutdown

        RAISES:
            SystemExit: siempre termina con código 0 exit exitoso
        """
        logger.info("deteniendo daemon...")
        self._cleanup_resources()
        sys.exit(0)

    def run(self) -> None:
        """
        EJECUTA EL BUCLE PRINCIPAL DEL DAEMON

        configura los manejadores de señales posix sigint sigterm para
        permitir una terminación ordenada crea un nuevo event loop de asyncio
        y ejecuta el servidor hasta que sea detenido

        este método es bloqueante y no retorna hasta que el daemon termine

        SEÑALES MANEJADAS
            - ``SIGINT`` interrupción de teclado ctrl+c
            - ``SIGTERM`` señal de terminación estándar

        EXAMPLE
            uso típico::

                if __name__ == "__main__":
                    daemon = Daemon()
                    daemon.run()
        """
        # configurar manejadores de señales
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        def signal_handler():
            logger.info("señal recibida apagando...")
            self.stop()

        # nota add_signal_handler no es compatible con windows pero estamos en linux
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
