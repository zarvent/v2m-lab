#!/usr/bin/env python3

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
instalar v2m como servicio del sistema

¿qué hace este script?
    configura v2m para que arranque automáticamente cuando inicies
    sesión en tu computadora ya no tendrás que iniciarlo manualmente

¿cómo lo uso?
    $ python scripts/install_service.py

    eso es todo el script hace el resto

¿qué pasa después de instalarlo?
    - v2m arranca solo cuando inicias sesión
    - puedes controlarlo con systemctl

      $ systemctl --user status v2m.service   # Ver si está corriendo
      $ systemctl --user restart v2m.service  # Reiniciarlo
      $ systemctl --user stop v2m.service     # Detenerlo
      $ systemctl --user disable v2m.service  # Desactivar arranque automático

¿dónde se guarda la configuración?
    ~/.config/systemd/user/v2m.service

¿por qué "usuario" y no "sistema"?
    porque v2m necesita acceso a tu display (para el portapapeles)
    y a tu sesión los servicios de sistema no tienen eso

requisitos previos
    1 entorno virtual creado en ./venv
    2 archivo .env con tu gemini_api_key
    3 no tener dos entornos virtuales (.venv y venv)

¿algo salió mal?
    - si ves errores de cuda ./scripts/repair_libs.sh
    - si hay .venv duplicado python scripts/cleanup.py --fix-venv
    - para ver logs journalctl --user -u v2m.service -f

para desarrolladores
    este script genera dinámicamente el archivo .service detectando
    las rutas de cuda automáticamente también configura display y
    xauthority para que el daemon pueda acceder al portapapeles x11
