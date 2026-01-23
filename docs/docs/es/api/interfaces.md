---
title: Protocolos y Contratos
description: Definiciones de protocolos (interfaces) y contratos de middleware.
status: stable
last_update: 2026-01-23
language: Native Latin American Spanish
---

# Protocolos y Contratos

Esta página documenta los protocolos (interfaces) que definen los contratos del sistema en el "Estado del Arte 2026".

## Workflows (Protocolo)

Los flujos de trabajo siguen un protocolo estándar para asegurar que la API pueda interactuar con ellos de forma genérica.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Workflow(Protocol):
    async def execute(self, *args, **kwargs):
        """Punto de entrada principal para la ejecución del flujo."""
        ...
```

## Adaptadores de Características

Cada característica (`Feature`) define su propia interfaz mediante protocolos de Python para permitir el intercambio de implementaciones (ej: cambiar `Gemini` por `Ollama`).

### LLMProvider

```python
class LLMProvider(Protocol):
    async def process(self, text: str, system_prompt: str) -> str:
        """Procesa texto usando un modelo de lenguaje."""
```

### AudioSource

```python
class AudioSource(Protocol):
    def read(self, frames: int) -> np.ndarray:
        """Lee frames de audio del buffer."""
```
