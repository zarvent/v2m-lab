"""Utilidad de Rutas Seguras.

Gestiona las rutas de archivos temporales y de ejecución, garantizando
la seguridad y el cumplimiento de los estándares XDG (XDG_RUNTIME_DIR).
"""

import contextlib
import os
import tempfile
from pathlib import Path


def get_secure_runtime_dir(app_name: str = "v2m") -> Path:
    """Retorna un directorio de ejecución seguro para la aplicación.

    Prioriza `XDG_RUNTIME_DIR` (estándar en Linux para archivos temporales
    específicos del usuario), luego recurre a un subdirectorio en `/tmp`
    con permisos estrictos (0700).

    Args:
        app_name: Nombre del subdirectorio de la aplicación.

    Returns:
        Path: Ruta segura al directorio.

    Raises:
        PermissionError: Si el directorio existe pero no es propiedad del usuario.
    """
    # 1. Intentar XDG_RUNTIME_DIR (Estándar Linux moderno)
    xdg_runtime = os.environ.get("XDG_RUNTIME_DIR")
    if xdg_runtime:
        runtime_dir = Path(xdg_runtime) / app_name
    else:
        # 2. Fallback a /tmp con subdirectorio específico del usuario
        # Se incluye el UID para evitar colisiones en sistemas multiusuario
        uid = os.getuid()
        runtime_dir = Path(tempfile.gettempdir()) / f"{app_name}_{uid}"

    # Asegurar que el directorio existe con permisos seguros (0700 - rwx------)
    if not runtime_dir.exists():
        runtime_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(runtime_dir, 0o700)
    else:
        # Si existe, verificar propiedad y permisos
        stat = runtime_dir.stat()
        if stat.st_uid != os.getuid():
            # Riesgo de seguridad: otro usuario posee este directorio
            raise PermissionError(f"El directorio de ejecución {runtime_dir} no pertenece al usuario actual.")

        # Forzar 0700 si los permisos son incorrectos
        if (stat.st_mode & 0o777) != 0o700:
            with contextlib.suppress(OSError):
                os.chmod(runtime_dir, 0o700)

    return runtime_dir
