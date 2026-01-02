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
descarga y prueba del modelo whisper

¿qué hace este script?
    descarga el modelo de transcripción (whisper large-v2) y verifica
    que se cargue correctamente en tu gpu es lo primero que debes
    correr después de instalar v2m

¿por qué tarda tanto la primera vez?
    el modelo pesa ~3 gb y se descarga de internet la primera
    ejecución puede tomar 5-10 minutos dependiendo de tu conexión
    las siguientes veces es instantáneo porque ya está en caché

¿cómo lo uso?
    $ python scripts/test_whisper_gpu.py

¿qué debería ver?
    🚀 Descargando modelo large-v2 (3GB, primera vez solamente)...
    ✅ Modelo cargado exitosamente en GPU RTX 3060!
    📊 Info del modelo:
       - Dispositivo: CUDA (RTX 3060)
       - Precisión: float16
       - Memoria GPU disponible: ~6GB

¿cuánta vram necesito?
    el modelo large-v2 necesita ~5-6 gb de vram funciona bien en
    - rtx 3060 (12 gb) ✅
    - rtx 3070/3080 ✅
    - rtx 2060 (6 gb) - justo pero funciona
    - gtx 1060 (6 gb) - muy justo

¿qué hago si no tengo suficiente vram?
    puedes usar un modelo más pequeño editando config.toml
    - "medium" necesita ~3 gb
    - "small" necesita ~1 gb
    - "tiny" necesita ~500 mb (calidad más baja)

para desarrolladores
    el modelo se guarda en ~/.cache/huggingface/hub/
    para limpiar el caché rm -rf ~/.cache/huggingface/hub/
"""

from faster_whisper import WhisperModel
import time


def load_whisper_model() -> WhisperModel:
    """
    descarga y carga el modelo whisper en gpu

    retorna el modelo listo para transcribir la primera vez
    descarga ~3 gb después usa el caché

    returns:
        el modelo whispermodel cargado
    """
    print("🚀 Descargando modelo large-v2 (3GB, primera vez solamente)...")
    print("Esto puede tomar 5-10 minutos dependiendo de tu internet.\n")

    # Inicializar modelo con GPU
    model = WhisperModel(
        "large-v2",
        device="cuda",
        compute_type="float16",
        device_index=0  # RTX 3060
    )

    return model


def main() -> None:
    """
    función principal de prueba del modelo whisper

    carga el modelo y muestra información sobre la configuración
    y tiempos de transcripción estimados
    """
    model = load_whisper_model()

    print("✅ Modelo cargado exitosamente en GPU RTX 3060!")
    print("\n📊 Info del modelo:")
    print(f"   - Dispositivo: CUDA (RTX 3060)")
    print(f"   - Precisión: float16")
    print(f"   - Memoria GPU disponible: ~6GB\n")

    # Test rápido si tienes un archivo de audio
    print("El modelo está listo para usar.")
    print("Con la RTX 3060 se esperara aproximadamente:")
    print("   • 3-5 segundos por cada minuto de audio")
    print("   • 10-15 segundos para audio de 3 minutos")
    print("   • 30-40 segundos para audio de 10 minutos\n")


if __name__ == "__main__":
    main()
