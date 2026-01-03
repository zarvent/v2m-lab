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
import shutil
import subprocess
import time
from pathlib import Path

from v2m.core.interfaces import ClipboardInterface, NotificationInterface
from v2m.core.logging import logger


class LinuxClipboardAdapter(ClipboardInterface):
    """
    Linux clipboard adapter using xclip or wl-clipboard.
    Automatically detects X11 vs Wayland environments.
    """

    def __init__(self):
        """
        Initializes the clipboard adapter and detects the environment.
        """
        self._backend: str | None = None
        self._env: dict = {}
        self._detect_environment()

    def _find_xauthority(self) -> str | None:
        """
        Locates the .Xauthority file.

        Returns:
            The path to the .Xauthority file or None.
        """
        if os.environ.get("XAUTHORITY"):
            return os.environ["XAUTHORITY"]

        # Standard home location
        home = Path(os.environ.get("HOME", Path.home()))
        xauth = home / ".Xauthority"
        if xauth.exists():
            return str(xauth)

        # /run/user/UID/gdm/Xauthority
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
        Detects the graphical environment (Wayland vs X11).
        Prioritizes environment variables, then falls back to loginctl.
        """
        # 1. Environment Variables (Highest Priority)
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
            logger.warning("loginctl not found, cannot scavenge environment")
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

                            logger.info(f"Environment detected via loginctl: {session_type} -> {display_val}")
                            return
                    except subprocess.SubprocessError:
                        continue

        except Exception as e:
            logger.warning(f"Environment detection failed: {e}")

        # 3. Fallback
        self._default_fallback()

    def _default_fallback(self):
        """Sets default X11 fallback configuration."""
        logger.warning("No graphical display detected. Defaulting to X11 :0")
        self._backend = "x11"
        self._env = {"DISPLAY": ":0"}

    def _get_clipboard_commands(self) -> tuple[list, list]:
        """
        Returns copy and paste commands based on the backend.
        """
        if self._backend == "wayland":
            return (["wl-copy"], ["wl-paste"])
        else:  # x11
            return (["xclip", "-selection", "clipboard"], ["xclip", "-selection", "clipboard", "-out"])

    def copy(self, text: str) -> None:
        """
        Copies text to the clipboard.
        """
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

            time.sleep(0.1)  # Short wait to ensure process starts
            exit_code = process.poll()

            if exit_code is not None and exit_code != 0:
                stderr_out = process.stderr.read().decode()
                logger.error(f"Clipboard process failed with code {exit_code}: {stderr_out}")
            else:
                logger.debug("Text copied to clipboard")

        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")

    def paste(self) -> str:
        """
        Retrieves text from the clipboard.

        Returns:
            The clipboard content or an empty string if failed.
        """
        _, paste_cmd = self._get_clipboard_commands()

        try:
            env = os.environ.copy()
            env.update(self._env)

            result = subprocess.run(paste_cmd, capture_output=True, env=env, timeout=2)

            if result.returncode != 0:
                logger.error(f"Clipboard paste failed: {result.stderr.decode('utf-8', errors='ignore')}")
                return ""

            return result.stdout.decode("utf-8", errors="ignore")

        except FileNotFoundError:
            logger.error(f"Clipboard tool not found: {paste_cmd[0]}. Please install xclip or wl-clipboard.")
            return ""
        except subprocess.TimeoutExpired:
            logger.error("Clipboard paste operation timed out")
            return ""
        except Exception as e:
            logger.error(f"Failed to paste from clipboard: {e}")
            return ""


class LinuxNotificationAdapter(NotificationInterface):
    """
    Linux notification adapter.

    Deprecated wrapper for backward compatibility.
    Use `v2m.infrastructure.notification_service.LinuxNotificationService` directly.
    """

    def __init__(self) -> None:
        from v2m.infrastructure.notification_service import LinuxNotificationService

        self._service = LinuxNotificationService()

    def notify(self, title: str, message: str) -> None:
        self._service.notify(title, message)
