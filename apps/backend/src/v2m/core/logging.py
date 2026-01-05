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
Configuración de Logging Estructurado (JSON).

Este módulo configura un sistema de logging que emite registros en formato JSON,
facilitando el análisis automatizado, la búsqueda y la agregación de logs en
sistemas de monitoreo modernos.

Características:
    - Formato JSON para cada entrada (machine-readable).
    - Salida a `stdout` (estándar de aplicaciones 12-factor / contenedores).
    - Instancia global pre-configurada.

Formato de salida:
    ```json
    {"asctime": "2024-01-15 10:30:45", "name": "v2m", "levelname": "INFO", "message": "..."}
    ```
"""

import logging as _logging
import sys

from pythonjsonlogger import json


def setup_logging() -> _logging.Logger:
    """
    Configura y retorna un logger estructurado en formato JSON.

    Crea un logger llamado 'v2m' configurado para emitir mensajes de nivel
    INFO o superior a stdout.

    Returns:
        logging.Logger: Instancia configurada. Se recomienda usar la variable global `logger`.
    """
    logger = _logging.getLogger("v2m")
    logger.setLevel(_logging.INFO)

    # Prevenir duplicación de handlers si se recarga el módulo
    if logger.hasHandlers():
        logger.handlers.clear()

    # --- Configuración de Handler y Formatter ---
    # StreamHandler para stdout (compatible con journald/docker)
    handler = _logging.StreamHandler(sys.stdout)
    # JsonFormatter para estructura
    formatter = json.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# --- Instancia Global del Logger ---
# Punto de acceso único para logging en toda la aplicación.
logger = setup_logging()
