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
Servicio de Notificaciones de Escritorio para Linux.

Este módulo implementa un servicio de notificaciones robusto que soporta
auto-dismiss (cierre automático) programático vía DBus, resolviendo la limitación
de entornos como GNOME o Unity que a veces ignoran el parámetro `expire-time`.

Arquitectura:
    - Utiliza la especificación FreeDesktop Notifications vía `gdbus` (sin deps externas pesadas).
    - ThreadPoolExecutor Singleton para manejar cierres asíncronos sin fugas de hilos.
    - Fallback automático a `notify-send` si DBus falla.
    - Configuración inyectada desde `config.toml`.
"""

from __future__ import annotations

import atexit
import re
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from time import sleep
from typing import TYPE_CHECKING, ClassVar
from weakref import WeakSet

from v2m.core.interfaces import NotificationInterface
from v2m.core.logging import logger

if TYPE_CHECKING:
    from v2m.config import NotificationsConfig


@dataclass(frozen=True, slots=True)
class NotificationResult:
    """
    Resultado inmutable de enviar una notificación.

    Atributos:
        success: True si la notificación se envió correctamente.
        notification_id: El ID asignado por DBus o None si falló.
        error: Mensaje de error si success es False.
    """

    success: bool
    notification_id: int | None = None
    error: str | None = None


class LinuxNotificationService(NotificationInterface):
    """
    Servicio de notificaciones para Linux con Auto-Dismiss vía DBus.

    Implementa el patrón Singleton para el ThreadPoolExecutor compartido
    entre todas las instancias, garantizando eficiencia de recursos y
    correcta limpieza al finalizar la aplicación.

    Atributos:
        expire_time_ms: Tiempo en ms antes de auto-cerrar.
        auto_dismiss: Si True, fuerza cierre programático vía DBus.
    """

    # --- Recursos Singleton a nivel de clase ---
    _executor: ClassVar[ThreadPoolExecutor | None] = None
    _instances: ClassVar[WeakSet[LinuxNotificationService]] = WeakSet()
    _lock: ClassVar[threading.Lock] = threading.Lock()
    MAX_POOL_SIZE: ClassVar[int] = 4  # Suficiente para ráfagas típicas

    # --- Constantes DBus ---
    _DBUS_DEST: ClassVar[str] = "org.freedesktop.Notifications"
    _DBUS_PATH: ClassVar[str] = "/org/freedesktop/Notifications"
    _DBUS_IFACE: ClassVar[str] = "org.freedesktop.Notifications"

    def __init__(self, config: NotificationsConfig | None = None) -> None:
        """
        Inicializa el servicio con configuración opcional.

        Args:
            config: Configuración de notificaciones. Si es None, se carga
                automáticamente desde la configuración global.
        """
        if config is None:
            from v2m.config import config as app_config

            config = app_config.notifications

        self._expire_time_ms: int = config.expire_time_ms
        self._auto_dismiss: bool = config.auto_dismiss
        self._pending_count: int = 0
        self._pending_lock: threading.Lock = threading.Lock()

        # Registrar instancia para limpieza global
        LinuxNotificationService._instances.add(self)

        # Inicializar executor singleton si no existe
        self._ensure_executor()

    @classmethod
    def _ensure_executor(cls) -> None:
        """
        Inicializa el ThreadPoolExecutor Singleton de forma segura (Thread-Safe).

        Usa patrón Double-Checked Locking para evitar contención innecesaria.
        """
        if cls._executor is None:
            with cls._lock:
                if cls._executor is None:
                    cls._executor = ThreadPoolExecutor(
                        max_workers=cls.MAX_POOL_SIZE, thread_name_prefix="v2m-notify-dismiss"
                    )
                    # Registrar limpieza al salir del proceso
                    atexit.register(cls._shutdown_executor)
                    logger.debug(f"executor de notificaciones inicializado max_workers={cls.MAX_POOL_SIZE}")

    @classmethod
    def _shutdown_executor(cls) -> None:
        """
        Cierra el executor limpiamente esperando tareas pendientes.

        Llamado automáticamente por atexit o manualmente vía shutdown.
        """
        if cls._executor is not None:
            logger.debug("cerrando executor de notificaciones...")
            cls._executor.shutdown(wait=True, cancel_futures=False)
            cls._executor = None
            logger.debug("cierre del executor de notificaciones completado")

    def notify(self, title: str, message: str) -> None:
        """
        Envía una notificación al escritorio con auto-dismiss opcional.

        El método es no bloqueante: el envío y el cierre programado ocurren
        sin detener el flujo principal.

        Args:
            title: Título breve y descriptivo.
            message: Cuerpo del mensaje.
        """
        result = self._send_notification(title, message)

        if result.success and self._auto_dismiss and result.notification_id is not None:
            self._schedule_dismiss(result.notification_id)
        elif not result.success:
            # Fallback a notify-send si DBus falló
            self._send_fallback(title, message)

    def _send_notification(self, title: str, message: str) -> NotificationResult:
        """
        Envía notificación vía DBus y retorna el ID asignado.

        Usa `gdbus` para evitar dependencias de Python adicionales.

        Returns:
            NotificationResult: Objeto con estado e ID/Error.
        """
        try:
            result = subprocess.run(
                [
                    "gdbus",
                    "call",
                    "--session",
                    "--dest",
                    self._DBUS_DEST,
                    "--object-path",
                    self._DBUS_PATH,
                    "--method",
                    f"{self._DBUS_IFACE}.Notify",
                    "v2m",  # app_name
                    "0",  # replaces_id (0 = nueva)
                    "",  # app_icon (vacio = default)
                    title,
                    message,
                    "[]",  # actions
                    "{}",  # hints
                    str(self._expire_time_ms),
                ],
                capture_output=True,
                text=True,
                timeout=2,
            )

            if result.returncode != 0:
                return NotificationResult(success=False, error=f"error de gdbus: {result.stderr.strip()}")

            # Parsear ID de respuesta: "(uint32 123,)"
            match = re.search(r"uint32 (\d+)", result.stdout)
            if match:
                notification_id = int(match.group(1))
                return NotificationResult(success=True, notification_id=notification_id)
            else:
                return NotificationResult(
                    success=False, error=f"falló al parsear id de notificación de: {result.stdout}"
                )

        except FileNotFoundError:
            return NotificationResult(success=False, error="gdbus no encontrado")
        except subprocess.TimeoutExpired:
            return NotificationResult(success=False, error="tiempo de espera gdbus agotado")
        except Exception as e:
            return NotificationResult(success=False, error=str(e))

    def _schedule_dismiss(self, notification_id: int) -> None:
        """
        Programa el cierre de una notificación en el Thread Pool.

        Args:
            notification_id: ID de la notificación a cerrar.
        """
        if self._executor is None:
            logger.warning("executor no disponible, cierre automático omitido")
            return

        with self._pending_lock:
            self._pending_count += 1

        def dismiss_task() -> None:
            try:
                # Esperar el tiempo de expiración
                sleep(self._expire_time_ms / 1000.0)

                # Cerrar la notificación vía DBus
                subprocess.run(
                    [
                        "gdbus",
                        "call",
                        "--session",
                        "--dest",
                        self._DBUS_DEST,
                        "--object-path",
                        self._DBUS_PATH,
                        "--method",
                        f"{self._DBUS_IFACE}.CloseNotification",
                        str(notification_id),
                    ],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=1,
                )
            except Exception:
                pass  # Fallo silencioso si ya fue cerrada
            finally:
                with self._pending_lock:
                    self._pending_count -= 1

        self._executor.submit(dismiss_task)

    def _send_fallback(self, title: str, message: str) -> None:
        """
        Envía notificación usando `notify-send` como fallback.

        Se usa cuando DBus no está disponible o falla. No soporta auto-dismiss
        programático preciso, pero asegura que el usuario vea el mensaje.
        """
        try:
            subprocess.run(
                ["notify-send", f"--expire-time={self._expire_time_ms}", title, message],
                check=False,
                stderr=subprocess.DEVNULL,
                timeout=2,
            )
        except FileNotFoundError:
            logger.warning("notify-send no encontrado, notificación omitida")
        except Exception as e:
            logger.error(f"notificación de fallback falló: {e}")

    @property
    def pending_dismissals(self) -> int:
        """
        Retorna el número de tareas de cierre pendientes.

        Returns:
            int: Cantidad de tareas en cola o ejecución.
        """
        with self._pending_lock:
            return self._pending_count

    def shutdown(self, wait: bool = True) -> None:
        """
        Cierra esta instancia y opcionalmente espera tareas pendientes.

        Args:
            wait: Si True, bloquea hasta que terminen los cierres pendientes
                de esta instancia.
        """
        if wait:
            while self.pending_dismissals > 0:
                sleep(0.1)

    @classmethod
    def shutdown_all(cls) -> None:
        """
        Cierra el Executor Singleton y todas las instancias.

        Usar solo al finalizar la aplicación o en pruebas unitarias.
        """
        cls._shutdown_executor()
