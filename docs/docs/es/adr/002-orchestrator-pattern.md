# ADR-002: Reemplazo de CQRS/CommandBus por Orchestrator

## Estado

Aceptada

## Fecha

2025-01-15

## Contexto

El backend original implementaba el patrón **CQRS (Command Query Responsibility Segregation)** con un **CommandBus** para procesar acciones del usuario.

### Problemas identificados:

1. **Sobre-ingeniería**: Para un sistema con ~10 comandos, el overhead de CQRS era desproporcionado
2. **Indirección excesiva**: Command → CommandBus → Handler → Result → Response
3. **Boilerplate**: Cada nueva funcionalidad requería crear Command DTO + Handler + registrar en bus
4. **Debugging complejo**: Stack traces profundos oscurecían el flujo real
5. **Testing verbose**: Mocks de CommandBus en cada test

### Requisitos:

- Mantener separación de concerns (no acoplar API a infraestructura)
- Simplificar el flujo de control
- Reducir boilerplate para nuevas features
- Facilitar testing y debugging

## Decisión

**Reemplazar CQRS/CommandBus por un Orchestrator central** que coordina el flujo de trabajo directamente.

### Implementación:

```python
class Orchestrator:
    async def toggle(self) -> ToggleResponse: ...
    async def start(self) -> ToggleResponse: ...
    async def stop(self) -> ToggleResponse: ...
```

El Orchestrator:

- Expone métodos directos para cada operación
- Coordina adaptadores (AudioRecorder, WhisperAdapter, LLMProvider)
- Mantiene el estado del sistema
- Emite eventos a WebSocket clients

## Consecuencias

### Positivas

- ✅ **Flujo explícito**: API → Orchestrator → Adapters (3 capas vs 6+)
- ✅ **Menos código**: Eliminamos ~500 LOC de CommandBus infrastructure
- ✅ **Debugging simple**: Stack traces claros y cortos
- ✅ **Testing directo**: Mockeamos adaptadores, no buses abstractos
- ✅ **Onboarding**: Nuevos devs entienden el sistema en minutos

### Negativas

- ⚠️ **Menos extensible**: Agregar un "middleware" global es menos trivial
- ⚠️ **Orchestrator "god object"**: Riesgo de que crezca demasiado (mitigado con composición)

## Alternativas Consideradas

### Mantener CQRS simplificado

- **Rechazado**: Incluso simplificado, el overhead conceptual no se justificaba.

### Event Sourcing

- **Rechazado**: Sobre-ingeniería aún mayor para el caso de uso actual.

### Simple Functions (sin clase)

- **Rechazado**: Perdíamos gestión de estado y lifecycle.

## Referencias

- [Martin Fowler on CQRS](https://martinfowler.com/bliki/CQRS.html)
- [When not to use CQRS](https://www.cqrs.nu/Faq/when-to-use-cqrs)