"""

import os
import sys
from pathlib import Path
import subprocess

# Configuración del servicio
SERVICE_NAME = "v2m.service"

USER_HOME = Path.home()
"""path: directorio home del usuario actual"""

SYSTEMD_USER_DIR = USER_HOME / ".config/systemd/user"
"""path: directorio para servicios systemd de usuario"""

SOURCE_SERVICE_FILE = Path("v2m.service")
"""path: archivo de servicio fuente (si existe)"""


def get_cuda_paths(venv_python: Path) -> str:
    """
    busca dónde están las librerías cuda/cudnn para que el servicio las encuentre

    cuando el daemon corre bajo systemd no tiene acceso al path normal
    así que necesitamos decirle explícitamente dónde encontrar las libs
    de nvidia esta función las busca en dos lugares

        1 torch.cuda.lib (para pytorch 2.9.1+)
        2 las carpetas nvidia/* dentro del venv

    args:
        venv_python: la ruta al python del venv (ej /home/user/v2m/venv/bin/python)

    returns:
        una cadena con las rutas separadas por ":" lista para usar en
        ld_library_path si no encuentra nada devuelve cadena vacía

    example
        >>> paths = get_cuda_paths(Path("/home/user/v2m/venv/bin/python"))
        >>> # Devuelve algo como: "/home/user/v2m/venv/.../nvidia/cublas/lib:..."
    """
    paths = []

    # 1. Intenta torch.cuda.lib (torch 2.9.1+)
    try:
        cmd = [
            str(venv_python),
            "-c",
            "import torch.cuda; import os; "
            "cuda_lib_path = os.path.join(os.path.dirname(torch.__file__), 'lib'); "
            "print(cuda_lib_path if os.path.exists(cuda_lib_path) else '')"
        ]
        result = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        if result:
            paths.append(result)
    except Exception:
        pass

    # 2. Buscar nvidia libs directamente en el venv
    venv_dir = Path(venv_python).parent.parent

    # Detectar versión de Python dinámicamente (no hardcodear 3.12)
    try:
        cmd = [str(venv_python), "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"]
        py_version = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        py_version = "3.12"  # Fallback si falla la detección

    nvidia_base = venv_dir / "lib" / f"python{py_version}" / "site-packages" / "nvidia"

    for lib_name in ["cublas", "cudnn"]:
        lib_dir = nvidia_base / lib_name / "lib"
        if lib_dir.exists():
            paths.append(str(lib_dir))

    if paths:
        # Eliminar duplicados manteniendo orden
        unique_paths = []
        for p in paths:
            if p not in unique_paths:
                unique_paths.append(p)
        return ':'.join(unique_paths)

    print("⚠️  Advertencia: No se pudieron detectar librerías NVIDIA automáticamente")
    return ""

def install_service() -> None:
    """
    hace toda la magia para que v2m corra como servicio systemd

    esta función hace un montón de cosas por vos

        1 crea la carpeta ~/.config/systemd/user/ si no existe
        2 verifica que no tengas dos venvs (común después de reinstalar)
        3 busca las librerías cuda automáticamente
        4 genera el archivo v2m.service con toda la config
        5 le dice a systemd que recargue y habilite el servicio
        6 reinicia el daemon para aplicar cambios

    si algo sale mal (venvs duplicados systemd falla) el script
    explota con un mensaje claro de qué pasó y cómo arreglarlo

    nota sobre display y xauthority
        el servicio necesita acceso al display de x11 para usar xclip
        (copiar al portapapeles) detectamos esas variables del ambiente
        actual y las hardcodeamos en el servicio
    """
    print(f"🔧 Instalando {SERVICE_NAME}...")

    # 1. Directorio de destino
    SYSTEMD_USER_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Rutas absolutas - Detectar estructura monorepo
    repo_root = Path.cwd().resolve()
    if (repo_root / "apps" / "backend").exists():
        current_dir = repo_root / "apps" / "backend"
    else:
        current_dir = repo_root  # Fallback para estructura legacy
    venv_python = current_dir / "venv/bin/python"

    # 2.1 Validar entornos virtuales duplicados
    venv_duplicate = current_dir / ".venv"
    if venv_duplicate.exists() and (current_dir / "venv").exists():
        print("❌ ERROR: Detectados dos entornos virtuales (.venv y venv)")
        print("   Esto puede causar consumo excesivo de disco (~10GB)")
        print(f"   Ejecuta: python3 scripts/cleanup.py --fix-venv")
        sys.exit(1)

    # 3. Calcular LD_LIBRARY_PATH
    cuda_path = get_cuda_paths(venv_python)
    env_vars = f"Environment=PYTHONPATH={current_dir}/src\n"
    env_vars += f"Environment=PYTHONUNBUFFERED=1\n"

    if cuda_path:
        print(f"✅ Librerías CUDA detectadas: {cuda_path[:50]}...")
        env_vars += f"Environment=LD_LIBRARY_PATH={cuda_path}\n"
    else:
        print("⚠️  Instalando sin soporte explícito de librerías CUDA (podría fallar si usas GPU)")

    # Detección agresiva de DISPLAY para hardcodearlo en el servicio
    display_val = os.environ.get("DISPLAY", ":0") # Default a :0 si no se detecta
    xauth_val = os.environ.get("XAUTHORITY", f"{USER_HOME}/.Xauthority")

    env_vars += f"Environment=DISPLAY={display_val}\n"
    env_vars += f"Environment=XAUTHORITY={xauth_val}\n" # Necesario para xclip/x11 a veces

    # 4. Contenido del servicio
    service_content = f"""[Unit]
Description=Voice2Machine Daemon
After=network.target sound.target default.target
PartOf=graphical-session.target

[Service]
Type=simple
WorkingDirectory={current_dir}
{env_vars}ExecStart={venv_python} -m v2m.main --daemon
Restart=on-failure
RestartSec=5

# Modern logging (Journald)
StandardOutput=journal
StandardError=journal

# Cargar variables (API Key) desde .env
EnvironmentFile={current_dir}/.env

[Install]
WantedBy=default.target
"""

    # 5. Escribir archivo
    dest_file = SYSTEMD_USER_DIR / SERVICE_NAME
    with open(dest_file, "w") as f:
        f.write(service_content)

    print(f"📄 Archivo de servicio escrito en: {dest_file}")

    # 6. Recargar y Habilitar
    print("🔄 Recargando systemd...")
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", SERVICE_NAME], check=True)

    # 7. Reiniciar para aplicar cambios
    print("🚀 Reiniciando servicio...")
    subprocess.run(["systemctl", "--user", "restart", SERVICE_NAME], check=True)

    print("\n✅ ¡Instalación Completada! Prueba dictar ahora.")

if __name__ == "__main__":
    install_service()
