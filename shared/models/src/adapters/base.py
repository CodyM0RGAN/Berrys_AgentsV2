"""
Base adapter interface for service boundary adapters.

This module defines the base adapter interface for converting entities
between different service representations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, Type, TypeVar, cast

from pydantic import BaseModel, ValidationError

from shared.models.src.adapters.exceptions import AdapterValidationError, EntityConversionError

# Type variables for generic adapter types
T_Source = TypeVar('T_Source')
T_Target = TypeVar('T_Target')

logger = logging.getLogger(__name__)


class ServiceBoundaryAdapter(ABC, Generic[T_Source, T_Target]):
    """
    Base adapter interface for transforming entities across service boundaries.
    
    This abstract class defines the interface for adapters that convert entities
    between different service representations. It provides common validation and
    error handling mechanisms.
    
    Type Parameters:
        T_Source: The source entity type
        T_Target: The target entity type
    """
    
    @classmethod
    @abstractmethod
    def transform_to_target(cls, source_entity: T_Source) -> T_Target:
        """
        Transform source entity to target service format.
        
        Args:
            source_entity: The source entity to transform
            
        Returns:
            The transformed entity in the target service format
            
        Raises:
            AdapterValidationError: If validation fails
            EntityConversionError: If conversion fails
        """
        pass
    
    @classmethod
    @abstractmethod
    def transform_from_target(cls, target_entity: T_Target) -> T_Source:
        """
        Transform target entity back to source service format.
        
        Args:
            target_entity: The target entity to transform
            
        Returns:
            The transformed entity in the source service format
            
        Raises:
            AdapterValidationError: If validation fails
            EntityConversionError: If conversion fails
        """
        pass
    
    @classmethod
    def validate_entity(cls, entity: Any, model_class: Type[BaseModel]) -> None:
        """
        Validate entity against a Pydantic model.
        
        Args:
            entity: The entity to validate
            model_class: The Pydantic model class to validate against
            
        Raises:
            AdapterValidationError: If validation fails
        """
        try:
            if isinstance(entity, dict):
                model_class(**entity)
            elif not isinstance(entity, model_class):
                model_class(**entity.dict())
        except ValidationError as e:
            raise AdapterValidationError(
                f"Validation failed: {str(e)}",
                source_data=entity,
                target_model=model_class
            )
        except Exception as e:
            raise AdapterValidationError(
                f"Unexpected error during validation: {str(e)}",
                source_data=entity,
                target_model=model_class
            )
    
    @classmethod
    def handle_metadata_conversion(
        cls, 
        data: Dict[str, Any], 
        source_field: str, 
        target_field: str
    ) -> Dict[str, Any]:
        """
        Handle metadata field conversion between different naming conventions.
        
        Args:
            data: The data dictionary to transform
            source_field: The source metadata field name
            target_field: The target metadata field name
            
        Returns:
            The transformed data dictionary
        """
        result = data.copy()
        
        if source_field in result:
            result[target_field] = result.pop(source_field)
        
        return result
    
    @classmethod
    def log_transformation(
        cls, 
        source_entity: Any, 
        target_entity: Any, 
        direction: str
    ) -> None:
        """
        Log a transformation operation.
        
        Args:
            source_entity: The source entity
            target_entity: The transformed entity
            direction: The transformation direction (e.g., 'web_to_coordinator')
        """
        source_type = type(source_entity).__name__
        target_type = type(target_entity).__name__
        
        logger.debug(
            f"Transformed {source_type} to {target_type} ({direction}): "
            f"ID: {getattr(source_entity, 'id', None)}"
        )
