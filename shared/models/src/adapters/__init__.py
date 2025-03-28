"""
Service boundary adapters for entity representation alignment.

This module provides adapters for converting entities between different service representations.
It handles field name differences, type conversions, and metadata transformations.
"""

from shared.models.src.adapters.base import ServiceBoundaryAdapter
from shared.models.src.adapters.exceptions import AdapterValidationError, EntityConversionError
from shared.models.src.adapters.types import (
    Entity, EntityConverter, EntityDict, PydanticModel, 
    SQLAlchemyModel, TransformFunction
)

# Service boundary adapters
from shared.models.src.adapters.web_to_coordinator import WebToCoordinatorAdapter
from shared.models.src.adapters.coordinator_to_agent import CoordinatorToAgentAdapter
from shared.models.src.adapters.agent_to_model import AgentToModelAdapter

__all__ = [
    # Base classes and types
    'ServiceBoundaryAdapter',
    'AdapterValidationError',
    'EntityConversionError',
    'Entity',
    'EntityConverter',
    'EntityDict',
    'PydanticModel',
    'SQLAlchemyModel',
    'TransformFunction',
    
    # Service boundary adapters
    'WebToCoordinatorAdapter',
    'CoordinatorToAgentAdapter',
    'AgentToModelAdapter',
]
