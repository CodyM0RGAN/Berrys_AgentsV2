"""
Type definitions for service boundary adapters.

This module defines type aliases and utility types for working with
service boundary adapters.
"""

from typing import Any, Callable, Dict, Protocol, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy.ext.declarative import DeclarativeMeta

# Type variables for entity types
T = TypeVar('T')
T_Source = TypeVar('T_Source')
T_Target = TypeVar('T_Target')

# Type aliases for common types
SQLAlchemyModel = DeclarativeMeta
PydanticModel = Type[BaseModel]
EntityDict = Dict[str, Any]

# Type for entity that can be a SQLAlchemy model, Pydantic model, or dictionary
Entity = Union[SQLAlchemyModel, BaseModel, EntityDict]

# Type for transformation function
TransformFunction = Callable[[Entity], Entity]


class EntityConverter(Protocol[T_Source, T_Target]):
    """Protocol for entity converters."""
    
    def __call__(self, source: T_Source) -> T_Target:
        """Convert source entity to target entity."""
        ...
