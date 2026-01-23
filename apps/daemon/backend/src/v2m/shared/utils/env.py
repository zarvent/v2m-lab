import ctypes
import os
import site
from pathlib import Path

from v2m.shared.logging import logger


def configure_gpu_environment() -> None:
    """Configura dinámicamente las rutas de librerías NVIDIA (cuDNN, Cublas) en el entorno.

    Estrategia SOTA (2026) para entornos aislados (venv):
    1. Identifica rutas de librerías nvidia instaladas vía pip.
    2. Actualiza LD_LIBRARY_PATH (útil para subprocesos).
    3. Precarga explícitamente librerías críticas (cuDNN, Cublas) usando ctypes con RTLD_GLOBAL.
       Esto expone los símbolos al cargador dinámico, permitiendo que CTranslate2/Faster-Whisper
       las encuentre sin necesitar configuración a nivel de sistema operativo.
    """
    try:
        site_packages = site.getsitepackages()
        nvidia_paths = []

        # Librerías críticas que deben ser precargadas en orden de dependencia
        # cuDNN 9 split libs: engines dependen de ops, ops depende de graph/cnn? No, graph depende de ops.
        # Orden seguro aproximado: cublas -> cudnn_ops -> cudnn_cnn -> cudnn_adv -> cudnn_engines
        libs_to_preload = [
            "libcublas.so",
            "libcublasLt.so",
            "libcudnn_engines_precompiled.so",  # cuDNN 9
            "libcudnn_engines_runtime.so",  # cuDNN 9
            "libcudnn_heuristic.so",  # cuDNN 9
            "libcudnn_graph.so",  # cuDNN 9
            "libcudnn_ops.so",  # cuDNN 9
            "libcudnn_cnn.so",  # cuDNN 9
            "libcudnn_adv.so",  # cuDNN 9
            "libcudnn.so",
        ]

        # 1. Encontrar rutas
        for sp in site_packages:
            p = Path(sp) / "nvidia"
            if p.exists() and p.is_dir():
                for lib_dir in p.glob("*/lib"):
                    if lib_dir.is_dir():
                        nvidia_paths.append(lib_dir)

        if not nvidia_paths:
            return

        # 2. Actualizar LD_LIBRARY_PATH (para hijos)
        new_ld_paths = [str(p) for p in nvidia_paths]
        current_ld = os.environ.get("LD_LIBRARY_PATH", "")
        if current_ld:
            new_ld_paths.append(current_ld)
        os.environ["LD_LIBRARY_PATH"] = ":".join(new_ld_paths)

        # 3. Precarga con ctypes
        loaded_count = 0
        for lib_name in libs_to_preload:
            # Buscar la librería en todas las rutas nvidia detectadas
            found = False
            for path in nvidia_paths:
                # Buscar patrón incluyendo versión (ej: libcudnn_ops.so.9)
                # glob permite encontrar libcudnn_ops.so.9.1.0 o enlaces
                candidates = list(path.glob(f"{lib_name}*"))
                if candidates:
                    # Preferir la versión más corta (suele ser el symlink .so o .so.9)
                    # O simplemente tomar el primero
                    target_lib = sorted(candidates, key=lambda x: len(str(x)))[0]

                    try:
                        ctypes.CDLL(str(target_lib), mode=ctypes.RTLD_GLOBAL)
                        loaded_count += 1
                        found = True
                        break
                    except OSError:
                        continue  # Intentar siguiente ruta o ignorar si falla

            if not found:
                # No es crítico fallar aquí, quizás no está instalada o no se necesita
                pass

        logger.info(f"entorno gpu configurado: {len(nvidia_paths)} rutas, {loaded_count} libs precargadas")

    except Exception as e:
        logger.warning(f"fallo autoconfiguración gpu: {e}")
