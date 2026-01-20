
"""
Puertos del Dominio (Modelos de Datos).

Este módulo define modelos Pydantic utilizados para estructurar las salidas
de los proveedores de LLM que soportan restricciones de esquema JSON (ej. Ollama).
Asegura que la interacción con el dominio sea tipada y predecible.
"""

from pydantic import BaseModel, Field


class CorrectionResult(BaseModel):
    """
    Modelo de salida estructurada para refinamiento de texto.

    Este modelo fuerza a los LLMs a responder en un formato JSON predecible,
    facilitando el parsing y reduciendo alucinaciones de formato.

    Atributos:
        corrected_text: Versión refinada y corregida del texto.
        explanation: Explicación opcional de los cambios (útil para depuración).
    """

    corrected_text: str = Field(description="Texto corregido con gramática y coherencia mejoradas")
    explanation: str | None = Field(default=None, description="Cambios realizados al texto original")
