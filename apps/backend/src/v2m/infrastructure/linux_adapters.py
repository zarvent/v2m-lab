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

import os
import subprocess
import time
from pathlib import Path

from v2m.core.interfaces import ClipboardInterface, NotificationInterface
from v2m.core.logging import logger


class LinuxClipboardAdapter(ClipboardInterface):
    """
    adaptador de portapapeles para linux que usa directamente xclip o wl-clipboard

    no depende de pyperclip para evitar problemas con variables de entorno
    en procesos daemon detecta automáticamente x11 vs wayland
    """

    def __init__(self):
        """
        inicializa el adaptador de portapapeles y detecta el entorno gráfico
        """
        self._backend: str | None = None
        self._env: dict = {}
        self._detect_environment()

    def _find_xauthority(self) -> str | None:
        """
        busca el archivo .xauthority en ubicaciones estándar

        returns:
            la ruta al archivo .xauthority si se encuentra o none
        """
        # 1. Si ya está en el entorno, usarlo
        if os.environ.get("XAUTHORITY"):
            return os.environ["XAUTHORITY"]

        # 2. Ubicación estándar en home
        home = Path(os.environ.get("HOME", subprocess.getoutput("echo ~")))
        xauth = home / ".Xauthority"
        if xauth.exists():
            return str(xauth)

        # 3. Ubicación en /run/user (común en GDM/systemd)
        try:
            uid = os.getuid()
            run_user_auth = Path(f"/run/user/{uid}/gdm/Xauthority")
            if run_user_auth.exists():
                return str(run_user_auth)
        except Exception:
            pass

        return None

    def _detect_environment(self) -> None:
        """
        detecta variables de entorno buscando sesiones gráficas
        estrategia env vars > loginctl > sockets en /tmp/.x11-unix
        """
        # 1. Heredar del entorno actual (Prioridad máxima)
        if os.environ.get("WAYLAND_DISPLAY"):
            self._backend = "wayland"
            self._env = {"WAYLAND_DISPLAY": os.environ["WAYLAND_DISPLAY"]}
            return
        if os.environ.get("DISPLAY"):
            self._backend = "x11"
            self._env = {"DISPLAY": os.environ["DISPLAY"]}
            return

        # 2. Scavenging vía loginctl
        try:
            user = os.environ.get("USER") or subprocess.getoutput("whoami")
            # Safe subprocess call without shell=True
            output = subprocess.check_output(
                ["loginctl", "list-sessions", "--no-legend"],
                text=True
            ).strip()

            sessions = []
            for line in output.split('\n'):
                parts = line.split()
                # loginctl list-sessions output format: SESSION UID USER SEAT TTY
                # We want session ID (index 0) where USER (index 2) matches current user
                if len(parts) >= 3 and parts[2] == user:
                     sessions.append(parts[0])

            for session_id in sessions:
                if not session_id: continue

                # Inspeccionar tipo de sesión
                type_cmd = ["loginctl", "show-session", session_id, "-p", "Type", "--value"]
                session_type = subprocess.check_output(type_cmd, text=True).strip()

                # Extraer Display si existe, independientemente del tipo
                display_cmd = ["loginctl", "show-session", session_id, "-p", "Display", "--value"]
                display_val = subprocess.check_output(display_cmd, text=True).strip()

                if display_val:
                    self._backend = session_type if session_type in ["wayland"] else "x11"
                    if session_type == "wayland":
                         self._env = {"WAYLAND_DISPLAY": display_val}
                    else:
                         self._env = {"DISPLAY": display_val}
                         # Scavenge XAUTHORITY for X11
                         xauth_path = self._find_xauthority()
                         if xauth_path:
                             self._env["XAUTHORITY"] = xauth_path
                             logger.info(f"XAUTHORITY scavenged: {xauth_path}")

                    logger.info(f"Environment detected via loginctl: Session {session_id} ({session_type}) -> {display_val}")
                    return

        except Exception as e:
            logger.warning(f"Environment scavenging failed: {e}")

        # 3. FALLBACK ULTIMATE: Escanear sockets activos en /tmp/.X11-unix
        # Esto encuentra :0, :1, :2 lo que sea que esté vivo.
        try:
            x11_socket_dir = Path("/tmp/.X11-unix")
            if x11_socket_dir.exists():
                # Buscar sockets que empiecen por X (ej: X0, X1)
                sockets = sorted([s.name for s in x11_socket_dir.iterdir() if s.name.startswith("X")])
                if sockets:
                    # Tomar el primero (o el último modificado si quisieras ser más fino)
                    # X1 -> :1
                    active_display = f":{sockets[0][1:]}"
                    self._backend = "x11"
                    self._env = {"DISPLAY": active_display}
                    logger.info(f"Display detected via socket scan: {active_display}")

                    # Intentar inyectar XAUTHORITY si falta
                    xauth = self._find_xauthority()
                    if xauth:
                        self._env["XAUTHORITY"] = xauth
                    return
        except Exception as e:
            logger.warning(f"Socket scan failed: {e}")

        logger.error("CRITICAL: No graphical display found. Clipboard will not work.")
        self._backend = "x11"
        # No definimos DISPLAY, dejamos que xclip intente su default (que es :0)
        self._env = {}

    def _get_clipboard_commands(self) -> tuple[list, list]:
        """
        retorna los comandos para copiar y pegar según el backend detectado

        returns:
            tupla con (comando_copy comando_paste)
        """
        if self._backend == "wayland":
            return (
                ["wl-copy"],
                ["wl-paste"]
            )
        else:  # x11
            return (
                ["xclip", "-selection", "clipboard"],
                ["xclip", "-selection", "clipboard", "-out"]
            )

    def copy(self, text: str) -> None:
        """
        copia el texto al portapapeles

        args:
            text: el texto a copiar
        """
        if not text: return
        copy_cmd, _ = self._get_clipboard_commands()

        try:
            env = os.environ.copy()
            env.update(self._env)

            process = subprocess.Popen(
                copy_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, # Capturamos stderr
                env=env
            )

            process.stdin.write(text.encode("utf-8"))
            process.stdin.close()

            # Espera táctica y verificación de estado
            time.sleep(0.1)
            exit_code = process.poll()

            if exit_code is not None and exit_code != 0:
                # El proceso murió prematuramente
                stderr_out = process.stderr.read().decode()
                logger.error(f"Clipboard process died with code {exit_code}. STDERR: {stderr_out}")
            else:
                logger.debug(f"Copied {len(text)} chars to clipboard (PID: {process.pid})")

        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")

    def paste(self) -> str:
        """
        obtiene texto del portapapeles del sistema

        returns:
            contenido del portapapeles o cadena vacía si falla
        """
        _, paste_cmd = self._get_clipboard_commands()

        try:
            # Combinar env del sistema con las variables detectadas
            env = os.environ.copy()
            env.update(self._env)

            result = subprocess.run(
                paste_cmd,
                capture_output=True,
                env=env,
                timeout=2
            )

            if result.returncode != 0:
                logger.error(f"Clipboard paste failed: {result.stderr.decode('utf-8', errors='ignore')}")
                return ""

            return result.stdout.decode("utf-8", errors="ignore")

        except FileNotFoundError:
            logger.error(f"Clipboard tool not found: {paste_cmd[0]}. Install xclip or wl-clipboard.")
            return ""
        except subprocess.TimeoutExpired:
            logger.error("Clipboard paste operation timed out")
            return ""
        except Exception as e:
            logger.error(f"Failed to paste from clipboard: {e}")
            return ""

class LinuxNotificationAdapter(NotificationInterface):
    """
    adaptador de notificaciones para linux

    wrapper de compatibilidad que delega al servicio de notificaciones
    production-ready mantener esta clase para backwards compatibility
    con código existente que importa desde linux_adapters

    note:
        para nuevos usos preferir importar directamente::

            from v2m.infrastructure.notification_service import LinuxNotificationService

    deprecated:
        esta clase será removida en v3.0 usar LinuxNotificationService
    """

    def __init__(self) -> None:
        """
        inicializa el adapter delegando al servicio de notificaciones
        """
        # lazy import para evitar circular imports
        from v2m.infrastructure.notification_service import LinuxNotificationService
        self._service = LinuxNotificationService()

    def notify(self, title: str, message: str) -> None:
        """
        envía una notificación al escritorio con auto-dismiss

        args:
            title: título de la notificación
            message: mensaje de la notificación
        """
        self._service.notify(title, message)
