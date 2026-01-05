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
Servicio Gestor de Configuración (Config Manager).

Gestiona la lectura y escritura del archivo de configuración global `config.toml`.
Permite actualizaciones en tiempo real desde el frontend, asegurando la integridad
del formato TOML.

Advertencia:
    Modificar la configuración en caliente requiere precaución. Este servicio
    valida que el resultado sea un TOML válido antes de guardar.
"""

import logging
from pathlib import Path
from typing import Any

import toml

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Gestor de configuración para `config.toml`.
    Actúa como una fachada para las operaciones de E/S de configuración.
    """

    def __init__(self, config_path: str = "config.toml") -> None:
        """
        Inicializa el gestor de configuración.

        Args:
            config_path: Ruta relativa o absoluta al archivo de configuración.
        """
        self.config_path = Path(config_path)
        if not self.config_path.is_absolute():
            # Resolver ruta relativa al directorio raíz del backend
            # (4 niveles arriba desde este archivo: src/v2m/application/config_manager.py -> apps/backend)
            module_dir = Path(__file__).parent.parent.parent.parent
            self.config_path = module_dir / config_path

        logger.info("gestor de configuración inicializado", extra={"ruta": str(self.config_path)})

    def load_config(self) -> dict[str, Any]:
        """
        Lee la configuración actual del disco.

        Returns:
            dict: Diccionario con la configuración cargada.
        """
        try:
            return toml.load(self.config_path)
        except Exception:
            logger.error(f"fallo al cargar configuración desde {self.config_path}", exc_info=True)
            raise

    def update_config(self, new_config: dict[str, Any]) -> None:
        """
        Actualiza el archivo de configuración con nuevos valores.
        Realiza un merge profundo simple (sobrescribe claves existentes).

        Args:
            new_config: Diccionario parcial o completo con nuevas configuraciones.

        Raises:
            ValueError: Si new_config no es un diccionario válido.
            Exception: Si falla la serialización TOML o escritura.
        """
        # Validar estructura básica antes de procesar
        if not isinstance(new_config, dict):
            raise ValueError("Las actualizaciones deben ser un diccionario")

        try:
            current_config = self.load_config()

            # Merge recursivo simple
            self._deep_update(current_config, new_config)

            # Validar integridad TOML antes de escribir (Rollback implícito si falla dump)
            try:
                toml.dumps(current_config)
            except Exception as e:
                logger.error("configuración actualizada no es toml válido, revirtiendo", exc_info=True)
                raise ValueError(f"Estructura TOML inválida tras el merge: {e}")

            with open(self.config_path, "w") as f:
                toml.dump(current_config, f)

            logger.info("configuración actualizada exitosamente")

        except Exception:
            logger.error("fallo al actualizar configuración", exc_info=True)
            raise

    def _deep_update(self, target: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
        """Actualiza recursivamente un diccionario anidado."""
        for key, value in updates.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
        return target
