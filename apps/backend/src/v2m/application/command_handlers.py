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
Manejadores de Comandos (Command Handlers).

Este módulo contiene la lógica de negocio central de la aplicación.
Cada manejador (handler) se suscribe a un tipo de comando específico y ejecuta
las acciones necesarias cuando dicho comando es despachado por el Command Bus.

Este diseño sigue el patrón CQRS (Command Query Responsibility Segregation),
permitiendo un desacoplamiento efectivo entre la capa de entrada (daemon/main)
y la lógica de dominio.
"""

import asyncio
import atexit
import re
from concurrent.futures import ThreadPoolExecutor

from v2m.application.commands import (
    GetConfigCommand,
    PauseDaemonCommand,
    ProcessTextCommand,
    ResumeDaemonCommand,
    StartRecordingCommand,
    StopRecordingCommand,
    TranslateTextCommand,
    UpdateConfigCommand,
)
from v2m.application.config_manager import ConfigManager
from v2m.application.llm_service import LLMService
from v2m.application.transcription_service import TranscriptionService
from v2m.config import config
from v2m.core.cqrs.command import Command
from v2m.core.cqrs.command_handler import CommandHandler
from v2m.core.interfaces import ClipboardInterface, NotificationInterface
from v2m.core.logging import logger

# Executor dedicado para operaciones de ML (single worker) para evitar contención de GPU.
# Esto es más eficiente que el ThreadPoolExecutor por defecto de asyncio.to_thread para tareas intensivas.
_ml_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ml-inference")
atexit.register(_ml_executor.shutdown, wait=True)


class StartRecordingHandler(CommandHandler):
    """
    Manejador para el comando `StartRecordingCommand`.

    Interactúa con el servicio de transcripción para iniciar la grabación de audio
    y notifica al usuario del cambio de estado.
    """

    def __init__(
        self, transcription_service: TranscriptionService, notification_service: NotificationInterface
    ) -> None:
        """
        Inicializa el handler con sus dependencias.

        Args:
            transcription_service: Servicio responsable de la grabación y transcripción.
            notification_service: Servicio para enviar notificaciones al sistema.
        """
        self.transcription_service = transcription_service
        self.notification_service = notification_service

    async def handle(self, command: StartRecordingCommand) -> None:
        """
        Ejecuta la lógica para iniciar la grabación.
        """
        # Ejecutamos start_recording en un hilo para no bloquear el Event Loop
        # si la inicialización de audio (sounddevice) toma tiempo.
        await asyncio.to_thread(self.transcription_service.start_recording)

        # Crear bandera de grabación para señalización externa (scripts bash, indicadores de estado)
        config.paths.recording_flag.touch()

        self.notification_service.notify("🎤 voice2machine", "grabación iniciada...")

    def listen_to(self) -> type[Command]:
        return StartRecordingCommand


class StopRecordingHandler(CommandHandler):
    """
    Manejador para el comando `StopRecordingCommand`.

    Detiene la grabación, coordina la transcripción del audio capturado,
    copia el resultado al portapapeles y notifica al usuario.
    """

    def __init__(
        self,
        transcription_service: TranscriptionService,
        notification_service: NotificationInterface,
        clipboard_service: ClipboardInterface,
    ) -> None:
        """
        Inicializa el handler con sus dependencias.

        Args:
            transcription_service: Servicio de transcripción.
            notification_service: Servicio de notificaciones.
            clipboard_service: Interfaz con el portapapeles del sistema.
        """
        self.transcription_service = transcription_service
        self.notification_service = notification_service
        self.clipboard_service = clipboard_service

    async def handle(self, command: StopRecordingCommand) -> str | None:
        """
        Detiene la grabación y procesa la transcripción.

        Returns:
            str | None: El texto transcrito o None si no se detectó voz.
        """
        # Eliminar bandera de grabación para indicar fin de captura
        if config.paths.recording_flag.exists():
            config.paths.recording_flag.unlink()

        self.notification_service.notify("⚡ v2m procesando", "procesando...")

        # Usar executor dedicado para ML - evita bloquear el loop principal y contención
        loop = asyncio.get_running_loop()
        transcription = await loop.run_in_executor(_ml_executor, self.transcription_service.stop_and_transcribe)

        # Validación: si la transcripción está vacía, no copiar nada
        if not transcription.strip():
            self.notification_service.notify("❌ whisper", "no se detectó voz en el audio")
            return None

        self.clipboard_service.copy(transcription)
        preview = transcription[:80]  # Vista previa corta para la notificación
        self.notification_service.notify("✅ whisper - copiado", f"{preview}...")
        return transcription

    def listen_to(self) -> type[Command]:
        return StopRecordingCommand


class ProcessTextHandler(CommandHandler):
    """
    Manejador para el comando `ProcessTextCommand`.

    Utiliza un LLM (Large Language Model) para refinar o procesar un texto existente.
    El resultado se copia automáticamente al portapapeles.
    """

    def __init__(
        self,
        llm_service: LLMService,
        notification_service: NotificationInterface,
        clipboard_service: ClipboardInterface,
    ) -> None:
        """
        Args:
            llm_service: Servicio de interfaz con el LLM (local o remoto).
            notification_service: Servicio de notificaciones.
            clipboard_service: Servicio de portapapeles.
        """
        self.llm_service = llm_service
        self.notification_service = notification_service
        self.clipboard_service = clipboard_service

    async def handle(self, command: ProcessTextCommand) -> str | None:
        """
        Procesa el texto utilizando el LLM configurado.
        """
        try:
            # Soporte híbrido para implementaciones síncronas/asíncronas del servicio LLM
            if asyncio.iscoroutinefunction(self.llm_service.process_text):
                refined_text = await self.llm_service.process_text(command.text)
            else:
                refined_text = await asyncio.to_thread(self.llm_service.process_text, command.text)

            self.clipboard_service.copy(refined_text)
            backend_name = config.llm.backend  # "local" o "gemini"
            self.notification_service.notify(f"✅ {backend_name} - copiado", f"{refined_text[:80]}...")
            return refined_text

        except Exception:
            # Fallback (Plan B): Si el LLM falla, asegurar que el usuario tenga al menos el texto original
            backend_name = config.llm.backend
            self.notification_service.notify(f"⚠️ {backend_name} falló", "usando texto original...")
            self.clipboard_service.copy(command.text)
            self.notification_service.notify("✅ whisper - copiado (crudo)", f"{command.text[:80]}...")
            return command.text

    def listen_to(self) -> type[Command]:
        return ProcessTextCommand


class TranslateTextHandler(CommandHandler):
    """
    Manejador para el comando `TranslateTextCommand`.

    Utiliza el servicio de LLM para traducir texto a un idioma específico.
    """

    def __init__(
        self,
        llm_service: LLMService,
        notification_service: NotificationInterface,
    ) -> None:
        self.llm_service = llm_service
        self.notification_service = notification_service

    async def handle(self, command: TranslateTextCommand) -> str | None:
        """
        Ejecuta la traducción del texto.

        Args:
            command: Contiene el texto fuente y el idioma destino.
        """
        # Validación de seguridad para prevenir inyección en prompts
        if not re.match(r"^[a-zA-Z\s\-]{2,20}$", command.target_lang):
            logger.warning(f"Intento de traducción con idioma inválido: {command.target_lang}")
            self.notification_service.notify("❌ Error", "Idioma de destino inválido")
            return None

        try:
            # Check for async implementation or fallback to thread
            if asyncio.iscoroutinefunction(self.llm_service.translate_text):
                translated_text = await self.llm_service.translate_text(command.text, command.target_lang)
            else:
                translated_text = await asyncio.to_thread(
                    self.llm_service.translate_text, command.text, command.target_lang
                )

            self.notification_service.notify(
                f"✅ Traducción ({command.target_lang})", f"{translated_text[:80]}..."
            )
            return translated_text

        except Exception as e:
            logger.error(f"Error en traducción: {e}")
            self.notification_service.notify("❌ Error traducción", "Fallo al traducir texto")
            return None

    def listen_to(self) -> type[Command]:
        return TranslateTextCommand


class UpdateConfigHandler(CommandHandler):
    """
    Manejador para `UpdateConfigCommand`.

    Actúa como adaptador entre el esquema de configuración del Frontend y el Backend.
    Transforma la estructura plana o específica de la UI al formato jerárquico TOML.

    Mapping:
        Frontend: whisper.model
        Backend:  transcription.whisper.model
    """

    def __init__(self, config_manager: ConfigManager, notification_service: NotificationInterface) -> None:
        self.config_manager = config_manager
        self.notification_service = notification_service

    async def handle(self, command: UpdateConfigCommand) -> dict:
        updates = command.updates

        # Transformar esquema Frontend -> Estructura TOML Backend
        toml_updates = {}

        if "whisper" in updates:
            toml_updates.setdefault("transcription", {})["whisper"] = updates["whisper"]

        if "llm" in updates:
            toml_updates["llm"] = updates["llm"]

        if "gemini" in updates:
            toml_updates["gemini"] = updates["gemini"]

        if "paths" in updates:
            toml_updates["paths"] = updates["paths"]

        if "notifications" in updates:
            toml_updates["notifications"] = updates["notifications"]

        # Si no hubo transformaciones específicas, usar el objeto tal cual (fallback)
        final_updates = toml_updates if toml_updates else updates

        self.config_manager.update_config(final_updates)
        self.notification_service.notify("⚙️ v2m config", "configuración actualizada")
        return {"status": "ok", "message": "configuración actualizada, reinicio sugerido"}

    def listen_to(self) -> type[Command]:
        return UpdateConfigCommand


class GetConfigHandler(CommandHandler):
    """
    Manejador para `GetConfigCommand`.

    Adapta la configuración interna (TOML) al esquema esperado por el Frontend.
    Esto permite que el backend evolucione su estructura sin romper la UI.
    """

    def __init__(self, config_manager: ConfigManager) -> None:
        self.config_manager = config_manager

    async def handle(self, command: GetConfigCommand) -> dict:
        raw = self.config_manager.load_config()

        # Transformar TOML Backend -> Esquema Frontend
        # Backend: transcription.whisper.model
        # Frontend: whisper.model
        return {
            "whisper": raw.get("transcription", {}).get("whisper", {}),
            "llm": raw.get("llm", {}),
            "gemini": raw.get("gemini", {}),
            "paths": raw.get("paths", {}),
            "notifications": raw.get("notifications", {}),
        }

    def listen_to(self) -> type[Command]:
        return GetConfigCommand


class PauseDaemonHandler(CommandHandler):
    """
    Manejador para pausar operaciones del Daemon.
    Notifica al usuario del cambio de estado.
    """

    def __init__(self, notification_service: NotificationInterface) -> None:
        self.notification_service = notification_service

    async def handle(self, command: PauseDaemonCommand) -> str:
        # El cambio de estado real ocurre en el Daemon, aquí manejamos efectos secundarios (UX)
        self.notification_service.notify("⏸️ v2m pausa", "daemon pausado")
        return "PAUSED"

    def listen_to(self) -> type[Command]:
        return PauseDaemonCommand


class ResumeDaemonHandler(CommandHandler):
    """
    Manejador para reanudar operaciones del Daemon.
    """

    def __init__(self, notification_service: NotificationInterface) -> None:
        self.notification_service = notification_service

    async def handle(self, command: ResumeDaemonCommand) -> str:
        self.notification_service.notify("▶️ v2m resume", "daemon reanudado")
        return "RUNNING"

    def listen_to(self) -> type[Command]:
        return ResumeDaemonCommand
