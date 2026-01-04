# This file is part of voice2machine.
#
# voice2machine is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# voice2machine is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with voice2machine.  If not, see <https://www.gnu.org/licenses/>.

"""
Domain ports (interfaces) and models for structured LLM outputs.

This module defines Pydantic models used for structured outputs with
LLM providers that support JSON schema constraints (e.g., Ollama).
"""

from pydantic import BaseModel, Field


class CorrectionResult(BaseModel):
    """Structured output for text refinement.

    This model forces LLM responses into a predictable JSON format
    when using providers that support format constraints via JSON schema.

    Attributes:
        corrected_text: The refined/corrected version of the input text.
        explanation: Optional description of changes made (useful for debugging).
    """

    corrected_text: str = Field(description="Texto corregido con gramática y coherencia mejoradas")
    explanation: str | None = Field(default=None, description="Cambios realizados al texto original")
