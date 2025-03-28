"""
Base interfaces for model conversion.

This module defines the base interfaces for model conversion between
different representations, such as SQLAlchemy ORM models and Pydantic models.
"""

from abc import ABC, abstractmethod
from typing import Dict, Generic, TypeVar, Any, List, Optional, Type, Union

from pydantic import BaseModel

# Type variables for generic type hints
T = TypeVar('T')  # Source type
U = TypeVar('U')  # Target type

class ModelConverter(Generic[T, U], ABC):
    """
    Base interface for model conversion between different representations.
    
    This abstract class defines the interface for converters that convert
    between different model representations, such as SQLAlchemy ORM models
    and Pydantic models.
    
    Type Parameters:
        T: The source model type
        U: The target model type
    """
    
    @abstractmethod
    def to_target(self, source: T) -> U:
        """
        Convert from source model to target model.
        
        Args:
            source: The source model instance to convert
            
        Returns:
            The converted target model instance
        """
        pass
    
    @abstractmethod
    def from_target(self, target: U) -> T:
        """
        Convert from target model to source model.
        
        Args:
            target: The target model instance to convert
            
        Returns:
            The converted source model instance
        """
        pass
    
    @abstractmethod
    def to_dict(self, source: T) -> Dict[str, Any]:
        """
        Convert source model to dictionary representation.
        
        Args:
            source: The source model instance to convert
            
        Returns:
            Dictionary representation of the source model
        """
        pass
    
    @abstractmethod
    def from_dict(self, data: Dict[str, Any]) -> T:
        """
        Create source model from dictionary representation.
        
        Args:
            data: Dictionary representation of the source model
            
        Returns:
            The created source model instance
        """
        pass
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """
        Validate that the data can be converted to the source model.
        
        Args:
            data: The data to validate
            
        Returns:
            True if the data can be converted, False otherwise
        """
        pass
    
    def batch_to_target(self, sources: List[T]) -> List[U]:
        """
        Convert a list of source models to target models.
        
        Args:
            sources: The source model instances to convert
            
        Returns:
            List of converted target model instances
        """
        return [self.to_target(source) for source in sources]
    
    def batch_from_target(self, targets: List[U]) -> List[T]:
        """
        Convert a list of target models to source models.
        
        Args:
            targets: The target model instances to convert
            
        Returns:
            List of converted source model instances
        """
        return [self.from_target(target) for target in targets]


class EntityConverter(Generic[T], ABC):
    """
    Interface for converting between ORM models and Pydantic models.
    
    This abstract class defines the interface for converters that convert
    between SQLAlchemy ORM models and Pydantic models for a specific entity.
    
    Type Parameters:
        T: The Pydantic model type
    """
    
    @abstractmethod
    def to_pydantic(self, orm_model: Any) -> T:
        """
        Convert ORM model to Pydantic model.
        
        Args:
            orm_model: The SQLAlchemy ORM model instance to convert
            
        Returns:
            The converted Pydantic model instance
        """
        pass
    
    @abstractmethod
    def to_orm(self, pydantic_model: T) -> Any:
        """
        Convert Pydantic model to ORM model.
        
        Args:
            pydantic_model: The Pydantic model instance to convert
            
        Returns:
            The converted SQLAlchemy ORM model instance
        """
        pass
    
    @abstractmethod
    def to_external(self, orm_model: Any) -> Dict[str, Any]:
        """
        Convert ORM model to external dictionary representation.
        
        Args:
            orm_model: The SQLAlchemy ORM model instance to convert
            
        Returns:
            Dictionary representation of the ORM model
        """
        pass
    
    @abstractmethod
    def from_external(self, data: Dict[str, Any]) -> T:
        """
        Create Pydantic model from external dictionary representation.
        
        Args:
            data: Dictionary representation of the model
            
        Returns:
            The created Pydantic model instance
        """
        pass
    
    def batch_to_pydantic(self, orm_models: List[Any]) -> List[T]:
        """
        Convert a list of ORM models to Pydantic models.
        
        Args:
            orm_models: The SQLAlchemy ORM model instances to convert
            
        Returns:
            List of converted Pydantic model instances
        """
        return [self.to_pydantic(orm_model) for orm_model in orm_models]
    
    def batch_to_orm(self, pydantic_models: List[T]) -> List[Any]:
        """
        Convert a list of Pydantic models to ORM models.
        
        Args:
            pydantic_models: The Pydantic model instances to convert
            
        Returns:
            List of converted SQLAlchemy ORM model instances
        """
        return [self.to_orm(pydantic_model) for pydantic_model in pydantic_models]


class ApiConverter(Generic[T, U], ABC):
    """
    Interface for converting between internal models and API models.
    
    This abstract class defines the interface for converters that convert
    between internal models and API models for a specific entity.
    
    Type Parameters:
        T: The internal model type
        U: The API model type
    """
    
    @abstractmethod
    def to_api(self, internal_model: T) -> U:
        """
        Convert internal model to API model.
        
        Args:
            internal_model: The internal model instance to convert
            
        Returns:
            The converted API model instance
        """
        pass
    
    @abstractmethod
    def from_api(self, api_model: U) -> T:
        """
        Convert API model to internal model.
        
        Args:
            api_model: The API model instance to convert
            
        Returns:
            The converted internal model instance
        """
        pass
    
    def batch_to_api(self, internal_models: List[T]) -> List[U]:
        """
        Convert a list of internal models to API models.
        
        Args:
            internal_models: The internal model instances to convert
            
        Returns:
            List of converted API model instances
        """
        return [self.to_api(internal_model) for internal_model in internal_models]
    
    def batch_from_api(self, api_models: List[U]) -> List[T]:
        """
        Convert a list of API models to internal models.
        
        Args:
            api_models: The API model instances to convert
            
        Returns:
            List of converted internal model instances
        """
        return [self.from_api(api_model) for api_model in api_models]


class ModelRegistry:
    """
    Registry for model converters.
    
    This class provides a registry for model converters, allowing
    converters to be registered and retrieved by model type.
    """
    
    def __init__(self):
        """Initialize the model registry."""
        self._entity_converters: Dict[str, EntityConverter] = {}
        self._api_converters: Dict[str, ApiConverter] = {}
    
    def register_entity_converter(self, entity_name: str, converter: EntityConverter) -> None:
        """
        Register an entity converter.
        
        Args:
            entity_name: The name of the entity
            converter: The entity converter to register
        """
        self._entity_converters[entity_name] = converter
    
    def register_api_converter(self, entity_name: str, converter: ApiConverter) -> None:
        """
        Register an API converter.
        
        Args:
            entity_name: The name of the entity
            converter: The API converter to register
        """
        self._api_converters[entity_name] = converter
    
    def get_entity_converter(self, entity_name: str) -> Optional[EntityConverter]:
        """
        Get an entity converter by entity name.
        
        Args:
            entity_name: The name of the entity
            
        Returns:
            The entity converter, or None if not found
        """
        return self._entity_converters.get(entity_name)
    
    def get_api_converter(self, entity_name: str) -> Optional[ApiConverter]:
        """
        Get an API converter by entity name.
        
        Args:
            entity_name: The name of the entity
            
        Returns:
            The API converter, or None if not found
        """
        return self._api_converters.get(entity_name)


# Global model registry instance
model_registry = ModelRegistry()
