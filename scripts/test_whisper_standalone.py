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
prueba completa del pipeline de transcripción

¿para qué sirve?
    este script prueba todo el proceso de transcripción de principio
    a fin sin necesidad de hablar genera audio de prueba (silencio)
    y verifica que whisper pueda procesarlo

¿cuándo usarlo?
    - después de instalar v2m
    - después de actualizar dependencias
    - cuando la transcripción falla y no sabes por qué
    - para verificar que cuda funciona antes de usar v2m

¿cómo lo uso?
    $ python scripts/test_whisper_standalone.py

¿qué debería ver?
    1. Verificando entorno...
    LD_LIBRARY_PATH: /ruta/a/nvidia/libs
    2. Generando audio dummy (1 segundo de silencio)...
    3. Cargando modelo (device=cuda)...
    ✅ Modelo cargado en CUDA
    4. Transcribiendo...
    Detected language: es
    ✅ Transcripción completada

¿qué pasa si cuda falla?
    el script automáticamente intenta usar cpu verás

    ❌ Falló carga en CUDA: [error]
    Intentando CPU...
    ⚠️ Modelo cargado en CPU (Fallback)

    funciona pero será más lento para arreglar cuda
    $ ./scripts/repair_libs.sh

¿por qué usa el modelo "tiny"?
    para que la prueba sea rápida (~5 segundos) en producción
    v2m usa "large-v2" que es mucho más preciso pero más pesado

para desarrolladores
    el audio dummy es un array numpy de ceros (silencio) de 1 segundo
    a 16khz faster-whisper espera audio como numpy array float32
"""

import os
import sys
import numpy as np
from faster_whisper import WhisperModel
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_whisper")


def test_transcription() -> None:
    """
    prueba el pipeline completo entorno modelo transcripción

    genera audio de silencio y lo pasa por whisper para verificar
    que todo funcione si cuda falla intenta con cpu automáticamente

    el proceso
        1 verifica que ld_library_path esté configurado
        2 genera 1 segundo de audio silencioso
        3 carga whisper (primero cuda luego cpu como fallback)
        4 ejecuta una transcripción de prueba

    note
        el audio de silencio no producirá texto pero permite
        verificar que todo el pipeline funcione correctamente
    """
    print("1. Verificando entorno...")
    print(f"LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', 'Not Set')}")

    print("2. Generando audio dummy (1 segundo de silencio)...")
    # Generar 1 segundo de silencio a 16kHz
    audio = np.zeros(16000, dtype=np.float32)

    print("3. Cargando modelo (device=cuda)...")
    try:
        model = WhisperModel("tiny", device="cuda", compute_type="float16")
        print("✅ Modelo cargado en CUDA")
    except Exception as e:
        print(f"❌ Falló carga en CUDA: {e}")
        print("Intentando CPU...")
        try:
            model = WhisperModel("tiny", device="cpu", compute_type="int8")
            print("⚠️ Modelo cargado en CPU (Fallback)")
        except Exception as e2:
            print(f"❌ Falló carga en CPU también: {e2}")
            return

    print("4. Transcribiendo...")
    try:
        segments, info = model.transcribe(audio, beam_size=5)
        print(f"Detected language: {info.language}")
        for segment in segments:
            print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        print("✅ Transcripción completada")
    except Exception as e:
        print(f"❌ Error durante transcripción: {e}")

if __name__ == "__main__":
    test_transcription()
