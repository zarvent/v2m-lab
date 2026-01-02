# cqrs

Command Query Responsibility Segregation (CQRS) pattern implementation for system action management.

## Components

- `command.py` - Base class for all commands (state change intentions)
- `command_bus.py` - Mediator that receives commands and routes them to the corresponding handler
- `command_handler.py` - Base interface for logic that processes a specific command

## Flow

1. Client sends a request (e.g., start recording)
2. A `Command` object is created
3. The `CommandBus` receives the command
4. The bus finds the registered `CommandHandler` for that command
5. The handler executes the business logic

## Benefits

Decouples who invokes the action from who executes it, allowing for a cleaner architecture and testing each part in isolation.
