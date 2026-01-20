# core

The application core contains fundamental components shared by all system layers. This is where main abstractions and communication mechanisms are defined.

## Content

- `cqrs/` - Command Query Responsibility Segregation pattern implementation
- `di/` - Dependency injection container
- `interfaces.py` - Port definitions (abstract interfaces) for adapters
- `ipc_protocol.py` - Inter-process communication protocol definition
- `logging.py` - Structured logging system configuration

## Purpose

This module aims to decouple high-level components from implementation details by providing clear interfaces and agnostic communication mechanisms.
