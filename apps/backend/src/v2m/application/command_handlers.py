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

Los handlers son el corazón de la lógica de aplicación. Cada handler se suscribe
a un tipo de comando específico y ejecuta las acciones correspondientes cuando
ese comando es despachado por el Command Bus.

Este enfoque, inspirado en CQRS (Command Query Responsibility Segregation),
permite un bajo acoplamiento entre el punto de entrada de la aplicación y la
lógica de negocio real.
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

# Executor dedicado para operaciones de ML (Single Worker).
# Evita la contención de GPU y es más eficiente que el ThreadPoolExecutor
# predeterminado para tareas intensivas en cómputo.
_ml_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ml-inference")
atexit.register(_ml_executor.shutdown, wait=True)


class StartRecordingHandler(CommandHandler):
    """
    Manejador para el comando `StartRecordingCommand`.

    Este handler interactúa con el servicio de transcripción para iniciar
    el proceso de grabación de audio y notifica al usuario.
    """

    def __init__(
        self, transcription_service: TranscriptionService, notification_service: NotificationInterface
    ) -> None:
        """
        Inicializa el handler con sus dependencias.

        Args:
            transcription_service: Servicio responsable de grabación y transcripción.
            notification_service: Servicio para enviar notificaciones al usuario.
        """
        self.transcription_service = transcription_service
        self.notification_service = notification_service

    async def handle(self, command: StartRecordingCommand) -> None:
        """
        Ejecuta la lógica para iniciar la grabación.

        Se ejecuta en un hilo separado para no bloquear el Event Loop principal
        si la inicialización del dispositivo de audio toma tiempo.
        """
        await asyncio.to_thread(self.transcription_service.start_recording)

        # Crear bandera de grabación para que scripts externos (Bash) sepan el estado.
        config.paths.recording_flag.touch()

        self.notification_service.notify("🎤 voice2machine", "grabación iniciada...")

    def listen_to(self) -> type[Command]:
        """Se suscribe al tipo de comando `StartRecordingCommand`."""
        return StartRecordingCommand


class StopRecordingHandler(CommandHandler):
    """
    Manejador para el comando `StopRecordingCommand`.

    Este handler detiene la grabación, obtiene la transcripción del audio,
    la copia al portapapeles y notifica al usuario del resultado.
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
            transcription_service: Servicio responsable de grabación y transcripción.
            notification_service: Servicio para enviar notificaciones al usuario.
            clipboard_service: Servicio para interactuar con el portapapeles.
        """
        self.transcription_service = transcription_service
        self.notification_service = notification_service
        self.clipboard_service = clipboard_service

    async def handle(self, command: StopRecordingCommand) -> str | None:
        """
        Ejecuta la lógica para detener la grabación y transcribir.

        Notifica al usuario durante el procesamiento y maneja el caso donde
        no se detecta voz en el audio. Utiliza un executor dedicado para la inferencia.

        Returns:
            str | None: El texto transcrito o None si no se detectó voz.
        """
        # Eliminar bandera de grabación.
        if config.paths.recording_flag.exists():
            config.paths.recording_flag.unlink()

        self.notification_service.notify("⚡ v2m procesando", "procesando...")

        # Usar executor dedicado para ML - evita contención con otras tareas async
        loop = asyncio.get_running_loop()
        transcription = await loop.run_in_executor(_ml_executor, self.transcription_service.stop_and_transcribe)

        # Si la transcripción está vacía no tiene sentido copiarla
        if not transcription.strip():
            self.notification_service.notify("❌ whisper", "no se detectó voz en el audio")
            return None

        self.clipboard_service.copy(transcription)
        preview = transcription[:80]  # Vista previa para la notificación
        self.notification_service.notify("✅ whisper - copiado", f"{preview}...")
        return transcription

    def listen_to(self) -> type[Command]:
        """Se suscribe al tipo de comando `StopRecordingCommand`."""
        return StopRecordingCommand


