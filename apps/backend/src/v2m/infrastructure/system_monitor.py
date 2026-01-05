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
Servicio de Monitoreo del Sistema.

Este servicio se encarga de recolectar métricas del sistema en tiempo real.
Utiliza `v2m_engine` (Rust) para métricas de CPU/RAM con bajo overhead, y si es posible,
para métricas de GPU vía NVML, evitando la dependencia de `nvidia-ml-py` (pynvml) en Python
cuando el motor Rust está disponible y compilado con soporte NVIDIA.
"""

import atexit
import logging
from typing import Any, TypedDict

import psutil

try:
    import pynvml
    HAS_PYNVML = True
except ImportError:
    HAS_PYNVML = False

logger = logging.getLogger(__name__)

# Intenta importar el monitor Rust
try:
    from v2m_engine import SystemMonitor as RustSystemMonitor

    HAS_RUST_MONITOR = True
    logger.info("🚀 monitor de sistema rust v2m_engine cargado")
except ImportError:
    HAS_RUST_MONITOR = False
    logger.warning("⚠️ monitor de sistema rust no disponible, usando fallback python")


class GPUMetrics(TypedDict):
    """Métricas estructuradas de GPU."""
    name: str
    vram_used_mb: float
    vram_total_mb: float
    temp_c: int


class SystemMonitor:
    """
    Monitor de recursos del sistema para observabilidad en tiempo real.
    """

    def __init__(self) -> None:
        """Inicializa el monitor y cachea información estática para optimizar polling."""
        self._rust_monitor = RustSystemMonitor() if HAS_RUST_MONITOR else None

        # Estrategia híbrida: Intenta usar Rust para GPU primero si retorna métricas válidas
        self._use_rust_gpu = False
        if self._rust_monitor:
            temp, used, total = self._rust_monitor.get_gpu_metrics()
            if total > 0:
                self._use_rust_gpu = True
                logger.info("Usando monitor GPU nativo de Rust (v2m_engine)")

        # Si Rust no tiene soporte GPU (feature flag off o sin driver), intentar pynvml
        self._nvml_handle: Any | None = None
        self._gpu_available = self._use_rust_gpu or self._init_gpu_monitoring()

        # Registrar limpieza para liberar handle de NVML si se usa
        if not self._use_rust_gpu:
            atexit.register(self._shutdown)

        # Cachear métricas estáticas (Total RAM, GPU Name)
        try:
            if self._rust_monitor:
                self._rust_monitor.update()
                total_bytes, _, _ = self._rust_monitor.get_ram_usage()
                self._ram_total_gb = round(total_bytes / (1024**3), 2)
            else:
                mem = psutil.virtual_memory()
                self._ram_total_gb = round(mem.total / (1024**3), 2)
        except Exception as e:
            logger.warning(f"fallo al cachear info ram: {e}")
            self._ram_total_gb = 0.0

        self._gpu_static_info: dict[str, Any] = {}

        # Si usamos Rust para métricas, aún necesitamos el nombre estático
        # Rust `get_gpu_metrics` no devuelve el nombre, así que si queremos nombre,
        # podríamos necesitar pynvml solo para init o extender Rust.
        # Por simplicidad y eficiencia, si usamos Rust, aceptamos "NVIDIA GPU" o
        # intentamos pynvml solo para el nombre una vez.
        if self._gpu_available:
            if self._nvml_handle:
                try:
                    name = pynvml.nvmlDeviceGetName(self._nvml_handle)
                    if isinstance(name, bytes):
                        name = name.decode("utf-8")
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(self._nvml_handle)
                    self._gpu_static_info = {
                        "name": name,
                        "vram_total_mb": round(mem_info.total / (1024**2), 2)
                    }
                except Exception:
                    pass
            elif self._use_rust_gpu:
                 # Si usamos Rust y pynvml no está, no tenemos el nombre exacto fácilmente
                 # sin extender más la API Rust. Asumimos genérico.
                 self._gpu_static_info = {"name": "NVIDIA GPU (Rust)"}


        logger.info(
            "monitor de sistema inicializado",
            extra={"gpu_disponible": self._gpu_available, "ram_total_gb": self._ram_total_gb},
        )

    def _shutdown(self) -> None:
        """Libera recursos del monitor (solo si usa pynvml directamente)."""
        if HAS_PYNVML and self._gpu_available and not self._use_rust_gpu:
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass

    def _init_gpu_monitoring(self) -> bool:
        """Inicializa monitoreo GPU vía NVML (Python fallback)."""
        if not HAS_PYNVML:
            return False

        try:
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count > 0:
                self._nvml_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                return True
            return False
        except pynvml.NVMLError as e:
            logger.warning(f"fallo al inicializar nvml (python): {e}")
            return False
        except Exception as e:
            logger.warning(f"error inesperado inicializando gpu (python): {e}")
            return False

    def get_system_metrics(self) -> dict[str, Any]:
        """Obtiene una instantánea de las métricas actuales del sistema."""
        if self._rust_monitor:
            self._rust_monitor.update()

        metrics = {
            "ram": self._get_ram_usage(),
            "cpu": self._get_cpu_usage(),
        }

        if self._gpu_available:
            metrics["gpu"] = self._get_gpu_usage()

        return metrics

    def _get_ram_usage(self) -> dict[str, float]:
        if self._rust_monitor:
            _, used, percent = self._rust_monitor.get_ram_usage()
            return {"total_gb": self._ram_total_gb, "used_gb": round(used / (1024**3), 2), "percent": round(percent, 1)}

        mem = psutil.virtual_memory()
        return {
            "total_gb": self._ram_total_gb,
            "used_gb": round(mem.used / (1024**3), 2),
            "percent": mem.percent,
        }

    def _get_cpu_usage(self) -> dict[str, Any]:
        if self._rust_monitor:
            return {"percent": round(self._rust_monitor.get_cpu_usage(), 1)}

        return {"percent": psutil.cpu_percent(interval=None)}

    def _get_gpu_usage(self) -> GPUMetrics:
        """Retorna uso real de GPU."""
        # 1. Camino Rápido: Rust
        if self._use_rust_gpu and self._rust_monitor:
            temp, used, total = self._rust_monitor.get_gpu_metrics()
            # Si Rust devuelve 0 total, algo falló temporalmente, pero seguimos confiando en él
            return {
                "name": self._gpu_static_info.get("name", "Unknown"),
                "vram_used_mb": round(used, 2),
                "vram_total_mb": round(total, 2) if total > 0 else self._gpu_static_info.get("vram_total_mb", 0.0),
                "temp_c": int(temp),
            }

        # 2. Camino Lento: Python pynvml
        try:
            if not self._nvml_handle:
                return {"name": "N/A", "vram_used_mb": 0.0, "vram_total_mb": 0.0, "temp_c": 0}

            mem_info = pynvml.nvmlDeviceGetMemoryInfo(self._nvml_handle)
            temp = pynvml.nvmlDeviceGetTemperature(self._nvml_handle, pynvml.NVML_TEMPERATURE_GPU)

            static = self._gpu_static_info

            return {
                "name": static.get("name", "Unknown"),
                "vram_used_mb": round(mem_info.used / (1024**2), 2),
                "vram_total_mb": static.get("vram_total_mb", 0.0),
                "temp_c": temp,
            }
        except pynvml.NVMLError as e:
            logger.error(f"fallo nvml python: {e}")
            try:
                pynvml.nvmlInit()
                self._nvml_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            except:
                pass
            return {"name": "Error", "vram_used_mb": 0.0, "vram_total_mb": 0.0, "temp_c": 0}
        except Exception as e:
            logger.error(f"fallo inesperado gpu python: {e}")
            return {"name": "Error", "vram_used_mb": 0.0, "vram_total_mb": 0.0, "temp_c": 0}
