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
Módulo de Registros de Proveedores (Service Providers).

Expone los Registros Globales para LLM y Transcripción, que son utilizados
por el Contenedor de Inyección de Dependencias (DI Container) para resolver
implementaciones concretas basándose en la configuración del usuario.

Registros Disponibles:
    - ``llm_registry``: Para servicios de Modelos de Lenguaje (Local, Gemini, etc.).
    - ``transcription_registry``: Para servicios de transcripción de audio (Whisper, etc.).

Ejemplo:
    Importar y usar los registros:

    ```python
    from v2m.core.providers import llm_registry, transcription_registry

    # Verificar proveedores disponibles
    print(llm_registry.available())  # ["local", "gemini"]
    print(transcription_registry.available())  # ["whisper"]

    # Resolver clase concreta por configuración
    LLMClass = llm_registry.get(config.llm.backend)
    ```
"""

from v2m.application.llm_service import LLMService
from v2m.application.transcription_service import TranscriptionService
from v2m.core.providers.provider_registry import ProviderNotFoundError, ProviderRegistry

# --- Registros Globales ---
# Se instancian una única vez al importar el módulo.
# Los proveedores concretos se registran al ser importados (generalmente en container.py).

llm_registry: ProviderRegistry[LLMService] = ProviderRegistry()
"""Registro para servicios LLM (local, gemini, ollama)."""

transcription_registry: ProviderRegistry[TranscriptionService] = ProviderRegistry()
"""Registro para servicios de transcripción (whisper)."""

__all__ = [
    "ProviderNotFoundError",
    "ProviderRegistry",
    "llm_registry",
    "transcription_registry",
]
