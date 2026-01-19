
"""
Excepciones Personalizadas del Dominio de Voice2Machine.

Este módulo define la jerarquía de excepciones específicas de la aplicación.
Estas excepciones representan errores de negocio semánticos que permiten un
manejo de errores más granular y claro, desacoplado de las excepciones
técnicas de la infraestructura.

Jerarquía de Excepciones:
    ```
    Exception
    └── ApplicationError (Base)
        ├── MicrophoneNotFoundError
        ├── RecordingError
        ├── TranscriptionError
        └── LLMError
    ```

Beneficios:
    - **Granularidad**: Manejo diferenciado por tipo de error de negocio.
    - **Semántica**: Los nombres describen el problema funcional, no técnico.
    - **Encapsulamiento**: Evita filtrar detalles de implementación (como `OSError` de PortAudio) a capas superiores.
"""


class ApplicationError(Exception):
    """
    Clase base para todas las excepciones de dominio de la aplicación.

    Heredar de una clase base común permite capturar todos los errores de
    negocio conocidos con un solo bloque `except ApplicationError`, diferenciándolos
    de errores inesperados del sistema (bugs, crash).
    """

    pass


class MicrophoneNotFoundError(ApplicationError):
    """
    Excepción lanzada cuando no se detecta ningún micrófono funcional.

    Indica que el dispositivo de entrada de audio predeterminado no está
    disponible o accesible.

    Causas comunes:
        - Micrófono desconectado.
        - Permisos insuficientes (Linux/PulseAudio).
        - Configuración de sistema errónea.
    """

    pass


class RecordingError(ApplicationError):
    """
    Excepción lanzada cuando ocurre un error durante el proceso de grabación.

    Cubre el ciclo de vida de la captura: inicio, flujo de datos y detención.

    Causas comunes:
        - Intento de iniciar grabación concurrente.
        - Fallo del stream de audio (buffer overflow/underflow).
        - Buffer vacío (grabación de duración cero).
    """

    pass


class TranscriptionError(ApplicationError):
    """
    Excepción lanzada cuando falla el proceso de transcripción (Whisper).

    Indica que el audio fue capturado pero la inferencia falló.

    Causas comunes:
        - Modelo corrupto o no encontrado.
        - Memoria VRAM insuficiente (OOM).
        - Error en kernels CUDA (ctranslate2).
    """

    pass


class LLMError(ApplicationError):
    """
    Excepción lanzada cuando falla la comunicación o inferencia con el LLM.

    Encapsula errores de proveedores externos (Gemini) o locales (Ollama/Llama).

    Causas comunes:
        - API Key inválida o cuota excedida.
        - Errores de red o timeout.
        - Respuesta malformada o vacía.
        - Servicio local no disponible.
    """

    pass
