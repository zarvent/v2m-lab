# ADR-002: Replacement of CQRS/CommandBus with Orchestrator

## Status

Accepted

## Date

2025-01-15

## Context

The original backend implemented the **CQRS (Command Query Responsibility Segregation)** pattern with a **CommandBus** to process user actions.

### Identified problems:

1. **Over-engineering**: For a system with ~10 commands, CQRS overhead was disproportionate
2. **Excessive indirection**: Command → CommandBus → Handler → Result → Response
3. **Boilerplate**: Each new feature required creating Command DTO + Handler + registering in bus
4. **Complex debugging**: Deep stack traces obscured the real flow
5. **Verbose testing**: CommandBus mocks in every test

### Requirements:

- Maintain separation of concerns (don't couple API to infrastructure)
- Simplify control flow
- Reduce boilerplate for new features
- Facilitate testing and debugging

## Decision

**Replace CQRS/CommandBus with a central Orchestrator** that coordinates workflow directly.

### Implementation:

```python
class Orchestrator:
    async def toggle(self) -> ToggleResponse: ...
    async def start(self) -> ToggleResponse: ...
    async def stop(self) -> ToggleResponse: ...
```

The Orchestrator:

- Exposes direct methods for each operation
- Coordinates adapters (AudioRecorder, WhisperAdapter, LLMProvider)
- Maintains system state
- Emits events to WebSocket clients

## Consequences

### Positive

- ✅ **Explicit flow**: API → Orchestrator → Adapters (3 layers vs 6+)
- ✅ **Less code**: Eliminated ~500 LOC of CommandBus infrastructure
- ✅ **Simple debugging**: Clear and short stack traces
- ✅ **Direct testing**: Mock adapters, not abstract buses
- ✅ **Onboarding**: New devs understand the system in minutes

### Negative

- ⚠️ **Less extensible**: Adding a global "middleware" is less trivial
- ⚠️ **Orchestrator "god object"**: Risk of growing too large (mitigated with composition)

## Alternatives Considered

### Keep simplified CQRS

- **Rejected**: Even simplified, the conceptual overhead wasn't justified.

### Event Sourcing

- **Rejected**: Even greater over-engineering for current use case.

### Simple Functions (no class)

- **Rejected**: Lost state management and lifecycle.

## References

- [Martin Fowler on CQRS](https://martinfowler.com/bliki/CQRS.html)
- [When not to use CQRS](https://www.cqrs.nu/Faq/when-to-use-cqrs)
