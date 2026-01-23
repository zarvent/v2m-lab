"""Paquete de la API (SOTA 2026)."""

from v2m.api.schemas import (
    HealthResponse,
    LLMResponse,
    ProcessTextRequest,
    StatusResponse,
    ToggleResponse,
    TranslateTextRequest,
)

__all__ = [
    "ToggleResponse",
    "StatusResponse",
    "LLMResponse",
    "ProcessTextRequest",
    "TranslateTextRequest",
    "HealthResponse",
]
