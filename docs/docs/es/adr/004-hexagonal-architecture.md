# ADR-004: Arquitectura Hexagonal (Puertos y Adaptadores)

## Estado

Aceptada

## Fecha

2024-03-01

## Contexto

Voice2Machine comenzó como un script monolítico de ~200 líneas. Al crecer en funcionalidad, enfrentamos problemas típicos de código acoplado:

1. **Testing difícil**: Mocks de GPU, audio, API externa
2. **Cambios cascada**: Modificar Whisper requería tocar 5+ archivos
3. **Vendor lock-in**: Cambiar de Ollama a Gemini requería refactor masivo
4. **Responsabilidades difusas**: No estaba claro dónde poner nueva lógica

### Requisitos:

- Núcleo de negocio agnóstico a frameworks
- Adaptadores intercambiables (ej: cambiar Whisper por otro ASR)
- Testabilidad sin hardware real
- Boundaries claros entre capas

## Decisión

**Adoptar Arquitectura Hexagonal (Ports & Adapters)** como patrón estructural.

### Estructura de carpetas:

```
src/v2m/
├── core/           # Configuración, logging, interfaces base
├── domain/         # Modelos, puertos (interfaces), errores
├── services/       # Orchestrator, coordinación
└── infrastructure/ # Adaptadores (Whisper, Audio, LLM)
```

### Implementación de puertos:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class TranscriptionService(Protocol):
    async def transcribe(self, audio: bytes) -> str: ...
```

Los adaptadores implementan los puertos:

```python
class WhisperAdapter:
    async def transcribe(self, audio: bytes) -> str:
        # Implementación concreta con faster-whisper
```

## Consecuencias

### Positivas

- ✅ **Testing aislado**: Tests unitarios sin GPU ni red
- ✅ **Flexibilidad**: Cambiar Gemini por Ollama es editar 1 archivo
- ✅ **Onboarding**: Estructura predecible y documentada
- ✅ **Type safety**: `Protocol` + mypy detecta incompatibilidades en compile time

### Negativas

- ⚠️ **Más archivos**: ~20 archivos vs ~5 del script original
- ⚠️ **Indirección**: Hay que navegar entre capas para entender flujo completo
- ⚠️ **Overhead inicial**: Setup más complejo para features simples

## Alternativas Consideradas

### Clean Architecture (Uncle Bob)

- **Rechazado**: Demasiadas capas (Entities, Use Cases, Interface Adapters, Frameworks) para el scope.

### MVC/MVP

- **Rechazado**: Orientado a UI, no aplica bien a un daemon backend.

### Simple Modules

- **Rechazado**: En la práctica volvíamos al acoplamiento original.

## Referencias

- [Alistair Cockburn - Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Netflix - Ready for changes with Hexagonal Architecture](https://netflixtechblog.com/ready-for-changes-with-hexagonal-architecture-b315ec967749)
