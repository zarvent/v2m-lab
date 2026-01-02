
import os
import tempfile
from pathlib import Path


def get_secure_runtime_dir(app_name: str = "v2m") -> Path:
    """
    Returns a secure runtime directory for the application.

    Prioritizes XDG_RUNTIME_DIR, then falls back to a user-owned subdirectory in /tmp
    with 0700 permissions.

    Args:
        app_name: The name of the application subdirectory.

    Returns:
        Path: The secure directory path.
    """
    # 1. Try XDG_RUNTIME_DIR (standard on Linux for user-specific runtime files)
    xdg_runtime = os.environ.get("XDG_RUNTIME_DIR")
    if xdg_runtime:
        runtime_dir = Path(xdg_runtime) / app_name
    else:
        # 2. Fallback to /tmp with a user-specific subdirectory
        # Using the user's UID to avoid collisions and permission issues
        uid = os.getuid()
        runtime_dir = Path(tempfile.gettempdir()) / f"{app_name}_{uid}"

    # Ensure the directory exists with secure permissions (0700 - rwx------)
    if not runtime_dir.exists():
        runtime_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(runtime_dir, 0o700)
    else:
        # If it exists, verify permissions and ownership
        stat = runtime_dir.stat()
        if stat.st_uid != os.getuid():
             # If owned by someone else, we can't use it safely.
             # This is a critical error or we need a new fallback.
             # For now, raising an error is safer than using an insecure directory.
             raise PermissionError(f"Runtime directory {runtime_dir} is not owned by the current user.")

        # Enforce 0700 if strictly required, but existing might be okay if user-owned.
        # However, to be safe:
        if (stat.st_mode & 0o777) != 0o700:
             # Try to fix permissions
             try:
                 os.chmod(runtime_dir, 0o700)
             except OSError:
                 pass # Might fail if not owner, but we checked ownership.

    return runtime_dir
