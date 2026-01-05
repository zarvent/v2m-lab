#!/usr/bin/env python3

# Este archivo es parte de voice2machine.
#
# voice2machine es software libre: puedes redistribuirlo y/o modificarlo
# bajo los términos de la Licencia Pública General GNU publicada por
# la Free Software Foundation, ya sea la versión 3 de la Licencia, o
# (a tu elección) cualquier versión posterior.
#
# voice2machine se distribuye con la esperanza de que sea útil,
# pero SIN NINGUNA GARANTÍA; ni siquiera la garantía implícita de
# COMERCIABILIDAD o IDONEIDAD PARA UN PROPÓSITO PARTICULAR. Consulta la
# Licencia Pública General GNU para más detalles.
#
# Deberías haber recibido una copia de la Licencia Pública General GNU
# junto con voice2machine. Si no, consulta <https://www.gnu.org/licenses/>.

"""
Verificación de Entorno CUDA - ¿Está mi GPU lista para V2M?

Propósito:
    Voice2Machine utiliza aceleración por hardware (GPU) para transcripción de baja latencia.
    Este script de diagnóstico valida que el stack completo de NVIDIA (Drivers -> CUDA -> cuDNN -> PyTorch)
    esté configurado correctamente.

Uso:
    $ python scripts/check_cuda.py

Salida esperada (Éxito):
    Python: .../venv/bin/python
    CUDA Disponible: True
    Dispositivo: NVIDIA GeForce RTX 4060
    ✅ Operación Tensor Core (cuDNN) exitosa

Resolución de problemas:
    Si "CUDA Disponible: False":
    1. Verifica drivers: `nvidia-smi`
    2. Reinstala dependencias: `./scripts/install.sh`
    3. Repara enlaces dinámicos: `./scripts/repair_libs.sh`
"""

import os
import sys

import torch


def check_cuda_availability() -> bool:
    """
    Realiza un diagnóstico completo del subsistema de GPU.

    Pasos de verificación:
        1. Entorno de ejecución (Ruta Python, LD_LIBRARY_PATH).
        2. Detección de dispositivo CUDA vía PyTorch.
        3. Prueba de estrés mínima (Convolución 2D) para validar cuDNN.

    Returns:
        bool: True si la GPU es completamente funcional para inferencia.
    """
    print(f"Intérprete Python: {sys.executable}")
    print(f"LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', 'No definido')}")

    cuda_available = torch.cuda.is_available()
    print(f"CUDA Disponible: {cuda_available}")

    if cuda_available:
        device_name = torch.cuda.get_device_name(0)
        print(f"Dispositivo Activo: {device_name}")

        try:
            # Prueba de humo para cuDNN (operación de convolución)
            # Esto falla si las librerías .so no están enlazadas correctamente
            x = torch.randn(1, 1, 10, 10).cuda()
            conv = torch.nn.Conv2d(1, 1, 3).cuda()
            _ = conv(x)
            print("✅ Operación Tensor Core (cuDNN) exitosa")
            return True
        except Exception as e:
            print(f"❌ Error crítico en operación GPU: {e}")
            print("Sugerencia: Ejecuta ./scripts/repair_libs.sh")
            return False
    else:
        print("❌ Aceleración GPU no disponible (Se usará CPU)")
        return False


if __name__ == "__main__":
    success = check_cuda_availability()
    sys.exit(0 if success else 1)
