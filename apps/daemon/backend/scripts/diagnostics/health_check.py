#!/usr/bin/env python3

"""
Health check para procesos v2m.

Detecta procesos zombie que consumen VRAM y los elimina automáticamente.
También verifica el estado del daemon y proporciona métricas de sistema.

Uso:
    python scripts/health_check.py [--kill-zombies] [--restart-daemon]
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import psutil
import subprocess
from typing import List, Tuple

# Colores ANSI
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'


def get_v2m_processes() -> List[psutil.Process]:
    """Encuentra todos los procesos relacionados con v2m."""
    v2m_procs = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'v2m' in cmdline and 'health_check' not in cmdline:
                v2m_procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return v2m_procs


def get_gpu_memory() -> Tuple[int, int]:
    """Obtiene memoria GPU usada y libre en MiB."""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used,memory.free', '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            check=True
        )
        used, free = map(int, result.stdout.strip().split(','))
        return used, free
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return 0, 0


def get_runtime_dir() -> Path:
    """Obtiene el directorio de runtime configurado."""
    try:
        from v2m.utils.paths import get_secure_runtime_dir
        return get_secure_runtime_dir()
    except ImportError:
        # Fallback si no se puede importar el utils del backend
        import os
        xdg_runtime = os.environ.get("XDG_RUNTIME_DIR")
        if xdg_runtime:
            path = Path(xdg_runtime) / "v2m"
        else:
            path = Path(f"/tmp/v2m_{os.getuid()}")

        if path.exists():
            if path.stat().st_uid != os.getuid():
                print(f"ERROR: Runtime directory {path} not owned by UID {os.getuid()}")
                return path # Still return it, but at least we warned.
        return path


def check_daemon_socket() -> bool:
    """Verifica si el socket del daemon existe."""
    return (get_runtime_dir() / 'v2m.sock').exists()


def check_pid_file() -> int | None:
    """Lee el PID file si existe."""
    pid_file = get_runtime_dir() / 'v2m_daemon.pid'
    if pid_file.exists():
        try:
            return int(pid_file.read_text().strip())
        except ValueError:
            return None
    return None


def is_daemon_responsive() -> bool:
    """Verifica si el daemon responde a PING usando el protocolo IPC correcto."""
    try:
        import socket
        import struct
        import json

        s = socket.socket(socket.AF_UNIX)
        s.settimeout(2)
        socket_path = get_runtime_dir() / 'v2m.sock'
        s.connect(str(socket_path))

        # Protocolo correcto: 4-byte big-endian length prefix + JSON payload
        request = json.dumps({"cmd": "PING", "data": {}}).encode("utf-8")
        s.sendall(struct.pack(">I", len(request)) + request)

        # Leer respuesta con el mismo protocolo
        header = s.recv(4)
        if len(header) < 4:
            s.close()
            return False

        response_len = struct.unpack(">I", header)[0]
        response_data = s.recv(response_len)
        s.close()

        response = json.loads(response_data.decode("utf-8"))
        return response.get("status") == "success"
    except Exception:
        return False


def kill_zombies(procs: List[psutil.Process]) -> int:
    """Mata procesos zombie y retorna cuántos fueron eliminados."""
    killed = 0
    for proc in procs:
        try:
            print(f"{Colors.YELLOW}  🧹 Matando proceso zombie PID {proc.pid}...{Colors.NC}")
            proc.kill()
            proc.wait(timeout=5)
            killed += 1
            print(f"{Colors.GREEN}  ✅ Proceso {proc.pid} eliminado{Colors.NC}")
        except (psutil.NoSuchProcess, psutil.TimeoutExpired, psutil.AccessDenied) as e:
            print(f"{Colors.RED}  ❌ Error eliminando {proc.pid}: {e}{Colors.NC}")
    return killed


def main():
    parser = argparse.ArgumentParser(description="Health check para v2m")
    parser.add_argument('--kill-zombies', action='store_true',
                        help='Eliminar automáticamente procesos zombie')
    parser.add_argument('--restart-daemon', action='store_true',
                        help='Reiniciar daemon después de cleanup')
    args = parser.parse_args()

    print(f"{Colors.BLUE}{'=' * 50}")
    print(f"🏥 V2M Health Check")
    print(f"{'=' * 50}{Colors.NC}\n")

    # 1. Verificar procesos
    print(f"{Colors.YELLOW}[1/4] Verificando procesos...{Colors.NC}")
    procs = get_v2m_processes()

    if not procs:
        print(f"{Colors.GREEN}✅ No hay procesos v2m corriendo{Colors.NC}")
        daemon_running = False
    else:
        print(f"{Colors.YELLOW}⚠️  {len(procs)} proceso(s) v2m encontrado(s):{Colors.NC}")
        for proc in procs:
            mem_mb = proc.memory_info().rss / 1024 / 1024
            cmdline_short = ' '.join(proc.cmdline()[:3])
            print(f"  PID {proc.pid}: {cmdline_short}... (RAM: {mem_mb:.0f}MB)")
        daemon_running = True

    # 2. Verificar socket
    print(f"\n{Colors.YELLOW}[2/4] Verificando socket Unix...{Colors.NC}")
    socket_exists = check_daemon_socket()
    if socket_exists:
        print(f"{Colors.GREEN}✅ Socket {get_runtime_dir() / 'v2m.sock'} existe{Colors.NC}")
    else:
        print(f"{Colors.YELLOW}⚠️  Socket no encontrado en {get_runtime_dir() / 'v2m.sock'}{Colors.NC}")

    # 3. Verificar PID file
    print(f"\n{Colors.YELLOW}[3/4] Verificando PID file...{Colors.NC}")
    pid_from_file = check_pid_file()
    if pid_from_file:
        if psutil.pid_exists(pid_from_file):
            print(f"{Colors.GREEN}✅ PID file válido: {pid_from_file}{Colors.NC}")
        else:
            print(f"{Colors.RED}❌ PID file apunta a proceso muerto: {pid_from_file}{Colors.NC}")
    else:
        print(f"{Colors.YELLOW}⚠️  PID file no encontrado{Colors.NC}")

    # 4. Verificar VRAM
    print(f"\n{Colors.YELLOW}[4/4] Verificando VRAM...{Colors.NC}")
    vram_used, vram_free = get_gpu_memory()
    if vram_used > 0:
        vram_total = vram_used + vram_free
        vram_pct = (vram_used / vram_total) * 100 if vram_total > 0 else 0
        print(f"  VRAM Usada: {vram_used}MiB / {vram_total}MiB ({vram_pct:.1f}%)")

        if vram_used > 1000 and not daemon_running:
            print(f"{Colors.RED}🚨 ALERTA: Alta VRAM sin daemon activo - posible leak!{Colors.NC}")
        elif vram_used < 500:
            print(f"{Colors.GREEN}✅ VRAM limpia{Colors.NC}")
        else:
            print(f"{Colors.YELLOW}⚠️  VRAM en uso (puede ser normal si daemon está activo){Colors.NC}")
    else:
        print(f"{Colors.YELLOW}⚠️  nvidia-smi no disponible{Colors.NC}")

    # 5. Test de responsividad
    if socket_exists and daemon_running:
        print(f"\n{Colors.YELLOW}[Test] Verificando responsividad del daemon...{Colors.NC}")
        if is_daemon_responsive():
            print(f"{Colors.GREEN}✅ Daemon responde correctamente (PONG){Colors.NC}")
        else:
            print(f"{Colors.RED}❌ Daemon NO responde - posible deadlock{Colors.NC}")

    # ACCIONES
    print(f"\n{Colors.BLUE}{'=' * 50}{Colors.NC}")

    # Detección de zombies
    zombie_detected = False
    if daemon_running and not socket_exists:
        print(f"{Colors.RED}🚨 ZOMBIE DETECTADO: Proceso corriendo sin socket{Colors.NC}")
        zombie_detected = True
    elif vram_used > 1000 and not daemon_running:
        print(f"{Colors.RED}🚨 ZOMBIE DETECTADO: VRAM alta sin daemon{Colors.NC}")
        zombie_detected = True

    if zombie_detected or (args.kill_zombies and procs):
        if args.kill_zombies:
            print(f"\n{Colors.YELLOW}Eliminando procesos zombie...{Colors.NC}")
            killed = kill_zombies(procs)
            print(f"{Colors.GREEN}✅ {killed} proceso(s) eliminado(s){Colors.NC}")

            # Limpiar archivos residuales
            (get_runtime_dir() / 'v2m.sock').unlink(missing_ok=True)
            (get_runtime_dir() / 'v2m_daemon.pid').unlink(missing_ok=True)
            print(f"{Colors.GREEN}✅ Archivos residuales eliminados en {get_runtime_dir()}{Colors.NC}")
        else:
            print(f"{Colors.YELLOW}💡 Usa --kill-zombies para eliminar automáticamente{Colors.NC}")

    if args.restart_daemon and (not daemon_running or zombie_detected):
        print(f"\n{Colors.YELLOW}Reiniciando daemon...{Colors.NC}")
        # Aquí podríamos agregar lógica para reiniciar
        print(f"{Colors.YELLOW}💡 Ejecuta manualmente: PYTHONPATH=src python -m v2m.daemon &{Colors.NC}")

    print(f"\n{Colors.GREEN}✅ Health check completado{Colors.NC}")

    # Exit code
    if zombie_detected and not args.kill_zombies:
        sys.exit(1)  # Indicar que hay problema


if __name__ == "__main__":
    main()
