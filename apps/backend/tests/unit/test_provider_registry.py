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
tests unitarios para el sistema de provider registry

verifica el correcto funcionamiento del ProviderRegistry incluyendo:
- registro de providers
- resolución por nombre
- manejo de errores para providers no encontrados
- listado de providers disponibles
"""

import pytest
from abc import ABC, abstractmethod


class MockInterface(ABC):
    """interfaz mock para tests"""
    @abstractmethod
    def do_something(self) -> str:
        pass


class MockProviderA(MockInterface):
    """provider mock A"""
    def do_something(self) -> str:
        return "A"


class MockProviderB(MockInterface):
    """provider mock B"""
    def do_something(self) -> str:
        return "B"


class TestProviderRegistry:
    """tests para el ProviderRegistry genérico"""

    def test_register_and_get(self):
        """test: registrar un provider y recuperarlo por nombre"""
        from v2m.core.providers.provider_registry import ProviderRegistry

        registry = ProviderRegistry[MockInterface]()
        registry.register("mock_a", MockProviderA)

        resolved = registry.get("mock_a")
        assert resolved is MockProviderA

        # verificar que la clase funciona
        instance = resolved()
        assert instance.do_something() == "A"

    def test_get_nonexistent_raises_error(self):
        """test: resolver un provider que no existe lanza ProviderNotFoundError"""
        from v2m.core.providers.provider_registry import ProviderRegistry, ProviderNotFoundError

        registry = ProviderRegistry[MockInterface]()
        registry.register("existing", MockProviderA)

        with pytest.raises(ProviderNotFoundError) as exc_info:
            registry.get("nonexistent")

        # verificar que el error contiene info útil
        assert "nonexistent" in str(exc_info.value)
        assert "existing" in str(exc_info.value)  # debe mostrar los disponibles

    def test_available_returns_registered_names(self):
        """test: available() retorna lista de nombres registrados"""
        from v2m.core.providers.provider_registry import ProviderRegistry

        registry = ProviderRegistry[MockInterface]()
        registry.register("provider_a", MockProviderA)
        registry.register("provider_b", MockProviderB)

        available = registry.available()
        assert len(available) == 2
        assert "provider_a" in available
        assert "provider_b" in available

    def test_contains_operator(self):
        """test: operador 'in' funciona correctamente"""
        from v2m.core.providers.provider_registry import ProviderRegistry

        registry = ProviderRegistry[MockInterface]()
        registry.register("exists", MockProviderA)

        assert "exists" in registry
        assert "not_exists" not in registry

    def test_len_returns_provider_count(self):
        """test: len() retorna cantidad de providers registrados"""
        from v2m.core.providers.provider_registry import ProviderRegistry

        registry = ProviderRegistry[MockInterface]()
        assert len(registry) == 0

        registry.register("a", MockProviderA)
        assert len(registry) == 1

        registry.register("b", MockProviderB)
        assert len(registry) == 2

    def test_register_overwrites_existing(self):
        """test: registrar con mismo nombre sobrescribe el anterior"""
        from v2m.core.providers.provider_registry import ProviderRegistry

        registry = ProviderRegistry[MockInterface]()
        registry.register("provider", MockProviderA)
        registry.register("provider", MockProviderB)

        resolved = registry.get("provider")
        assert resolved is MockProviderB  # debe ser el último registrado


class TestGlobalRegistries:
    """tests para los registries globales llm_registry y transcription_registry"""

    def test_llm_registry_exists(self):
        """test: llm_registry está disponible y es del tipo correcto"""
        from v2m.core.providers import llm_registry, ProviderRegistry

        assert llm_registry is not None
        assert isinstance(llm_registry, ProviderRegistry)

    def test_transcription_registry_exists(self):
        """test: transcription_registry está disponible y es del tipo correcto"""
        from v2m.core.providers import transcription_registry, ProviderRegistry

        assert transcription_registry is not None
        assert isinstance(transcription_registry, ProviderRegistry)

    def test_can_register_in_global_registry(self):
        """test: se puede registrar un provider en el registry global"""
        from v2m.core.providers import llm_registry

        # nota: esto es un test destructivo, modifica el estado global
        # pero en tests es aceptable
        llm_registry.register("test_provider", MockProviderA)
        assert "test_provider" in llm_registry
