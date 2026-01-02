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
registro genérico de providers para servicios de la aplicación

implementa el patrón **PROVIDER REGISTRY** que permite registrar y resolver
implementaciones concretas de servicios (LLM, transcripción) de forma dinámica.
esto elimina vendor lock-in y permite extensibilidad futura sin modificar código core.

patrones utilizados
    - **SERVICE LOCATOR** simplificado via registry estático
    - **FACTORY** implícito al resolver providers por nombre
    - **GENERIC TYPING** (python 3.12+) para type-safety

example
    registrar un provider personalizado::

        from v2m.core.providers import transcription_registry, TranscriptionService

        class MiTranscripcion(TranscriptionService):
            def start_recording(self) -> None: ...
            def stop_and_transcribe(self) -> str: ...

        transcription_registry.register("mi_modelo", MiTranscripcion)

    resolver desde el DI container::

        provider_class = transcription_registry.get(config.transcription.backend)
        service = provider_class()
"""

from typing import Generic, TypeVar

T = TypeVar("T")


class ProviderNotFoundError(Exception):
    """error lanzado cuando se intenta resolver un provider no registrado"""

    def __init__(self, provider_name: str, available: list[str]) -> None:
        self.provider_name = provider_name
        self.available = available
        available_str = ", ".join(available) if available else "(ninguno)"
        super().__init__(
            f"provider '{provider_name}' no encontrado. "
            f"disponibles: {available_str}"
        )


class ProviderRegistry(Generic[T]):
    """
    registry genérico tipado para providers de servicios

    permite registrar implementaciones concretas de una interfaz base (T)
    y resolverlas por nombre en runtime. diseñado para ser instanciado
    una vez por tipo de servicio (LLM, transcripción, etc.)

    attributes
        _providers: diccionario interno que mapea nombres a clases

    example
        crear un registry para servicios LLM::

            from v2m.application.llm_service import LLMService

            llm_registry = ProviderRegistry[LLMService]()
            llm_registry.register("local", LocalLLMService)
            llm_registry.register("gemini", GeminiLLMService)

            # resolver por nombre de config
            Provider = llm_registry.get("local")
            service = Provider()
    """

    def __init__(self) -> None:
        """inicializa el registry vacío"""
        self._providers: dict[str, type[T]] = {}

    def register(self, name: str, provider_class: type[T]) -> None:
        """
        registra un provider bajo un nombre único

        args
            name: identificador único del provider (ej: "whisper", "local")
                  debe coincidir con el valor usado en config.toml
            provider_class: clase que implementa la interfaz T

        note
            si el nombre ya existe, se sobrescribe silenciosamente.
            esto permite override en tests o configuraciones custom.
        """
        self._providers[name] = provider_class

    def get(self, name: str) -> type[T]:
        """
        resuelve un provider por nombre

        args
            name: identificador del provider a resolver

        returns
            la clase del provider (no una instancia)

        raises
            ProviderNotFoundError: si el nombre no está registrado
        """
        if name not in self._providers:
            raise ProviderNotFoundError(name, self.available())
        return self._providers[name]

    def available(self) -> list[str]:
        """
        lista los nombres de todos los providers registrados

        returns
            lista de identificadores disponibles

        example
            >>> registry.available()
            ["whisper", "vosk", "custom"]
        """
        return list(self._providers.keys())

    def __contains__(self, name: str) -> bool:
        """permite usar 'in' operator: if "whisper" in registry"""
        return name in self._providers

    def __len__(self) -> int:
        """cantidad de providers registrados"""
        return len(self._providers)
