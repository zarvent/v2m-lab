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
contenedor de inyección de dependencias (di) para voice2machine

este módulo implementa el patrón de inyección de dependencias que cablea
toda la aplicación es el único lugar donde las implementaciones concretas
son conocidas y donde se decide qué implementación usar para cada interfaz

responsabilidades del contenedor
    1 **instanciar servicios de infraestructura** crea las implementaciones
       concretas como singletons (whisperservice geminiservice etc)
    2 **instanciar handlers de aplicación** crea los command handlers
       inyectándoles las dependencias que necesitan
    3 **configurar el commandbus** registra todos los handlers para que
       el bus sepa a quién despachar cada tipo de comando

beneficios
    - **desacoplamiento** los handlers dependen de interfaces no implementaciones
    - **testabilidad** fácil sustituir servicios reales por mocks
    - **configurabilidad** cambiar implementaciones (ej gemini -> openai)
      solo requiere modificar este archivo

diagrama de dependencias
    ::

        Container
        ├── VADService
        ├── WhisperTranscriptionService (usa VADService)
        ├── GeminiLLMService
        ├── LinuxNotificationAdapter
        ├── LinuxClipboardAdapter
        ├── StartRecordingHandler (usa Transcription, Notification)
        ├── StopRecordingHandler (usa Transcription, Notification, Clipboard)
        ├── ProcessTextHandler (usa LLM, Notification, Clipboard)
        └── CommandBus (registra todos los handlers)

example
    acceso al contenedor desde otros módulos::

        from v2m.core.di.container import container

        bus = container.get_command_bus()
        await bus.dispatch(MiComando())
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from v2m.application.command_handlers import ProcessTextHandler, StartRecordingHandler, StopRecordingHandler
from v2m.application.llm_service import LLMService
from v2m.application.transcription_service import TranscriptionService
from v2m.config import config
from v2m.core.cqrs.command_bus import CommandBus
from v2m.core.interfaces import ClipboardInterface, NotificationInterface
from v2m.core.logging import logger
from v2m.core.providers import ProviderNotFoundError, llm_registry, transcription_registry
from v2m.infrastructure.gemini_llm_service import GeminiLLMService
from v2m.infrastructure.linux_adapters import LinuxClipboardAdapter
from v2m.infrastructure.local_llm_service import LocalLLMService
from v2m.infrastructure.notification_service import LinuxNotificationService

# --- AUTO-REGISTRO DE PROVIDERS ---
# los imports fuerzan el registro en los registries globales
# esto permite que el container resuelva providers dinámicamente desde config
from v2m.infrastructure.whisper_transcription_service import WhisperTranscriptionService

# registrar providers explícitamente (más claro que auto-registro vía decorador)
transcription_registry.register("whisper", WhisperTranscriptionService)
llm_registry.register("local", LocalLLMService)
llm_registry.register("gemini", GeminiLLMService)

