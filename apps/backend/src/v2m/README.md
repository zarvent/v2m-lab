# voice2machine package

This is the main voice2machine application package. It contains all business logic, infrastructure, and system configuration.

## Structure

The package follows a modified hexagonal architecture (ports and adapters):

- `application/` - Use cases and application logic
- `core/` - System core, interfaces, protocols, and shared utilities
- `domain/` - Business entities and domain errors
- `infrastructure/` - Concrete interface implementations (adapters)
- `gui/` - Graphical user interface (if applicable)

## Main Files

- `main.py` - Application entry point (CLI and daemon)
- `daemon.py` - Background process implementation
- `client.py` - Client to communicate with daemon via IPC
- `config.py` - Centralized configuration management
