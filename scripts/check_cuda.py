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
verificación de cuda - ¿mi gpu funciona con v2m?

¿para qué sirve este script?
    v2m usa la gpu de tu computadora para transcribir audio rápidamente
    este script verifica que tu tarjeta gráfica nvidia esté configurada
    correctamente y lista para usar

¿cómo lo uso?
    simplemente ejecuta

    $ python scripts/check_cuda.py

¿qué debería ver si todo está bien?
    Python: /home/tu-usuario/v2m/venv/bin/python
    CUDA Available: True
    CUDA Device: NVIDIA GeForce RTX 3060
    ✅ Operación cuDNN básica exitosa

¿qué pasa si cuda no está disponible?
    el script mostrará "CUDA Available: False" en ese caso

    1 verifica que tengas drivers nvidia instalados
       $ nvidia-smi

    2 si eso falla instala los drivers
       $ sudo apt install nvidia-driver-535

    3 si tienes drivers pero cuda sigue sin funcionar prueba
       $ ./scripts/repair_libs.sh

nota para desarrolladores
    este script usa pytorch para detectar cuda y ejecuta una operación
    de convolución simple para verificar que cudnn funcione si la
    operación tiene éxito significa que todo el stack de gpu está
    funcionando correctamente
"""

import torch
import os
import sys


def check_cuda_availability() -> bool:
    """
    verifica si cuda y cudnn están funcionando

    ¿qué hace exactamente?
        1 muestra qué python estás usando
        2 muestra las rutas de librerías cuda
        3 prueba si cuda está disponible
        4 si lo está hace una prueba rápida con cudnn

    returns:
        true si todo funciona false si hay algún problema

    example
        >>> if check_cuda_availability():
        ...     print("Listo para usar GPU")
        ... else:
        ...     print("Usando CPU (más lento)")
    """
    print(f"Python: {sys.executable}")
    print(f"LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', 'Not Set')}")
    print(f"CUDA Available: {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        print(f"CUDA Device: {torch.cuda.get_device_name(0)}")
        try:
            # Intentar cargar algo que use cuDNN
            x = torch.randn(1, 1, 10, 10).cuda()
            conv = torch.nn.Conv2d(1, 1, 3).cuda()
            y = conv(x)
            print("✅ Operación cuDNN básica exitosa")
            return True
        except Exception as e:
            print(f"❌ Error en operación cuDNN: {e}")
            return False
    else:
        print("❌ CUDA no disponible")
        return False


if __name__ == "__main__":
    check_cuda_availability()
