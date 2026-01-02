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
módulo de registros de providers para servicios model-agnostic

expone los registries globales para LLM y transcripción que son utilizados
por el DI container para resolver implementaciones concretas basándose
en la configuración del usuario

registries disponibles
    - ``llm_registry`` para servicios de modelos de lenguaje
    - ``transcription_registry`` para servicios de transcripción de audio

example
    importar y usar los registries::

        from v2m.core.providers import llm_registry, transcription_registry

        # verificar providers disponibles
        print(llm_registry.available())  # ["local", "gemini"]
        print(transcription_registry.available())  # ["whisper"]

        # resolver por configuración
        LLMClass = llm_registry.get(config.llm.backend)
        TranscriptionClass = transcription_registry.get(config.transcription.backend)
"""

from v2m.application.llm_service import LLMService
from v2m.application.transcription_service import TranscriptionService
from v2m.core.providers.provider_registry import ProviderNotFoundError, ProviderRegistry

# --- registries globales ---
# se crean una única vez al importar el módulo
# los providers se auto-registran al ser importados en container.py

llm_registry: ProviderRegistry[LLMService] = ProviderRegistry()
"""registry para servicios LLM (local, gemini, futuro: openai, anthropic, custom)"""

transcription_registry: ProviderRegistry[TranscriptionService] = ProviderRegistry()
"""registry para servicios de transcripción (whisper, futuro: vosk, speechbrain, custom)"""

__all__ = [
    "ProviderNotFoundError",
    "ProviderRegistry",
    "llm_registry",
    "transcription_registry",
]
