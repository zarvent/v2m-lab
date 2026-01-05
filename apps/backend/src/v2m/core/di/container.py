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
Contenedor de Inyección de Dependencias (DI) para Voice2Machine.

Este módulo implementa el patrón de Inyección de Dependencias que conecta
toda la aplicación. Es el único lugar donde las implementaciones concretas
son conocidas y donde se decide qué implementación usar para cada interfaz.

Responsabilidades del Contenedor:
    1. **Instanciar Servicios de Infraestructura**: Crea las implementaciones
       concretas como singletons (WhisperService, GeminiService, etc.).
    2. **Instanciar Handlers de Aplicación**: Crea los Command Handlers
       inyectándoles las dependencias que necesitan.
    3. **Configurar el CommandBus**: Registra todos los handlers para que
       el bus sepa a quién despachar cada tipo de comando.

Beneficios:
    - **Desacoplamiento**: Los handlers dependen de interfaces, no de implementaciones.
    - **Testabilidad**: Es fácil sustituir servicios reales por mocks en los tests.
    - **Configurabilidad**: Cambiar implementaciones (ej. Gemini -> OpenAI)
      solo requiere modificar este archivo o la configuración.

Diagrama de Dependencias:
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

Ejemplo:
    Acceso al contenedor desde otros módulos:

    ```python
    from v2m.core.di.container import container

    bus = container.get_command_bus()
    await bus.dispatch(MiComando())
    ```
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
from v2m.infrastructure.ollama_llm_service import OllamaLLMService

# --- AUTO-REGISTRO DE PROVEEDORES ---
# Los imports fuerzan el registro en los registries globales.
# Esto permite que el container resuelva providers dinámicamente desde config.
from v2m.infrastructure.whisper_transcription_service import WhisperTranscriptionService

# Registrar providers explícitamente (más claro que auto-registro vía decorador)
transcription_registry.register("whisper", WhisperTranscriptionService)
llm_registry.register("local", LocalLLMService)
llm_registry.register("gemini", GeminiLLMService)
llm_registry.register("ollama", OllamaLLMService)


class Container:
    """
    Contenedor de DI que gestiona el ciclo de vida y las dependencias de los objetos.

    El contenedor es instanciado una única vez al inicio de la aplicación
    y proporciona acceso a los servicios configurados durante toda la
    ejecución del programa.

    Atributos:
        transcription_service: Servicio de transcripción (faster-whisper).
        llm_service: Servicio de LLM para refinamiento de texto (Gemini, Local, Ollama).
        notification_service: Adaptador de notificaciones del sistema.
        clipboard_service: Adaptador del portapapeles del sistema.
        start_recording_handler: Handler para el comando StartRecording.
        stop_recording_handler: Handler para el comando StopRecording.
        process_text_handler: Handler para el comando ProcessText.
        command_bus: Bus de comandos configurado con todos los handlers.
    """

    def __init__(self) -> None:
        """
        Inicializa y configura todas las dependencias de la aplicación.

        El proceso de configuración sigue estos pasos:

        1. **Servicios de Infraestructura** (como Singletons):
           Se crean las implementaciones concretas de los servicios.
           Aquí se decide qué implementación usar para cada interfaz.

        2. **Handlers de Aplicación**:
           Se crean los manejadores de comandos inyectándoles las
           dependencias que necesitan para funcionar.

        3. **CommandBus**:
           Se configura el bus registrando todos los handlers para que
           sepa a cuál despachar cada tipo de comando.

        Nota:
            El modelo Whisper se precarga en un hilo de fondo para evitar
            latencia en la primera transcripción. Si falla la precarga,
            se cargará bajo demanda en el primer uso.
        """
        # --- 1. Instanciar Servicios (como Singletons) ---
        # Resolución dinámica desde registries según config.toml

        # --- Selección de backend de transcripción según configuración ---
        transcription_backend = config.transcription.backend
        try:
            TranscriptionClass = transcription_registry.get(transcription_backend)
            self.transcription_service: TranscriptionService = TranscriptionClass()
            logger.info(f"backend de transcripción seleccionado: {transcription_backend}")
        except ProviderNotFoundError as e:
            logger.critical(f"backend de transcripción inválido: {e}")
            raise

        # ThreadPoolExecutor para warmup - libera el GIL mejor que threading.Thread
        # porque permite que el event loop siga procesando durante la carga
        self._warmup_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="warmup")
        self._warmup_future = self._warmup_executor.submit(self._preload_models)

        # --- Selección de backend LLM según configuración ---
        llm_backend = config.llm.backend
        try:
            LLMClass = llm_registry.get(llm_backend)
            self.llm_service: LLMService = LLMClass()
            logger.info(f"backend llm seleccionado: {llm_backend}")
        except ProviderNotFoundError as e:
            logger.critical(f"backend llm inválido: {e}")
            raise

        # Adaptadores de Sistema
        self.notification_service: NotificationInterface = LinuxNotificationService()
        self.clipboard_service: ClipboardInterface = LinuxClipboardAdapter()

        # --- 2. Instanciar Manejadores de Comandos ---
        # Se inyectan las dependencias en el constructor de cada handler
        self.start_recording_handler = StartRecordingHandler(self.transcription_service, self.notification_service)
        self.stop_recording_handler = StopRecordingHandler(
            self.transcription_service, self.notification_service, self.clipboard_service
        )
        self.process_text_handler = ProcessTextHandler(
            self.llm_service, self.notification_service, self.clipboard_service
        )

        # --- 3. Instanciar y Configurar el Bus de Comandos ---
        # El bus de comandos se convierte en el punto de acceso central para
        # ejecutar la lógica de negocio
        self.command_bus = CommandBus()
        self.command_bus.register(self.start_recording_handler)
        self.command_bus.register(self.stop_recording_handler)
        self.command_bus.register(self.process_text_handler)

    def get_command_bus(self) -> CommandBus:
        """
        Proporciona acceso al CommandBus configurado.

        Este es el punto de acceso principal para despachar comandos.
        El bus ya tiene todos los handlers registrados y está listo para usar.

        Returns:
            CommandBus: La instancia única del bus con todos los handlers
            registrados.
        """
        return self.command_bus

    def _preload_models(self) -> None:
        """
        Precarga modelos de ML en segundo plano para reducir latencia del primer uso.

        Se ejecuta en ThreadPoolExecutor para no bloquear el event loop.
        La carga de Whisper involucra:
        - Descarga/verificación del modelo (~1-2GB).
        - Asignación de VRAM en GPU.
        - Compilación de kernels CUDA (primera vez).
        """
        try:
            # Precargar Whisper (el más pesado)
            _ = self.transcription_service.model
            logger.info("✅ whisper precargado correctamente")
        except Exception as e:
            logger.warning(f"⚠️ no se pudo precargar whisper: {e}")

    async def wait_for_warmup(self, timeout: float = 30.0) -> bool:
        """
        Espera a que los modelos terminen de cargar (async-safe).

        Args:
            timeout: Tiempo máximo de espera en segundos.

        Returns:
            bool: True si la carga fue exitosa, False si hubo timeout.
        """
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(loop.run_in_executor(None, self._warmup_future.result), timeout=timeout)
            return True
        except TimeoutError:
            logger.warning(f"timeout de warmup después de {timeout}s")
            return False


# --- Instancia Global del Contenedor ---
# Se crea una única instancia del contenedor que será accesible desde toda la
# aplicación (principalmente desde `main.py`).
container = Container()
