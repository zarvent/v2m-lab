"""Pruebas unitarias del SystemMonitor.

Propósito
---------
Verificar que el SystemMonitor recolecte métricas del sistema correctamente
y maneje gracefully la ausencia de GPU.

Este archivo verifica
---------------------
    * Que SystemMonitor se inicialice sin errores.
    * Que get_system_metrics retorne estructura válida con RAM y CPU.
    * Que GPU detection falle gracefully si torch no está disponible.
    * Que las métricas de GPU sean opcionales y no rompan el sistema.

Ejecución
---------
    >>> pytest tests/unit/test_system_monitor.py -v
"""

from v2m.infrastructure.system_monitor import SystemMonitor


def test_system_monitor_initialization() -> None:
    """Verifica que SystemMonitor se inicialice correctamente."""
    monitor = SystemMonitor()
    assert monitor is not None
    assert isinstance(monitor._gpu_available, bool)


def test_get_system_metrics_structure() -> None:
    """Verifica que get_system_metrics retorne estructura válida.

    Validación de estructura
    ------------------------
    - RAM metrics: total_gb, used_gb, percent
    - CPU metrics: percent
    - GPU metrics: opcional, solo si GPU disponible
    """
    monitor = SystemMonitor()
    metrics = monitor.get_system_metrics()

    # Validar estructura básica (RAM y CPU siempre presentes)
    assert "ram" in metrics, "RAM metrics missing"
    assert "cpu" in metrics, "CPU metrics missing"

    # Validar RAM metrics
    assert "total_gb" in metrics["ram"], "RAM total_gb missing"
    assert "used_gb" in metrics["ram"], "RAM used_gb missing"
    assert "percent" in metrics["ram"], "RAM percent missing"

    # Validar tipos de RAM
    assert isinstance(metrics["ram"]["total_gb"], (int, float))
    assert isinstance(metrics["ram"]["used_gb"], (int, float))
    assert isinstance(metrics["ram"]["percent"], (int, float))

    # Validar rangos de RAM
    assert metrics["ram"]["total_gb"] > 0, "RAM total should be positive"
    assert metrics["ram"]["used_gb"] >= 0, "RAM used should be non-negative"
    assert 0 <= metrics["ram"]["percent"] <= 100, "RAM percent should be 0-100"

    # Validar CPU metrics
    assert "percent" in metrics["cpu"], "CPU percent missing"
    assert isinstance(metrics["cpu"]["percent"], (int, float))
    assert 0 <= metrics["cpu"]["percent"] <= 100, "CPU percent should be 0-100"


def test_gpu_metrics_optional() -> None:
    """Verifica que GPU metrics sean opcionales y no rompan el sistema.

    Comportamiento esperado
    -----------------------
    - Si GPU disponible: metrics["gpu"] debe existir con estructura válida
    - Si GPU no disponible: metrics["gpu"] puede no existir o estar vacío
    """
    monitor = SystemMonitor()
    metrics = monitor.get_system_metrics()

    # GPU es opcional
    if "gpu" in metrics:
        # Si existe, debe tener estructura válida
        assert "name" in metrics["gpu"], "GPU name missing"
        assert "vram_used_mb" in metrics["gpu"], "GPU vram_used_mb missing"
        assert "vram_total_mb" in metrics["gpu"], "GPU vram_total_mb missing"
        assert "temp_c" in metrics["gpu"], "GPU temp_c missing"

        # Validar tipos
        assert isinstance(metrics["gpu"]["name"], str)
        assert isinstance(metrics["gpu"]["vram_used_mb"], (int, float))
        assert isinstance(metrics["gpu"]["vram_total_mb"], (int, float))
        assert isinstance(metrics["gpu"]["temp_c"], (int, float))


def test_gpu_availability_graceful_fallback() -> None:
    """Verifica que GPU detection falle gracefully si torch no disponible.

    Casos de prueba
    ---------------
    1. torch disponible y GPU presente: _gpu_available = True
    2. torch disponible pero sin GPU: _gpu_available = False
    3. torch no disponible: _gpu_available = False (no debe lanzar excepción)
    """
    monitor = SystemMonitor()

    # No debe lanzar excepción incluso si torch no está disponible
    assert isinstance(monitor._gpu_available, bool)

    # Si GPU no disponible, get_system_metrics no debe incluir GPU o debe estar vacío
    if not monitor._gpu_available:
        metrics = monitor.get_system_metrics()
        # GPU no debe estar presente o debe tener valores por defecto
        if "gpu" in metrics:
            assert metrics["gpu"]["name"] in ["N/A", "Error"]
            assert metrics["gpu"]["vram_used_mb"] == 0
            assert metrics["gpu"]["vram_total_mb"] == 0
