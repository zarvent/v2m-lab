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
Main Entry Point for Voice2Machine.

This module acts as a unified launcher that can operate in two modes:

1. **Daemon Mode** (`--daemon`): Starts the persistent background process.
2. **Client Mode** (`<COMMAND>`): Sends IPC commands to the running daemon.

Examples:
    Start the daemon:
        python -m v2m.main --daemon

    Send commands:
        python -m v2m.main START_RECORDING
        python -m v2m.main STOP_RECORDING
"""

import argparse
import asyncio
import sys

from v2m.client import send_command
from v2m.core.ipc_protocol import IPCCommand
from v2m.core.logging import logger


def _setup_uvloop() -> None:
    """
    Configures uvloop as the event loop if available.
    """
    try:
        import uvloop

        uvloop.install()
        logger.debug("uvloop enabled")
    except ImportError:
        pass


def main() -> None:
    """
    Main function processing arguments and executing the appropriate mode.
    """
    parser = argparse.ArgumentParser(description="Voice2Machine Main Entry Point")

    parser.add_argument("--daemon", action="store_true", help="Start the daemon process in foreground")
    parser.add_argument("command", nargs="?", choices=[e.value for e in IPCCommand], help="IPC command to send")
    parser.add_argument("payload", nargs="*", help="Optional payload for the command")

    args = parser.parse_args()

    if args.daemon:
        _setup_uvloop()

        from v2m.daemon import Daemon

        logger.info("starting voice2machine daemon...")
        daemon = Daemon()
        daemon.run()
    elif args.command:
        # Client mode
        try:
            full_command = args.command
            if args.payload:
                full_command += " " + " ".join(args.payload)

            response = asyncio.run(send_command(full_command))
            print(response)
        except Exception as e:
            print(f"error sending command: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
