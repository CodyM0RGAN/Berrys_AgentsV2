"""
Bridge module for model registry functionality.

This module provides backward compatibility for the model registry functionality
that was moved from shared.models.src.base to shared.utils.src.conversion.base.interfaces.
"""

from shared.utils.src.conversion.base.interfaces import ModelRegistry
from shared.utils.src.conversion.base.interfaces import model_registry

def register_models(sqlalchemy_model, pydantic_model, model_type):
    """
    Register a mapping between SQLAlchemy and Pydantic models.
    
    Args:
        sqlalchemy_model: The SQLAlchemy model class
        pydantic_model: The Pydantic model class
        model_type: The type of model (e.g., 'default', 'create', 'update')
    """
    model_registry.register_entity_converter(sqlalchemy_model.__tablename__, pydantic_model)
