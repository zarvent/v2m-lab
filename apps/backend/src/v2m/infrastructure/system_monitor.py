
"""
Servicio de Monitoreo del Sistema.

Este servicio se encarga de recolectar métricas del sistema en tiempo real.
Utiliza `v2m_engine` (Rust) para métricas de CPU/RAM con bajo overhead, con fallback
automático a `psutil` si Rust no está disponible. Las métricas de GPU se obtienen
vía `torch.cuda`.

Se adhiere al Principio de Responsabilidad Única (SRP), proveyendo solo datos de observación
sin realizar acciones sobre el sistema.
"""

import logging
from types import ModuleType
from typing import Any

import psutil

logger = logging.getLogger(__name__)

# Intenta importar el monitor Rust
try:
    from v2m_engine import SystemMonitor as RustSystemMonitor

    HAS_RUST_MONITOR = True
    logger.info("🚀 monitor de sistema rust v2m_engine cargado")
except ImportError:
    HAS_RUST_MONITOR = False
    logger.warning("⚠️ monitor de sistema rust no disponible, usando fallback python")


class SystemMonitor:
    """
    Monitor de recursos del sistema para observabilidad en tiempo real.

    Provee métricas de RAM, CPU y GPU (si está disponible).
    Optimizado para minimizar overhead mediante el uso de Rust y caché de metadatos estáticos.
    """

    def __init__(self) -> None:
        """Inicializa el monitor y cachea información estática para optimizar polling."""
        # Motor Rust (Opcional)
        self._rust_monitor = RustSystemMonitor() if HAS_RUST_MONITOR else None

        # Optimización: Cachear módulo torch para evitar importación repetida
        self._torch: ModuleType | None = None
        self._gpu_available = self._check_gpu_availability()

        # Optimización: Cachear métricas estáticas (Total RAM, GPU Name)
        # Esto evita syscalls y llamadas a driver redundantes en cada ciclo de polling
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
        if self._gpu_available and self._torch:
            try:
                device = self._torch.cuda.current_device()
                props = self._torch.cuda.get_device_properties(device)
                self._gpu_static_info = {"name": props.name, "vram_total_mb": round(props.total_memory / (1024**2), 2)}
            except Exception as e:
                logger.warning(f"fallo al cachear info gpu: {e}")
                self._gpu_available = False

        logger.info(
            "monitor de sistema inicializado",
            extra={"gpu_disponible": self._gpu_available, "ram_total_gb": self._ram_total_gb},
        )

    def _check_gpu_availability(self) -> bool:
        """Verifica si hay una GPU NVIDIA disponible via torch.cuda."""
        try:
            import torch

            # Optimización: Guardar referencia al módulo para reuso en polling
            self._torch = torch
            return torch.cuda.is_available()
        except ImportError:
            logger.warning("torch no disponible, monitoreo gpu deshabilitado")
            return False
        except Exception as e:
            logger.warning(f"fallo al verificar disponibilidad gpu: {e}")
            return False

    def get_system_metrics(self) -> dict[str, Any]:
        """
        Obtiene una instantánea de las métricas actuales del sistema.

        Returns:
            dict[str, Any]: Diccionario con claves 'ram', 'cpu', 'gpu' (opcional).
        """
        if self._rust_monitor:
            # Actualizar snapshot en Rust
            self._rust_monitor.update()

        metrics = {
            "ram": self._get_ram_usage(),
            "cpu": self._get_cpu_usage(),
        }

        if self._gpu_available:
            metrics["gpu"] = self._get_gpu_usage()

        return metrics

    def _get_ram_usage(self) -> dict[str, float]:
        """Retorna uso de memoria RAM en GB y porcentaje."""
        if self._rust_monitor:
            _, used, percent = self._rust_monitor.get_ram_usage()
            return {"total_gb": self._ram_total_gb, "used_gb": round(used / (1024**3), 2), "percent": round(percent, 1)}

        mem = psutil.virtual_memory()
        return {
            "total_gb": self._ram_total_gb,  # Usar valor cacheado
            "used_gb": round(mem.used / (1024**3), 2),
            "percent": mem.percent,
        }

    def _get_cpu_usage(self) -> dict[str, Any]:
        """Retorna uso de CPU global."""
        if self._rust_monitor:
            return {"percent": round(self._rust_monitor.get_cpu_usage(), 1)}

        return {"percent": psutil.cpu_percent(interval=None)}

    def _get_gpu_usage(self) -> dict[str, Any]:
        """
        Retorna uso real de GPU usando torch.cuda.

        Returns:
            dict[str, Any]: Métricas de GPU: name, vram_used_mb, vram_total_mb, temp_c.
        """
        try:
            # Optimización: Usar referencia cacheada self._torch
            # Evita búsqueda en sys.modules cada ciclo
            if not self._torch or not self._torch.cuda.is_available():
                return {"name": "N/A", "vram_used_mb": 0, "vram_total_mb": 0, "temp_c": 0}

            device = self._torch.cuda.current_device()
            # Usar estáticos cacheados
            static = self._gpu_static_info

            # VRAM metrics en MB (Dinámico)
            vram_reserved = self._torch.cuda.memory_reserved(device) / (1024**2)

            # SOTA 2026: Usar Rust para temperatura nativa via NVML si está disponible
            gpu_temp = self._rust_monitor.get_gpu_temp() if self._rust_monitor else 0

            return {
                "name": static.get("name", "Unknown"),
                "vram_used_mb": round(vram_reserved, 2),
                "vram_total_mb": static.get("vram_total_mb", 0),
                "temp_c": gpu_temp,
            }
        except Exception as e:
            logger.error(f"fallo obteniendo métricas gpu: {e}", exc_info=True)
            return {"name": "Error", "vram_used_mb": 0, "vram_total_mb": 0, "temp_c": 0}
