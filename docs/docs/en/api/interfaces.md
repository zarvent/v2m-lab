---
title: Protocols and Contracts
description: Protocol (interfaces) and middleware contract definitions.
status: stable
last_update: 2026-01-23
language: US English
---

# Protocols and Contracts

This page documents the protocols (interfaces) that define system contracts in "State of the Art 2026".

## Workflows (Protocol)

Workflows follow a standard protocol to ensure the API can interact with them generically.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Workflow(Protocol):
    async def execute(self, *args, **kwargs):
        """Main entry point for workflow execution."""
        ...
```

## Feature Adapters

Each `Feature` defines its own interface using Python protocols to allow switching implementations (e.g., swapping `Gemini` for `Ollama`).

### LLMProvider

```python
class LLMProvider(Protocol):
    async def process(self, text: str, system_prompt: str) -> str:
        """Process text using a language model."""
```

### AudioSource

```python
class AudioSource(Protocol):
    def read(self, frames: int) -> np.ndarray:
        """Reads audio frames from buffer."""
```
