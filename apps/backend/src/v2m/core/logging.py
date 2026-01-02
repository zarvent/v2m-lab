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
CONFIGURACIÓN DE LOGGING ESTRUCTURADO EN FORMATO JSON PARA VOICE2MACHINE

este módulo configura un sistema de logging estructurado que emite
registros en formato json facilitando el análisis automatizado búsqueda
y agregación de logs en sistemas de monitoreo

CARACTERÍSTICAS
    - formato json para cada entrada de log
    - incluye timestamp nivel nombre del logger y mensaje
    - salida a stdout para compatibilidad con systemd journald
    - instancia global pre-configurada para uso en toda la aplicación

FORMATO DE SALIDA
    cada línea es un objeto json independiente::

        {"asctime": "2024-01-15 10:30:45", "name": "v2m", "levelname": "INFO",
         "message": "grabación iniciada"}

USO
    importar el logger global desde cualquier módulo::

        from v2m.core.logging import logger

        logger.info("operación completada")
        logger.error(f"error: {e}")
        logger.debug("datos de depuración")

NOTE
    el nivel por defecto es info los mensajes debug no se mostrarán
    a menos que se modifique el nivel del logger
"""

import logging as _logging
import sys

from pythonjsonlogger import jsonlogger


def setup_logging() -> _logging.Logger:
    """
    CONFIGURA Y RETORNA UN LOGGER ESTRUCTURADO EN FORMATO JSON

    crea un logger nombrado 'v2m' configurado para emitir mensajes de nivel
    info o superior a stdout en formato json si el módulo se importa
    múltiples veces evita duplicar handlers

    el formato json incluye los siguientes campos
        - ``asctime`` timestamp iso del evento
        - ``name`` nombre del logger siempre 'v2m'
        - ``levelname`` nivel del mensaje info warning error etc
        - ``message`` contenido del mensaje de log

    RETURNS:
        una instancia de ``logging.Logger`` configurada y lista para usar
        todos los módulos deberían importar la instancia global ``logger``
        en lugar de llamar esta función directamente

    EXAMPLE
        configuración automática al importar::

            from v2m.core.logging import logger
            logger.info("aplicación iniciada")
    """
    logger = _logging.getLogger("v2m")
    logger.setLevel(_logging.INFO)

    # previene que se añadan múltiples handlers si este módulo se importa más de una vez
    if logger.hasHandlers():
        logger.handlers.clear()

    # --- configuración del handler y el formatter ---
    # se utiliza un streamhandler para enviar logs a stdout
    handler = _logging.StreamHandler(sys.stdout)
    # se usa jsonformatter para asegurar que todos los logs sean objetos json
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

# --- instancia global del logger ---
# se crea una única instancia del logger que será accesible desde toda la
# aplicación asegurando una configuración consistente
logger = setup_logging()
