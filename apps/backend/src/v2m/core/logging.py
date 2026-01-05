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
    - SOTA 2026: Rename de campos para compatibilidad con OpenTelemetry (time, severity, body).

Formato de salida:
    ```json
    {"time": "2026-01-05T10:30:45Z", "severity": "INFO", "body": "...", "module": "..."}
    ```
"""

import logging as _logging
import sys
import datetime
from typing import Any

from pythonjsonlogger import json


class CustomJsonFormatter(json.JsonFormatter):
    """
    Formatter JSON personalizado para estándares de observabilidad 2026.

    Normaliza los campos para que sean amigables con backends como OpenTelemetry,
    Datadog o CloudWatch sin configuración extra.
    """

    def add_fields(self, log_record: dict[str, Any], record: _logging.LogRecord, message_dict: dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)

        # SOTA: ISO 8601 UTC timestamp
        now = datetime.datetime.now(datetime.timezone.utc)
        log_record['time'] = now.isoformat()

        # SOTA: 'severity' en lugar de 'levelname' (estándar OTel)
        if 'levelname' in log_record:
            log_record['severity'] = log_record['levelname']
            del log_record['levelname']

        # SOTA: 'body' en lugar de 'message'
        if 'message' in log_record:
            log_record['body'] = log_record['message']
            del log_record['message']

        # Contexto útil
        log_record['module'] = record.module
        log_record['line'] = record.lineno


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

    # JsonFormatter con campos base
    formatter = CustomJsonFormatter("%(levelname)s %(message)s %(module)s %(lineno)d")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Evitar propagación al logger root para no duplicar
    logger.propagate = False

    return logger


# --- Instancia Global del Logger ---
# Punto de acceso único para logging en toda la aplicación.
logger = setup_logging()
