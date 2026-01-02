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
MÓDULO QUE DEFINE LOS COMANDOS ESPECÍFICOS DE LA APLICACIÓN

cada clase en este módulo representa una intención de acción que el sistema
puede realizar estos objetos son despachados por el `commandbus` y no
contienen lógica de negocio solo los datos necesarios para ejecutar la acción
"""

from v2m.core.cqrs.command import Command


class StartRecordingCommand(Command):
    """
    COMANDO PARA INICIAR LA GRABACIÓN DE AUDIO

    este comando no requiere datos adicionales al ser despachado instruye
    al sistema para que comience a capturar audio del micrófono
    """
    pass

class StopRecordingCommand(Command):
    """
    COMANDO PARA DETENER LA GRABACIÓN Y SOLICITAR LA TRANSCRIPCIÓN

    este comando tampoco requiere datos su función es finalizar la grabación
    actual y disparar el proceso de transcripción del audio capturado
    """
    pass

class ProcessTextCommand(Command):
    """
    COMANDO PARA PROCESAR Y REFINAR UN BLOQUE DE TEXTO USANDO UN LLM

    este comando encapsula el texto que necesita ser procesado
    """
    def __init__(self, text: str) -> None:
        """
        INICIALIZA EL COMANDO CON EL TEXTO A PROCESAR

        ARGS:
            text: el texto que será enviado al servicio de llm para su refinamiento
        """
        self.text = text

class UpdateConfigCommand(Command):
    """
    COMANDO PARA ACTUALIZAR LA CONFIGURACIÓN DEL SISTEMA
    """
    def __init__(self, updates: dict) -> None:
        self.updates = updates

class GetConfigCommand(Command):
    """COMANDO PARA OBTENER LA CONFIGURACIÓN ACTUAL"""
    pass

class PauseDaemonCommand(Command):
    """COMANDO PARA PAUSAR EL DAEMON"""
    pass

class ResumeDaemonCommand(Command):
    """COMANDO PARA REANUDAR EL DAEMON"""
    pass
