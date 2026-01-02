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
voice2machine (v2m) - Sistema de dictado por voz para Linux.

Este paquete proporciona una solución completa de dictado por voz que convierte
audio en texto utilizando el modelo Whisper de OpenAI ejecutándose localmente en GPU.
Opcionalmente, el texto puede ser refinado mediante un modelo de lenguaje grande (LLM)
como Google Gemini.

Arquitectura:
    El proyecto sigue una arquitectura limpia basada en el patrón CQRS
    (Command Query Responsibility Segregation) con inyección de dependencias:

    - **core/**: Interfaces, protocolos IPC y el bus de comandos (CQRS).
    - **application/**: Casos de uso y servicios de aplicación (handlers).
    - **domain/**: Errores de dominio y entidades del negocio.
    - **infrastructure/**: Implementaciones concretas (Whisper, Gemini, Linux).

Componentes principales:
    - **Daemon**: Proceso persistente que mantiene el modelo Whisper en memoria.
    - **Client**: Cliente CLI que envía comandos al daemon vía socket Unix.
    - **AudioRecorder**: Captura de audio usando sounddevice.
    - **WhisperTranscriptionService**: Transcripción con faster-whisper.
    - **GeminiLLMService**: Refinamiento de texto con Google Gemini.

Flujo típico de uso:
    1. El usuario presiona un atajo de teclado global.
    2. El script bash envía ``START_RECORDING`` al daemon.
    3. El daemon comienza a capturar audio del micrófono.
    4. Al presionar el atajo nuevamente, se envía ``STOP_RECORDING``.
    5. El audio es transcrito con Whisper y copiado al portapapeles.

Ejemplo:
    Iniciar el daemon::

        python -m v2m.main --daemon

    Enviar comandos desde otro proceso::

        python -m v2m.main START_RECORDING
        python -m v2m.main STOP_RECORDING

Notas:
    - Requiere Linux con X11 o Wayland.
    - Requiere xclip o wl-clipboard para el portapapeles.
    - Requiere notify-send para notificaciones.
    - GPU NVIDIA con CUDA recomendada para mejor rendimiento.

Versión: 1.0.0
Autor: zarvent
Licencia: MIT
"""

__version__ = "1.0.0"
__author__ = "zarvent"
__license__ = "MIT"

# Exportaciones públicas del paquete
__all__ = [
    "__author__",
    "__license__",
    "__version__",
]
