"""Esquemas de la API (Pydantic V2)."""

from pydantic import BaseModel, Field


class ToggleResponse(BaseModel):
    """Respuesta del endpoint /toggle."""

    status: str = Field(description="Estado actual: 'recording' o 'idle'")
    message: str = Field(description="Mensaje descriptivo para el usuario")
    text: str | None = Field(default=None, description="Texto transcrito (solo en stop)")


class StatusResponse(BaseModel):
    """Respuesta del endpoint /status."""

    state: str = Field(description="Estado del daemon: 'idle', 'recording', 'processing'")
    recording: bool = Field(description="True si está grabando actualmente")
    model_loaded: bool = Field(description="True si el modelo Whisper está cargado")


class ProcessTextRequest(BaseModel):
    """Request para /llm/process."""

    text: str = Field(min_length=1, max_length=10000, description="Texto a procesar")


class TranslateTextRequest(BaseModel):
    """Request para /llm/translate."""

    text: str = Field(min_length=1, max_length=10000, description="Texto a traducir")
    target_lang: str = Field(default="en", description="Idioma destino (ej. 'en', 'es')")


class LLMResponse(BaseModel):
    """Respuesta de endpoints LLM."""

    text: str = Field(description="Texto procesado/traducido")
    backend: str = Field(description="Backend usado: 'gemini', 'ollama', 'local'")


class HealthResponse(BaseModel):
    """Respuesta del endpoint /health."""

    status: str = Field(default="ok")
    version: str = Field(default="0.2.0")