class Container:
    """
    contenedor de di que gestiona el ciclo de vida y dependencias de objetos

    el contenedor es instanciado una única vez al inicio de la aplicación
    y proporciona acceso a los servicios configurados durante toda la
    ejecución del programa

    attributes:

        transcription_service: servicio de transcripción (faster-whisper)
        llm_service: servicio de llm para refinamiento de texto (gemini)
        notification_service: adaptador de notificaciones del sistema
        clipboard_service: adaptador del portapapeles del sistema
        start_recording_handler: handler para el comando startrecording
        stop_recording_handler: handler para el comando stoprecording
        process_text_handler: handler para el comando processtext
        command_bus: bus de comandos configurado con todos los handlers

    example
        uso típico (ya pre-instanciado como singleton global)::

            from v2m.core.di.container import container

            # obtener el bus de comandos
            bus = container.get_command_bus()

            # acceso directo a servicios (menos común)
            transcription = container.transcription_service
    """
    def __init__(self) -> None:
        """
        inicializa y configura todas las dependencias de la aplicación

        el proceso de configuración sigue estos pasos

        1 **servicios de infraestructura** (como singletons)
           se crean las implementaciones concretas de los servicios
           aquí se decide qué implementación usar para cada interfaz
           por ejemplo para cambiar de gemini a openai solo se modificaría
           esta línea

        2 **handlers de aplicación**
           se crean los manejadores de comandos inyectándoles las
           dependencias que necesitan para funcionar

        3 **commandbus**
           se configura el bus registrando todos los handlers para que
           sepa a cuál despachar cada tipo de comando

        note
            el modelo whisper se precarga en un hilo de fondo para evitar
            latencia en la primera transcripción si falla la precarga
            se cargará de forma lazy en el primer uso
        """
        # --- 1 instanciar servicios (como singletons) ---
        # resolución dinámica desde registries según config.toml


        # --- selección de backend de transcripción según configuración ---
        transcription_backend = config.transcription.backend
        try:
            TranscriptionClass = transcription_registry.get(transcription_backend)
            self.transcription_service: TranscriptionService = TranscriptionClass()
            logger.info(f"transcription backend: {transcription_backend}")
        except ProviderNotFoundError as e:
            logger.critical(f"backend de transcripción inválido: {e}")
            raise

        # threadpoolexecutor para warmup - libera el gil mejor que threading.thread
        # porque permite que el event loop siga procesando durante la carga
        self._warmup_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="warmup")
        self._warmup_future = self._warmup_executor.submit(self._preload_models)

        # --- selección de backend LLM según configuración ---
        llm_backend = config.llm.backend
        try:
            LLMClass = llm_registry.get(llm_backend)
            self.llm_service: LLMService = LLMClass()
            logger.info(f"llm backend: {llm_backend}")
        except ProviderNotFoundError as e:
            logger.critical(f"backend llm inválido: {e}")
            raise

        # adaptadores de sistema
        self.notification_service: NotificationInterface = LinuxNotificationService()
        self.clipboard_service: ClipboardInterface = LinuxClipboardAdapter()

        # --- 2 instanciar manejadores de comandos ---
        # se inyectan las dependencias en el constructor de cada handler
        self.start_recording_handler = StartRecordingHandler(
            self.transcription_service,
            self.notification_service
        )
        self.stop_recording_handler = StopRecordingHandler(
            self.transcription_service,
            self.notification_service,
            self.clipboard_service
        )
        self.process_text_handler = ProcessTextHandler(
            self.llm_service,
            self.notification_service,
            self.clipboard_service
        )

        # --- 3 instanciar y configurar el bus de comandos ---
        # el bus de comandos se convierte en el punto de acceso central para
        # ejecutar la lógica de negocio
        self.command_bus = CommandBus()
        self.command_bus.register(self.start_recording_handler)
        self.command_bus.register(self.stop_recording_handler)
        self.command_bus.register(self.process_text_handler)

    def get_command_bus(self) -> CommandBus:
        """
        proporciona acceso al commandbus configurado

        este es el punto de acceso principal para despachar comandos
        el bus ya tiene todos los handlers registrados y está listo para usar

        returns:
            la instancia única del commandbus con todos los handlers
            registrados usar esta instancia para despachar comandos
            desde cualquier parte de la aplicación

        example
            despachar un comando::

                bus = container.get_command_bus()
                await bus.dispatch(StartRecordingCommand())
        """
        return self.command_bus

    def _preload_models(self) -> None:
        """
        precarga modelos de ml en background para reducir latencia del primer uso

        ejecuta en threadpoolexecutor para no bloquear el event loop
        la carga de whisper involucra
        - descarga/verificación del modelo (~1-2gb)
        - allocación de vram en gpu
        - compilación de kernels cuda (primera vez)
        """
        try:
            # precargar whisper (el más pesado)
            _ = self.transcription_service.model
            logger.info("✅ whisper precargado correctamente")
        except Exception as e:
            logger.warning(f"⚠️ no se pudo precargar whisper: {e}")



    async def wait_for_warmup(self, timeout: float = 30.0) -> bool:
        """
        espera a que los modelos terminen de cargar (async-safe)

        args:
            timeout: tiempo máximo de espera en segundos

        returns:
            true si la carga fue exitosa false si hubo timeout
        """
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, self._warmup_future.result),
                timeout=timeout
            )
            return True
        except asyncio.TimeoutError:
            logger.warning(f"timeout de warmup después de {timeout}s")
            return False

# --- instancia global del contenedor ---
# se crea una única instancia del contenedor que será accesible desde toda la
# aplicación (principalmente desde `main.py`)
container = Container()
