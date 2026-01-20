"""
Servicios de negocio para Voice2Machine.

Este módulo contiene la lógica de negocio simplificada que reemplaza
el patrón CQRS + Command Handlers por llamadas directas a servicios.
"""

from v2m.services.orchestrator import Orchestrator

__all__ = ["Orchestrator"]