class ProcessTextHandler(CommandHandler):
    """
    Manejador para el comando `ProcessTextCommand`.

    Utiliza un servicio de LLM (Large Language Model) para procesar y refinar
    un texto dado. El resultado se copia al portapapeles.
    """

    def __init__(
        self,
        llm_service: LLMService,
        notification_service: NotificationInterface,
        clipboard_service: ClipboardInterface,
    ) -> None:
        """
        Inicializa el handler con sus dependencias.

        Args:
            llm_service: Servicio que interactúa con el LLM (ej. Gemini, Ollama).
            notification_service: Servicio para enviar notificaciones.
            clipboard_service: Servicio para interactuar con el portapapeles.
        """
        self.llm_service = llm_service
        self.notification_service = notification_service
        self.clipboard_service = clipboard_service

    async def handle(self, command: ProcessTextCommand) -> str | None:
        """
        Ejecuta la lógica para procesar el texto con el LLM.

        Returns:
            str | None: El texto refinado o el original si hubo error (con notificación).
        """
        try:
            # Soporte dual para implementaciones síncronas y asíncronas de LLMService
            if asyncio.iscoroutinefunction(self.llm_service.process_text):
                refined_text = await self.llm_service.process_text(command.text)
            else:
                refined_text = await asyncio.to_thread(self.llm_service.process_text, command.text)

            self.clipboard_service.copy(refined_text)
            backend_name = config.llm.backend  # "local", "gemini", "ollama"
            self.notification_service.notify(f"✅ {backend_name} - copiado", f"{refined_text[:80]}...")
            return refined_text

        except Exception:
            # Fallback: si falla el LLM, copiamos el texto original para no perder datos
            backend_name = config.llm.backend
            self.notification_service.notify(f"⚠️ {backend_name} falló", "usando texto original...")
            self.clipboard_service.copy(command.text)
            self.notification_service.notify("✅ whisper - copiado (crudo)", f"{command.text[:80]}...")
            return command.text

    def listen_to(self) -> type[Command]:
        """Se suscribe al tipo de comando `ProcessTextCommand`."""
        return ProcessTextCommand


class TranslateTextHandler(CommandHandler):
    """
    Manejador para el comando `TranslateTextCommand`.

    Utiliza un servicio de LLM para traducir texto a un idioma objetivo.
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
        Ejecuta la lógica para traducir el texto.

        Valida el idioma de destino para prevenir inyección de prompts.
        """
        # Validar target_lang para prevenir inyecciones
        if not re.match(r"^[a-zA-Z\s\-]{2,20}$", command.target_lang):
            logger.warning(f"Intento de traducción con idioma inválido: {command.target_lang}")
            self.notification_service.notify("❌ Error", "Idioma de destino inválido")
            return None

        try:
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

    Transforma el formato del frontend (esquema plano) al formato TOML (esquema anidado)
    antes de guardar.
    Frontend: whisper.model -> Backend: transcription.whisper.model
    """

    def __init__(self, config_manager: ConfigManager, notification_service: NotificationInterface) -> None:
        self.config_manager = config_manager
        self.notification_service = notification_service

    async def handle(self, command: UpdateConfigCommand) -> dict:
        updates = command.updates

        # Transformar esquema frontend a estructura TOML
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

        # Usar estructura transformada si hubo cambios, sino usar original
        final_updates = toml_updates if toml_updates else updates

        self.config_manager.update_config(final_updates)
        self.notification_service.notify("⚙️ v2m config", "configuración actualizada")
        return {"status": "ok", "message": "config updated, restart may be required"}

    def listen_to(self) -> type[Command]:
        return UpdateConfigCommand


class GetConfigHandler(CommandHandler):
    """
    Manejador para `GetConfigCommand`.

    Transforma la estructura de `config.toml` al formato esperado por el frontend.
    Backend: transcription.whisper.model -> Frontend: whisper.model
    """

    def __init__(self, config_manager: ConfigManager) -> None:
        self.config_manager = config_manager

    async def handle(self, command: GetConfigCommand) -> dict:
        raw = self.config_manager.load_config()

        # Transformar estructura TOML a esquema esperado por frontend
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
    """Manejador para pausar el Daemon."""

    def __init__(self, notification_service: NotificationInterface) -> None:
        self.notification_service = notification_service

    async def handle(self, command: PauseDaemonCommand) -> str:
        # La lógica de estado real se maneja en el Daemon, este handler es para efectos secundarios (UI)
        self.notification_service.notify("⏸️ v2m pausa", "daemon pausado")
        return "PAUSED"

    def listen_to(self) -> type[Command]:
        return PauseDaemonCommand


class ResumeDaemonHandler(CommandHandler):
    """Manejador para reanudar el Daemon."""

    def __init__(self, notification_service: NotificationInterface) -> None:
        self.notification_service = notification_service

    async def handle(self, command: ResumeDaemonCommand) -> str:
        self.notification_service.notify("▶️ v2m resume", "daemon reanudado")
        return "RUNNING"

    def listen_to(self) -> type[Command]:
        return ResumeDaemonCommand
