
"""
Definición de Comandos Específicos de la Aplicación.

Cada clase en este módulo representa una intención de acción concreta que el sistema
puede realizar. Estos objetos (DTOs) son despachados por el `CommandBus` y no
contienen lógica de negocio, solo los datos inmutables necesarios para ejecutar la acción.
"""

from v2m.core.cqrs.command import Command


class StartRecordingCommand(Command):
    """
    Comando para iniciar la grabación de audio.

    Instruye al sistema para comenzar la captura de audio del micrófono predeterminado.
    No requiere datos adicionales.
    """

    pass


class StopRecordingCommand(Command):
    """
    Comando para detener la grabación y solicitar la transcripción.

    Finaliza la sesión de grabación actual, procesa el audio capturado con Whisper
    y gestiona el resultado (portapapeles, notificaciones).
    """

    pass


class ProcessTextCommand(Command):
    """
    Comando para procesar y refinar un bloque de texto usando un LLM.

    Utilizado para corrección gramatical, reescritura o formateo de texto existente.
    """

    def __init__(self, text: str) -> None:
        """
        Inicializa el comando.

        Args:
            text: El texto crudo que será enviado al servicio de LLM para su refinamiento.
        """
        self.text = text


class TranslateTextCommand(Command):
    """
    Comando para traducir un bloque de texto usando un LLM.
    """

    def __init__(self, text: str, target_lang: str) -> None:
        """
        Inicializa el comando.

        Args:
            text: El texto original a traducir.
            target_lang: El código del idioma objetivo (ej: "en", "es", "fr").
        """
        self.text = text
        self.target_lang = target_lang


class UpdateConfigCommand(Command):
    """
    Comando para actualizar la configuración del sistema en tiempo de ejecución.
    """

    def __init__(self, updates: dict) -> None:
        """
        Inicializa el comando.

        Args:
            updates: Diccionario con las claves de configuración a modificar y sus nuevos valores.
                     Soporta notación de punto para claves anidadas (ej. "transcription.whisper.model").
        """
        self.updates = updates


class GetConfigCommand(Command):
    """
    Comando para obtener la configuración actual serializable del sistema.
    """

    pass


class PauseDaemonCommand(Command):
    """
    Comando para pausar el funcionamiento del Demonio.

    Evita que el demonio procese nuevas solicitudes de grabación o transcripción
    hasta que sea reanudado. Útil para mantenimiento o evitar conflictos temporales.
    """

    pass


class ResumeDaemonCommand(Command):
    """
    Comando para reanudar el funcionamiento del Demonio previamente pausado.
    """

    pass


class TranscribeFileCommand(Command):
    """
    Comando para transcribir un archivo de audio/video desde el disco.

    Soporta formatos de video (MP4, MOV, MKV) y audio (WAV, MP3, FLAC, M4A).
    Para archivos de video, extrae el audio primero usando FFmpeg.
    """

    def __init__(self, file_path: str) -> None:
        """
        Inicializa el comando.

        Args:
            file_path: Ruta absoluta al archivo a transcribir.
        """
        self.file_path = file_path
