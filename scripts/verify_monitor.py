
import sys
import logging

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

print("Modules before import:", "torch" in sys.modules)

try:
    from v2m.infrastructure.system_monitor import SystemMonitor

    print("Initializing monitor...")
    monitor = SystemMonitor()

    print("Modules after init:", "torch" in sys.modules)

    metrics = monitor.get_system_metrics()
    print("Metrics:", metrics)

    if "gpu" in metrics:
        print("GPU Metrics found:", metrics["gpu"])
    else:
        print("No GPU metrics available (expected if no GPU/driver)")

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
