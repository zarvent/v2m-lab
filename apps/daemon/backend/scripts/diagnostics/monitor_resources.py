#!/usr/bin/env python3

"""
Monitoreo de recursos - ¿Cuánto consume V2M?

¿Para qué sirve?
    Te genera un reporte de cuánta memoria, GPU y disco está usando
    V2M. Útil cuando:
    - Sientes que tu computadora está lenta
    - Quieres saber cuánta VRAM usa el modelo
    - Necesitas diagnosticar problemas de rendimiento

¿Cómo lo uso?
    # Ver el reporte en pantalla
    $ python scripts/monitor_resources.py

    # Guardar el reporte a un archivo
    $ python scripts/monitor_resources.py --save mi-reporte.md

¿Qué incluye el reporte?
    - Procesos V2M activos
    - Memoria del daemon
    - Uso de GPU (VRAM, utilización)
    - Espacio en disco por directorio
    - Cantidad de archivos de cache

¿Cuántos recursos debería usar V2M?
    Valores típicos:
    - Memoria daemon: 200-500 MB (sin modelo cargado)
    - VRAM con modelo large-v2: ~5-6 GB
    - Disco total del proyecto: 3-5 GB

¿Qué hago si consume demasiado?
    1. Limpia el cache: python scripts/cleanup.py --all
    2. Revisa si hay .venv duplicado (puede ser ~10 GB extra!)
    3. Reinicia el daemon: ./scripts/v2m-daemon.sh restart

Para desarrolladores:
    El script usa subprocesos para llamar a nvidia-smi, ps, du, etc.
    Si nvidia-smi no está disponible, simplemente omite esa sección.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[2]
VENV_DIR = PROJECT_ROOT / "venv"
LOGS_DIR = PROJECT_ROOT / "logs"
"""Path: Directorio de archivos de log."""


def get_process_info() -> None:
    """
    Te muestra qué procesos de V2M están corriendo ahora mismo.

    Básicamente hace un `ps aux | grep v2m` pero más bonito.
    Útil para verificar que el daemon esté vivo y ver cuánto
    CPU está usando.

    Si no aparece ningún proceso, el daemon probablemente esté
    apagado o hubo algún crash.
    """
    print("## PROCESOS V2M / V2M PROCESSES\n")

    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            check=True
        )

        # Filtrar procesos relacionados con V2M
        v2m_processes = [line for line in result.stdout.split('\n')
                         if 'v2m' in line.lower() and 'grep' not in line]

        if v2m_processes:
            print("```")
            print(result.stdout.split('\n')[0])  # Header
            for proc in v2m_processes:
                print(proc)
            print("```\n")
        else:
            print("⚠️  No se encontraron procesos V2M activos\n")

    except Exception as e:
        print(f"❌ Error obteniendo procesos: {e}\n")


def get_daemon_memory() -> None:
    """
    Consulta cuánta memoria RAM está usando el daemon.

    Le pregunta a systemd cuál es el PID del servicio v2m.service
    y extrae el dato de memoria de ahí. Es la forma más precisa
    de saber si el daemon está consumiendo mucha RAM.

    Tip:
        Si ves que la memoria sigue creciendo con el tiempo,
        podría haber un memory leak. Avisanos si pasa.
    """
    print("## MEMORIA DEL DAEMON / DAEMON MEMORY\n")

    try:
        # Obtener PID del daemon desde systemd
        result = subprocess.run(
            ["systemctl", "--user", "show", "v2m.service", "-p", "MainPID"],
            capture_output=True,
            text=True,
            check=True
        )

        pid = result.stdout.split('=')[1].strip()

        if pid == "0":
            print("⚠️  Daemon no está corriendo\n")
            return

        # Obtener memoria del proceso
        status_result = subprocess.run(
            ["systemctl", "--user", "status", "v2m.service", "--no-pager"],
            capture_output=True,
            text=True,
            check=False
        )

        # Extraer línea de Memory
        for line in status_result.stdout.split('\n'):
            if 'Memory:' in line:
                print(f"**PID**: {pid}")
                print(f"**{line.strip()}**\n")
                break

    except Exception as e:
        print(f"❌ Error obteniendo memoria del daemon: {e}\n")


def get_gpu_usage() -> None:
    """
    Muestra cuánto de tu GPU NVIDIA está usando V2M.

    Usa nvidia-smi (la herramienta oficial de NVIDIA) para mostrarte:
        - Qué GPU tenés
        - Cuánta VRAM está en uso (Whisper puede comer bastante)
        - El porcentaje de utilización del GPU

    Si no tenés GPU NVIDIA o nvidia-smi no está instalado,
    simplemente te avisa y sigue adelante sin explotar.
    """
    print("## USO DE GPU / GPU USAGE\n")

    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=True
        )

        gpu_info = result.stdout.strip().split(', ')

        print(f"**GPU**: {gpu_info[0]}")
        print(f"**VRAM**: {gpu_info[1]} MB / {gpu_info[2]} MB ({int(gpu_info[1])/int(gpu_info[2])*100:.1f}%)")
        print(f"**Utilización**: {gpu_info[3]}%\n")

    except FileNotFoundError:
        print("⚠️  nvidia-smi no disponible (GPU no detectada)\n")
    except Exception as e:
        print(f"❌ Error obteniendo info de GPU: {e}\n")


def get_disk_usage() -> None:
    """
    Te muestra qué carpetas del proyecto ocupan más espacio.

    Corre `du` por debajo para calcular el tamaño de cada
    subcarpeta y te muestra las 10 más gordas. Útil para
    encontrar qué está llenando tu disco.

    Spoiler: casi siempre es venv/ o algún cache.
    """
    print("## USO DE DISCO / DISK USAGE\n")

    try:
        result = subprocess.run(
            ["du", "-sh", str(PROJECT_ROOT / "*")],
            capture_output=True,
            text=True,
            shell=True,
            check=False
        )

        lines = result.stdout.strip().split('\n')
        sorted_lines = sorted(lines, key=lambda x: x.split()[0], reverse=True)

        print("```")
        for line in sorted_lines[:10]:  # Top 10
            print(line)
        print("```\n")

        # Tamaño total
        total_result = subprocess.run(
            ["du", "-sh", str(PROJECT_ROOT)],
            capture_output=True,
            text=True,
            check=True
        )

        print(f"**TOTAL**: {total_result.stdout.split()[0]}\n")

    except Exception as e:
        print(f"❌ Error obteniendo uso de disco: {e}\n")


def check_cache_bloat() -> None:
    """
    Revisa si hay demasiado cache de Python acumulado.

    Cuenta los directorios __pycache__ y archivos .pyc. Si hay
    una cantidad ridiculosa (más de 100 dirs o 1000 archivos),
    te avisa que es hora de una limpieza.

    No borra nada automáticamente, solo te dice qué encontró.
    Para limpiar, corré: python scripts/cleanup.py --cache
    """
    print("## CACHE PYTHON / PYTHON CACHE\n")

    try:
        pycache_result = subprocess.run(
            ["find", str(PROJECT_ROOT), "-type", "d", "-name", "__pycache__"],
            capture_output=True,
            text=True,
            check=True
        )

        pyc_result = subprocess.run(
            ["find", str(PROJECT_ROOT), "-name", "*.pyc"],
            capture_output=True,
            text=True,
            check=True
        )

        pycache_count = len([l for l in pycache_result.stdout.strip().split('\n') if l])
        pyc_count = len([l for l in pyc_result.stdout.strip().split('\n') if l])

        print(f"**Directorios `__pycache__`**: {pycache_count}")
        print(f"**Archivos `.pyc`**: {pyc_count}")

        if pycache_count > 100 or pyc_count > 1000:
            print("\n⚠️  **ADVERTENCIA**: Cache excesivo detectado")
            print(f"   Ejecuta: `python3 scripts/cleanup.py --cache`\n")
        else:
            print("\n✓ Cache dentro de límites normales\n")

    except Exception as e:
        print(f"❌ Error contando cache: {e}\n")


def generate_report() -> None:
    """
    Genera un reporte completo de recursos en formato Markdown.

    Ejecuta todas las funciones de diagnóstico y muestra el resultado
    en un formato estructurado con secciones para cada tipo de recurso.
    Al final incluye una sección de acciones recomendadas.

    Secciones del reporte:
        1. Procesos V2M activos
        2. Memoria del daemon
        3. Uso de GPU
        4. Uso de disco
        5. Cache Python
        6. Acciones recomendadas
    """
    print("\n" + "="*70)
    print(f"# REPORTE DE RECURSOS V2M / V2M RESOURCE REPORT")
    print(f"**Fecha**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

    get_process_info()
    get_daemon_memory()
    get_gpu_usage()
    get_disk_usage()
    check_cache_bloat()

    print("="*70)
    print("## ACCIONES RECOMENDADAS / RECOMMENDED ACTIONS\n")
    print("- **Limpieza completa**: `python3 scripts/cleanup.py --all`")
    print("- **Solo cache**: `python3 scripts/cleanup.py --cache`")
    print("- **Reiniciar daemon**: `systemctl --user restart v2m.service`")
    print("- **Ver logs**: `journalctl --user -u v2m.service -n 50`")
    print("="*70 + "\n")


def main() -> None:
    """
    Punto de entrada principal del script de monitoreo.

    Procesa los argumentos de línea de comandos y genera el reporte
    de recursos. Puede mostrar el reporte en pantalla o guardarlo
    en un archivo Markdown.

    Opciones de línea de comandos:
        --save FILE: Guarda el reporte en el archivo especificado
                    en lugar de mostrarlo en pantalla.

    Example:
        >>> # Desde línea de comandos:
        >>> # python scripts/monitor_resources.py
        >>> # python scripts/monitor_resources.py --save status.md
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Monitoreo de recursos del proyecto V2M"
    )

    parser.add_argument("--save", type=str, metavar="FILE",
                       help="Guardar reporte en archivo markdown")

    args = parser.parse_args()

    if args.save:
        # Redirigir stdout a archivo
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            generate_report()

        output = f.getvalue()

        with open(args.save, 'w') as out:
            out.write(output)

        print(f"✓ Reporte guardado en: {args.save}")
    else:
        generate_report()


if __name__ == "__main__":
    main()
