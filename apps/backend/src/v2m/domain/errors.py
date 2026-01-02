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
EXCEPCIONES PERSONALIZADAS DEL DOMINIO DE VOICE2MACHINE

este módulo define la jerarquía de excepciones específicas de la aplicación
estas excepciones representan errores de negocio semánticos que permiten un
manejo de errores más granular y claro que las excepciones genéricas

JERARQUÍA DE EXCEPCIONES
    ::

        Exception
        └── ApplicationError base para todas las excepciones de v2m
            ├── MicrophoneNotFoundError
            ├── RecordingError
            ├── TranscriptionError
            └── LLMError

BENEFICIOS DE EXCEPCIONES PERSONALIZADAS
    - **granularidad** manejo diferenciado por tipo de error
    - **semántica** los nombres describen el problema de negocio
    - **encapsulamiento** no filtran detalles de infraestructura
    - **captura grupal** ``except ApplicationError`` captura todos

EXAMPLE
    manejo de errores en un handler::

        from v2m.domain.errors import TranscriptionError, LLMError

        try:
            transcription = service.transcribe(audio)
        except TranscriptionError as e:
            logger.error(f"fallo en transcripción: {e}")
            notification.notify("❌ error", "no se pudo transcribir")
"""

class ApplicationError(Exception):
    """
    CLASE BASE PARA TODAS LAS EXCEPCIONES PERSONALIZADAS DE LA APLICACIÓN

    heredar de una clase base común permite capturar todos los errores de
    negocio conocidos con un solo bloque ``except ApplicationError``
    mientras se dejan pasar errores inesperados del sistema

    EXAMPLE
        captura genérica de errores de aplicación::

            try:
                await handler.execute(command)
            except ApplicationError as e:
                # error conocido de negocio
                return f"error: {e}"
            except Exception as e:
                # error inesperado del sistema
                logger.critical(f"error no manejado: {e}")
                raise
    """
    pass

class MicrophoneNotFoundError(ApplicationError):
    """
    EXCEPCIÓN LANZADA CUANDO NO SE DETECTA NINGÚN MICRÓFONO FUNCIONAL

    esta excepción indica que el dispositivo de grabación de audio por defecto
    no está disponible no está conectado o no está configurado correctamente
    en el sistema operativo

    CAUSAS COMUNES
        - micrófono usb desconectado
        - permisos insuficientes para acceder al dispositivo de audio
        - dispositivo de entrada por defecto mal configurado en pulseaudio alsa
        - driver de audio no cargado

    SOLUCIÓN SUGERIDA
        verificar con ``pactl list sources`` o ``arecord -l`` que el
        micrófono esté visible para el sistema
    """
    pass

class RecordingError(ApplicationError):
    """
    EXCEPCIÓN LANZADA CUANDO OCURRE UN ERROR DURANTE LA GRABACIÓN DE AUDIO

    cubre errores relacionados con la captura de audio desde el inicio
    de la grabación hasta la obtención de los datos del buffer

    CAUSAS COMUNES
        - intento de iniciar una grabación cuando ya hay una en progreso
        - intento de detener cuando no hay grabación activa
        - fallo del stream de sounddevice
        - buffer de audio vacío grabación de duración cero
        - permisos de acceso al dispositivo de audio revocados

    ATRIBUTOS HEREDADOS
        args[0] mensaje descriptivo del error específico
    """
    pass

class TranscriptionError(ApplicationError):
    """
    EXCEPCIÓN LANZADA CUANDO FALLA EL PROCESO DE TRANSCRIPCIÓN

    indica un problema durante la conversión de audio a texto usando el
    modelo whisper el audio ya fue capturado exitosamente pero no pudo
    ser procesado

    CAUSAS COMUNES
        - modelo whisper corrupto o no descargado completamente
        - memoria gpu insuficiente para cargar el modelo
        - formato de audio inválido o corrupto
        - error de ctranslate2 cuda durante la inferencia
        - timeout en la transcripción audio demasiado largo

    DIAGNÓSTICO
        verificar logs para el mensaje de error específico de faster-whisper
        o ctranslate2
    """
    pass

class LLMError(ApplicationError):
    """
    EXCEPCIÓN LANZADA CUANDO HAY UN ERROR EN LA COMUNICACIÓN CON EL LLM

    encapsula errores relacionados con el servicio de modelo de lenguaje
    actualmente google gemini incluyendo problemas de red autenticación
    y límites de uso

    CAUSAS COMUNES
        - api key inválida expirada o sin permisos
        - error de red o timeout en la conexión
        - rate limiting demasiadas solicitudes
        - respuesta vacía o malformada del servicio
        - servicio de gemini no disponible

    NOTE
        el sistema tiene un fallback que si falla el llm copia el texto
        original sin refinar al portapapeles

    DIAGNÓSTICO
        verificar que ``gemini_api_key`` esté correctamente configurada en
        el archivo ``.env`` y que la cuenta tenga créditos disponibles
    """
    pass
