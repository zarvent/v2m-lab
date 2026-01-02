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
SERVICIO DE NOTIFICACIONES DE ESCRITORIO PARA LINUX

este módulo implementa un servicio de notificaciones robusto que soporta
auto-dismiss programático via dbus resolviendo la limitación de unity o gnome
que ignora el parámetro expire-time de notify-send

ARQUITECTURA:
    - usa freedesktop notifications spec via gdbus sin dependencias externas
    - thread pool executor singleton para manejar cierres sin fugas de hilos
    - fallback automático a notify-send si dbus falla
    - configuración inyectada desde config.toml

EXAMPLE:
    uso básico::

        from v2m.infrastructure.notification_service import LinuxNotificationService

        service = LinuxNotificationService()
        service.notify("✅ éxito", "operación completada")
        # la notificación se cerrará automáticamente después de expire_time_ms

    limpieza al finalizar::

        service.shutdown()  # espera a que terminen los cierres pendientes

NOTE:
    este servicio es seguro para hilos y puede usarse desde múltiples hilos
    simultáneamente sin problemas de concurrencia
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
    RESULTADO INMUTABLE DE ENVIAR UNA NOTIFICACIÓN

    ATTRIBUTES:
        success: true si la notificación se envió correctamente
        notification_id: el id asignado por dbus o none si falló
        error: mensaje de error si success es false
    """
    success: bool
    notification_id: int | None = None
    error: str | None = None


class LinuxNotificationService(NotificationInterface):
    """
    SERVICIO DE NOTIFICACIONES PARA LINUX CON AUTO-DISMISS VIA DBUS

    implementa el patrón singleton para el thread pool executor compartido
    entre todas las instancias garantizando eficiencia de recursos y
    correcta limpieza al finalizar la aplicación

    ATTRIBUTES:
        expire_time_ms: tiempo en ms antes de auto-cerrar de config
        auto_dismiss: si true fuerza cierre via dbus de config

    CLASS ATTRIBUTES:
        _executor: thread pool compartido entre instancias
        _instances: referencias débiles a instancias activas para apagado
        _lock: mutex para inicialización segura de hilos del executor
        MAX_POOL_SIZE: máximo de hilos para cierres concurrentes

    EXAMPLE:
        inyección de dependencias en un manejador::

            class MyHandler:
                def __init__(self, notifier: NotificationInterface):
                    self.notifier = notifier

                def execute(self):
                    self.notifier.notify("🎤 grabando", "grabación iniciada")
    """

    # --- recursos singleton a nivel de clase ---
    _executor: ClassVar[ThreadPoolExecutor | None] = None
    _instances: ClassVar[WeakSet[LinuxNotificationService]] = WeakSet()
    _lock: ClassVar[threading.Lock] = threading.Lock()
    MAX_POOL_SIZE: ClassVar[int] = 4  # suficiente para ráfaga de notificaciones

    # --- constantes dbus ---
    _DBUS_DEST: ClassVar[str] = "org.freedesktop.Notifications"
    _DBUS_PATH: ClassVar[str] = "/org/freedesktop/Notifications"
    _DBUS_IFACE: ClassVar[str] = "org.freedesktop.Notifications"

    def __init__(self, config: NotificationsConfig | None = None) -> None:
        """
        INICIALIZA EL SERVICIO CON CONFIGURACIÓN OPCIONAL

        ARGS:
            config: configuración de notificaciones si none se carga
                automáticamente desde config.toml
        """
        if config is None:
            from v2m.config import config as app_config
            config = app_config.notifications

        self._expire_time_ms: int = config.expire_time_ms
        self._auto_dismiss: bool = config.auto_dismiss
        self._pending_count: int = 0
        self._pending_lock: threading.Lock = threading.Lock()

        # registrar instancia para limpieza global
        LinuxNotificationService._instances.add(self)

        # inicializar executor singleton si no existe
        self._ensure_executor()

    @classmethod
    def _ensure_executor(cls) -> None:
        """
        INICIALIZA EL THREAD POOL EXECUTOR SINGLETON SEGURO PARA HILOS

        usa patrón double-checked locking para evitar contención
        innecesaria después de la primera inicialización
        """
        if cls._executor is None:
            with cls._lock:
                if cls._executor is None:
                    cls._executor = ThreadPoolExecutor(
                        max_workers=cls.MAX_POOL_SIZE,
                        thread_name_prefix="v2m-notify-dismiss"
                    )
                    # registrar limpieza al salir del proceso
                    atexit.register(cls._shutdown_executor)
                    logger.debug(f"executor de notificaciones inicializado max_workers={cls.MAX_POOL_SIZE}")

    @classmethod
    def _shutdown_executor(cls) -> None:
        """
        CIERRA EL EXECUTOR LIMPIAMENTE ESPERANDO TAREAS PENDIENTES

        llamado automáticamente por atexit o manualmente via shutdown
        """
        if cls._executor is not None:
            logger.debug("cerrando executor de notificaciones...")
            cls._executor.shutdown(wait=True, cancel_futures=False)
            cls._executor = None
            logger.debug("cierre del executor de notificaciones completado")

    def notify(self, title: str, message: str) -> None:
        """
        ENVÍA UNA NOTIFICACIÓN AL ESCRITORIO CON AUTO-DISMISS OPCIONAL

        el método es no bloqueante la notificación se envía y el cierre
        se programa en segundo plano sin bloquear al invocador

        ARGS:
            title: título de la notificación breve y descriptivo
            message: cuerpo del mensaje máx 100 caracteres recomendado

        NOTE:
            si auto_dismiss está habilitado y dbus funciona el cierre
            se ejecuta después de expire_time_ms en un hilo del pool
        """
        result = self._send_notification(title, message)

        if result.success and self._auto_dismiss and result.notification_id is not None:
            self._schedule_dismiss(result.notification_id)
        elif not result.success:
            # fallback a notify-send si dbus falló
            self._send_fallback(title, message)

    def _send_notification(self, title: str, message: str) -> NotificationResult:
        """
        ENVÍA NOTIFICACIÓN VIA DBUS Y RETORNA EL ID DE NOTIFICACIÓN

        usa gdbus para evitar dependencias python adicionales
        gdbus viene preinstalado en ubuntu debian fedora

        ARGS:
            title: título de la notificación
            message: cuerpo del mensaje

        RETURNS:
            notificationresult con success=true y notification_id si ok
            notificationresult con success=false y error si falló
        """
        try:
            result = subprocess.run(
                [
                    "gdbus", "call",
                    "--session",
                    "--dest", self._DBUS_DEST,
                    "--object-path", self._DBUS_PATH,
                    "--method", f"{self._DBUS_IFACE}.Notify",
                    "v2m",  # app_name
                    "0",    # replaces_id (0 = nueva notificación)
                    "",     # app_icon (empty = usar default)
                    title,
                    message,
                    "[]",   # actions
                    "{}",   # hints
                    str(self._expire_time_ms)
                ],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode != 0:
                return NotificationResult(
                    success=False,
                    error=f"error de gdbus: {result.stderr.strip()}"
                )

            # parsear id de respuesta: "(uint32 123,)"
            match = re.search(r'uint32 (\d+)', result.stdout)
            if match:
                notification_id = int(match.group(1))
                return NotificationResult(success=True, notification_id=notification_id)
            else:
                return NotificationResult(
                    success=False,
                    error=f"falló al parsear id de notificación de: {result.stdout}"
                )

        except FileNotFoundError:
            return NotificationResult(success=False, error="gdbus no encontrado")
        except subprocess.TimeoutExpired:
            return NotificationResult(success=False, error="tiempo de espera gdbus agotado")
        except Exception as e:
            return NotificationResult(success=False, error=str(e))

    def _schedule_dismiss(self, notification_id: int) -> None:
        """
        PROGRAMA EL CIERRE DE UNA NOTIFICACIÓN EN EL THREAD POOL

        ARGS:
            notification_id: id de la notificación a cerrar

        NOTE:
            usa el executor singleton para evitar creación de hilos
            por notificación lo que causaría fugas de hilos
        """
        if self._executor is None:
            logger.warning("executor no disponible cierre omitido")
            return

        with self._pending_lock:
            self._pending_count += 1

        def dismiss_task() -> None:
            try:
                # esperar el tiempo de expiración
                sleep(self._expire_time_ms / 1000.0)

                # cerrar la notificación via dbus
                subprocess.run(
                    [
                        "gdbus", "call",
                        "--session",
                        "--dest", self._DBUS_DEST,
                        "--object-path", self._DBUS_PATH,
                        "--method", f"{self._DBUS_IFACE}.CloseNotification",
                        str(notification_id)
                    ],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=1
                )
            except Exception:
                pass  # fallo silencioso si la notificación ya fue cerrada
            finally:
                with self._pending_lock:
                    self._pending_count -= 1

        self._executor.submit(dismiss_task)

    def _send_fallback(self, title: str, message: str) -> None:
        """
        ENVÍA NOTIFICACIÓN USANDO NOTIFY-SEND COMO FALLBACK

        se usa cuando dbus no está disponible o falla el notify
        no soporta auto-dismiss pero al menos muestra la notificación

        ARGS:
            title: título de la notificación
            message: cuerpo del mensaje
        """
        try:
            subprocess.run(
                [
                    "notify-send",
                    f"--expire-time={self._expire_time_ms}",
                    title,
                    message
                ],
                check=False,
                stderr=subprocess.DEVNULL,
                timeout=2
            )
        except FileNotFoundError:
            logger.warning("notify-send no encontrado notificación omitida")
        except Exception as e:
            logger.error(f"notificación de fallback falló: {e}")

    @property
    def pending_dismissals(self) -> int:
        """
        RETORNA EL NÚMERO DE CIERRES PENDIENTES EN EL EXECUTOR

        útil para pruebas y depuración

        RETURNS:
            número de tareas de cierre aún en cola o ejecutando
        """
        with self._pending_lock:
            return self._pending_count

    def shutdown(self, wait: bool = True) -> None:
        """
        CIERRA ESTA INSTANCIA Y OPCIONALMENTE ESPERA TAREAS PENDIENTES

        ARGS:
            wait: si true espera a que terminen los cierres pendientes
                antes de retornar default true

        NOTE:
            el executor singleton no se cierra aquí solo se marca la instancia
            como inactiva el executor se cierra en atexit o llamando
            shutdown_all explícitamente
        """
        if wait:
            # esperar activamente a que terminen los cierres de esta instancia
            while self.pending_dismissals > 0:
                sleep(0.1)

    @classmethod
    def shutdown_all(cls) -> None:
        """
        CIERRA EL EXECUTOR SINGLETON Y TODAS LAS INSTANCIAS

        usar solo al finalizar la aplicación o en pruebas
        """
        cls._shutdown_executor()
