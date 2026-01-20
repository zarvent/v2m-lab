
"""
Registro Genérico de Proveedores (Provider Registry).

Implementa el patrón **PROVIDER REGISTRY** que permite registrar y resolver
implementaciones concretas de servicios (LLM, Transcripción) de forma dinámica
en tiempo de ejecución.

Esto elimina el acoplamiento fuerte ("Vendor Lock-in") y permite la extensibilidad
futura (Open-Closed Principle) sin modificar el código del núcleo.

Patrones utilizados:
    - **Service Locator**: Simplificado vía registro estático.
    - **Factory**: Implícito al resolver proveedores por nombre.
    - **Generic Typing**: Uso de `TypeVar` y `Generic` para seguridad de tipos estricta.
"""




class ProviderNotFoundError(Exception):
    """
    Error lanzado cuando se intenta resolver un proveedor no registrado.
    """

    def __init__(self, provider_name: str, available: list[str]) -> None:
        self.provider_name = provider_name
        self.available = available
        available_str = ", ".join(available) if available else "(ninguno)"
        super().__init__(f"Proveedor '{provider_name}' no encontrado. Disponibles: {available_str}")


class ProviderRegistry[T]:
    """
    Registro Genérico Tipado para Proveedores de Servicios.

    Permite registrar implementaciones concretas de una interfaz base (T)
    y resolverlas por nombre en tiempo de ejecución. Diseñado para ser instanciado
    una vez por tipo de servicio.

    Atributos:
        _providers: Diccionario interno que mapea nombres (str) a clases (Type[T]).

    Ejemplo:
        Crear un registro para servicios LLM:

        ```python
        from v2m.application.llm_service import LLMService

        llm_registry = ProviderRegistry[LLMService]()
        llm_registry.register("local", LocalLLMService)
        llm_registry.register("gemini", GeminiLLMService)

        # Resolver por nombre desde la configuración
        ProviderClass = llm_registry.get("local")
        service = ProviderClass()
        ```
    """

    def __init__(self) -> None:
        """Inicializa el registro vacío."""
        self._providers: dict[str, type[T]] = {}

    def register(self, name: str, provider_class: type[T]) -> None:
        """
        Registra un proveedor bajo un nombre único.

        Args:
            name: Identificador único del proveedor (ej: "whisper", "local").
                  Debe coincidir con el valor usado en `config.toml`.
            provider_class: La clase que implementa la interfaz T.

        Nota:
            Si el nombre ya existe, se sobrescribe. Esto es útil para
            pruebas (mocks) o configuraciones personalizadas.
        """
        self._providers[name] = provider_class

    def get(self, name: str) -> type[T]:
        """
        Resuelve un proveedor por su nombre.

        Args:
            name: Identificador del proveedor a resolver.

        Returns:
            Type[T]: La clase del proveedor (no una instancia).

        Raises:
            ProviderNotFoundError: Si el nombre no está registrado.
        """
        if name not in self._providers:
            raise ProviderNotFoundError(name, self.available())
        return self._providers[name]

    def available(self) -> list[str]:
        """
        Lista los nombres de todos los proveedores registrados.

        Returns:
            list[str]: Lista de identificadores disponibles.
        """
        return list(self._providers.keys())

    def __contains__(self, name: str) -> bool:
        """Permite usar el operador `in`: `if "whisper" in registry`."""
        return name in self._providers

    def __len__(self) -> int:
        """Cantidad de proveedores registrados."""
        return len(self._providers)
