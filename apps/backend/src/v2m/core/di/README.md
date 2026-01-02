# Dependency Injection

This module handles dependency injection (DI) for the entire application using a centralized container.

## Components

- `container.py` - Defines the `Container` class that instantiates and stores all services and handlers as singletons

## Responsibilities

- **Composition Root**: The only place where concrete implementations are known (e.g., `WhisperTranscriptionService`)
- **Wiring**: Injects necessary dependencies into class constructors (e.g., passing `NotificationInterface` to `StartRecordingHandler`)
- **Lifecycle**: Ensures heavy services (like ML models) are instantiated only once and reused

## Usage

To access a service from any point in the application (though it's recommended to do so only at entry points):

```python
from v2m.core.di.container import container
bus = container.get_command_bus()
```
