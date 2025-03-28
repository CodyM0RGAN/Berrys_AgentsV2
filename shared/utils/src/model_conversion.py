"""
Model conversion utilities for the Berrys_AgentsV2 project.

This module provides utilities for converting between different model types,
particularly between SQLAlchemy ORM models and Pydantic models.
"""

import inspect
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, get_type_hints

from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase

T = TypeVar('T')
P = TypeVar('P', bound=BaseModel)
S = TypeVar('S', bound=DeclarativeBase)


def to_dict(obj: Any, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Convert an object to a dictionary.

    Args:
        obj: The object to convert.
        exclude: A list of attribute names to exclude from the result.

    Returns:
        A dictionary representation of the object.
    """
    if exclude is None:
        exclude = []
    
    if hasattr(obj, '__table__'):
        # SQLAlchemy model
        result = {}
        for column in obj.__table__.columns:
            if column.name not in exclude:
                result[column.name] = getattr(obj, column.name)
        return result
    
    if isinstance(obj, BaseModel):
        # Pydantic model
        return obj.model_dump(exclude=set(exclude))
    
    # Generic object
    result = {}
    for key, value in obj.__dict__.items():
        if not key.startswith('_') and key not in exclude:
            result[key] = value
    return result


def normalize_enum_value(value: Any, enum_class: Type[Enum]) -> str:
    """
    Normalize an enum value to its string representation.

    Args:
        value: The value to normalize.
        enum_class: The enum class.

    Returns:
        The normalized enum value.
    """
    if value is None:
        return None
    
    if isinstance(value, enum_class):
        return value.value
    
    if isinstance(value, str):
        # Handle case-insensitive matching
        for enum_item in enum_class:
            if value.upper() == enum_item.value.upper():
                return enum_item.value
    
    # Try to convert to enum and get value
    try:
        return enum_class(value).value
    except (ValueError, TypeError):
        raise ValueError(f"Invalid value {value} for enum {enum_class.__name__}")


def sqlalchemy_to_pydantic(
    sqlalchemy_model: S,
    pydantic_model_class: Type[P],
    exclude: Optional[List[str]] = None,
    include_relationships: bool = False
) -> P:
    """
    Convert a SQLAlchemy model instance to a Pydantic model instance.

    Args:
        sqlalchemy_model: The SQLAlchemy model instance to convert.
        pydantic_model_class: The Pydantic model class to convert to.
        exclude: A list of attribute names to exclude from the result.
        include_relationships: Whether to include relationships in the result.

    Returns:
        A Pydantic model instance.
    """
    if exclude is None:
        exclude = []
    
    # Get the data from the SQLAlchemy model
    data = {}
    
    # Add columns
    for column in sqlalchemy_model.__table__.columns:
        if column.name not in exclude:
            data[column.name] = getattr(sqlalchemy_model, column.name)
    
    # Add relationships if requested
    if include_relationships:
        for relationship_name, relationship in inspect.getmembers(
            sqlalchemy_model.__class__,
            lambda attr: hasattr(attr, 'property') and hasattr(attr.property, 'key')
        ):
            if relationship_name not in exclude:
                related_obj = getattr(sqlalchemy_model, relationship_name)
                if related_obj is not None:
                    if hasattr(related_obj, '__iter__'):
                        # Many relationship
                        data[relationship_name] = [to_dict(item) for item in related_obj]
                    else:
                        # One relationship
                        data[relationship_name] = to_dict(related_obj)
    
    # Convert enum values
    pydantic_fields = get_type_hints(pydantic_model_class)
    for field_name, field_type in pydantic_fields.items():
        if field_name in data and data[field_name] is not None:
            # Check if field type is an enum
            origin = getattr(field_type, '__origin__', None)
            if origin is Union:
                # Handle Optional[Enum]
                args = getattr(field_type, '__args__', [])
                for arg in args:
                    if inspect.isclass(arg) and issubclass(arg, Enum):
                        data[field_name] = normalize_enum_value(data[field_name], arg)
                        break
            elif inspect.isclass(field_type) and issubclass(field_type, Enum):
                # Handle direct Enum type
                data[field_name] = normalize_enum_value(data[field_name], field_type)
    
    # Create the Pydantic model
    return pydantic_model_class(**data)


def pydantic_to_sqlalchemy(
    pydantic_model: P,
    sqlalchemy_model_class: Type[S],
    exclude: Optional[List[str]] = None
) -> S:
    """
    Convert a Pydantic model instance to a SQLAlchemy model instance.

    Args:
        pydantic_model: The Pydantic model instance to convert.
        sqlalchemy_model_class: The SQLAlchemy model class to convert to.
        exclude: A list of attribute names to exclude from the result.

    Returns:
        A SQLAlchemy model instance.
    """
    if exclude is None:
        exclude = []
    
    # Get the data from the Pydantic model
    data = pydantic_model.model_dump(exclude=set(exclude))
    
    # Convert enum instances to their values
    for key, value in list(data.items()):
        if isinstance(value, Enum):
            data[key] = value.value
    
    # Create the SQLAlchemy model
    return sqlalchemy_model_class(**data)


def update_sqlalchemy_from_pydantic(
    sqlalchemy_model: S,
    pydantic_model: P,
    exclude: Optional[List[str]] = None
) -> S:
    """
    Update a SQLAlchemy model instance from a Pydantic model instance.

    Args:
        sqlalchemy_model: The SQLAlchemy model instance to update.
        pydantic_model: The Pydantic model instance to update from.
        exclude: A list of attribute names to exclude from the update.

    Returns:
        The updated SQLAlchemy model instance.
    """
    if exclude is None:
        exclude = []
    
    # Get the data from the Pydantic model
    data = pydantic_model.model_dump(exclude=set(exclude))
    
    # Update the SQLAlchemy model
    for key, value in data.items():
        if hasattr(sqlalchemy_model, key) and key not in exclude:
            if isinstance(value, Enum):
                value = value.value
            setattr(sqlalchemy_model, key, value)
    
    return sqlalchemy_model
