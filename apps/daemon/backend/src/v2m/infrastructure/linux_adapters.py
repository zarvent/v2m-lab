
"""
Adaptadores de Sistema para Linux.

Implementaciones concretas de interfaces de sistema para entornos Linux,
incluyendo detección automática de servidor de pantalla (X11 vs Wayland)
y gestión del portapapeles.
"""

import os
import shutil
import subprocess
import time
from pathlib import Path

from v2m.core.interfaces import ClipboardInterface, NotificationInterface
from v2m.core.logging import logger


class LinuxClipboardAdapter(ClipboardInterface):
    """
    Adaptador de portapapeles para Linux usando xclip o wl-clipboard.

    Detecta automáticamente el entorno gráfico (X11 vs Wayland) y selecciona
    la herramienta de línea de comandos apropiada. Prioriza variables de
    entorno, luego introspección de sesión vía loginctl.
    """

    def __init__(self):
        """Inicializa el adaptador y detecta el entorno."""
        self._backend: str | None = None
        self._env: dict = {}
        self._detect_environment()

    def _find_xauthority(self) -> str | None:
        """
        Localiza el archivo .Xauthority necesario para X11.

        Busca en ubicaciones estándar ($XAUTHORITY, home, /run/user).

        Returns:
            str | None: Ruta al archivo o None si no se encuentra.
        """
        if os.environ.get("XAUTHORITY"):
            return os.environ["XAUTHORITY"]

        # Ubicación estándar en home
        home = Path(os.environ.get("HOME", Path.home()))
        xauth = home / ".Xauthority"
        if xauth.exists():
            return str(xauth)

        # Ubicación en /run/user (común en GDM/systemd modernos)
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
        Detecta el entorno gráfico (Wayland vs X11).

        Estrategia:
        1. Variables de Entorno (Prioridad más alta).
        2. Introspección `loginctl` (Systemd/GDM).
        3. Fallback a X11 predeterminado.
        """
        # 1. Variables de Entorno (Máxima Prioridad)
        if os.environ.get("WAYLAND_DISPLAY"):
            self._backend = "wayland"
            self._env = {"WAYLAND_DISPLAY": os.environ["WAYLAND_DISPLAY"]}
            return
        if os.environ.get("DISPLAY"):
            self._backend = "x11"
            self._env = {"DISPLAY": os.environ["DISPLAY"]}
            return

        # 2. loginctl (Systemd/GDM)
        if not shutil.which("loginctl"):
            logger.warning("loginctl no encontrado, no se puede escanear entorno")
            self._default_fallback()
            return

        try:
            user = os.environ.get("USER") or subprocess.getoutput("whoami")
            output = subprocess.check_output(["loginctl", "list-sessions", "--no-legend"], text=True).strip()

            for line in output.split("\n"):
                parts = line.split()
                if len(parts) >= 3 and parts[2] == user:
                    session_id = parts[0]

                    try:
                        session_type = subprocess.check_output(
                            ["loginctl", "show-session", session_id, "-p", "Type", "--value"], text=True
                        ).strip()

                        display_val = subprocess.check_output(
                            ["loginctl", "show-session", session_id, "-p", "Display", "--value"], text=True
                        ).strip()

                        if display_val:
                            self._backend = "wayland" if session_type == "wayland" else "x11"
                            if self._backend == "wayland":
                                self._env = {"WAYLAND_DISPLAY": display_val}
                            else:
                                self._env = {"DISPLAY": display_val}
                                xauth = self._find_xauthority()
                                if xauth:
                                    self._env["XAUTHORITY"] = xauth

                            logger.info(f"entorno detectado vía loginctl: {session_type} -> {display_val}")
                            return
                    except subprocess.SubprocessError:
                        continue

        except Exception as e:
            logger.warning(f"falló la detección de entorno: {e}")

        # 3. Fallback
        self._default_fallback()

    def _default_fallback(self):
        """Establece configuración predeterminada de fallback a X11."""
        logger.warning("no se detectó pantalla gráfica, usando fallback x11 :0")
        self._backend = "x11"
        self._env = {"DISPLAY": ":0"}

    def _get_clipboard_commands(self) -> tuple[list, list]:
        """Devuelve los comandos de copiar y pegar según el backend."""
        if self._backend == "wayland":
            return (["wl-copy"], ["wl-paste"])
        else:  # x11
            return (["xclip", "-selection", "clipboard"], ["xclip", "-selection", "clipboard", "-out"])

    def copy(self, text: str) -> None:
        """Copia texto al portapapeles."""
        if not text:
            return
        copy_cmd, _ = self._get_clipboard_commands()

        try:
            env = os.environ.copy()
            env.update(self._env)

            process = subprocess.Popen(
                copy_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=env
            )

            process.stdin.write(text.encode("utf-8"))
            process.stdin.close()

            time.sleep(0.1)  # Pequeña espera para asegurar inicio
            exit_code = process.poll()

            if exit_code is not None and exit_code != 0:
                stderr_out = process.stderr.read().decode()
                logger.error(f"proceso de portapapeles falló con código {exit_code}: {stderr_out}")
            else:
                logger.debug("texto copiado al portapapeles")

        except Exception as e:
            logger.error(f"fallo al copiar al portapapeles: {e}")

    def paste(self) -> str:
        """
        Recupera texto del portapapeles.

        Returns:
            str: Contenido del portapapeles o cadena vacía si falla.
        """
        _, paste_cmd = self._get_clipboard_commands()

        try:
            env = os.environ.copy()
            env.update(self._env)

            result = subprocess.run(paste_cmd, capture_output=True, env=env, timeout=2)

            if result.returncode != 0:
                logger.error(f"falló el pegado del portapapeles: {result.stderr.decode('utf-8', errors='ignore')}")
                return ""

            return result.stdout.decode("utf-8", errors="ignore")

        except FileNotFoundError:
            logger.error(f"herramienta de portapapeles no encontrada: {paste_cmd[0]}. instale xclip o wl-clipboard.")
            return ""
        except subprocess.TimeoutExpired:
            logger.error("operación de pegado agotó el tiempo de espera")
            return ""
        except Exception as e:
            logger.error(f"fallo al pegar del portapapeles: {e}")
            return ""


class LinuxNotificationAdapter(NotificationInterface):
    """
    Adaptador de notificaciones para Linux.

    Wrapper obsoleto para compatibilidad hacia atrás.
    Use `v2m.infrastructure.notification_service.LinuxNotificationService` directamente.
    """

    def __init__(self) -> None:
        from v2m.infrastructure.notification_service import LinuxNotificationService

        self._service = LinuxNotificationService()

    def notify(self, title: str, message: str) -> None:
        self._service.notify(title, message)
