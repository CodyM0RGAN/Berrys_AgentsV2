"""
Utility functions for model conversion.

This module provides utility functions for model conversion between
different representations, such as SQLAlchemy ORM models and Pydantic models.
"""

import inspect
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, get_type_hints, get_origin, get_args

from pydantic import BaseModel
from sqlalchemy.ext.declarative import DeclarativeMeta

from shared.utils.src.conversion.exceptions import ConversionError, ValidationError, TypeConversionError, MissingFieldError

# Type variables for generic type hints
T = TypeVar('T')  # Pydantic model type
U = TypeVar('U')  # SQLAlchemy model type

logger = logging.getLogger(__name__)


def convert_to_pydantic(
    orm_instance: Union[Any, Dict[str, Any]], 
    pydantic_cls: Type[T]
) -> T:
    """
    Convert an ORM instance or dictionary to a Pydantic model.
    
    Args:
        orm_instance: The ORM instance or dictionary to convert
        pydantic_cls: The Pydantic model class to convert to
        
    Returns:
        An instance of the Pydantic model
        
    Raises:
        ValidationError: If the data fails validation
        TypeConversionError: If a type conversion error occurs
    """
    try:
        # If orm_instance is already a dictionary, use it directly
        if isinstance(orm_instance, dict):
            data = orm_instance
        # If orm_instance has a to_dict method, use it
        elif hasattr(orm_instance, 'to_dict') and callable(getattr(orm_instance, 'to_dict')):
            data = orm_instance.to_dict()
        # Otherwise, extract attributes from the ORM instance
        else:
            data = {}
            # Get all columns from the ORM model
            if hasattr(orm_instance, '__table__'):
                for column in orm_instance.__table__.columns:
                    value = getattr(orm_instance, column.name)
                    
                    # Handle metadata columns
                    if column.name.endswith('_metadata'):
                        # Convert entity_metadata to metadata in Pydantic models
                        base_name = column.name.replace('_metadata', '')
                        if hasattr(orm_instance, '__tablename__') and base_name == orm_instance.__tablename__:
                            data['metadata'] = value
                        else:
                            data[column.name] = value
                    else:
                        data[column.name] = value
            # Fallback for non-SQLAlchemy objects
            else:
                for attr_name in dir(orm_instance):
                    if not attr_name.startswith('_') and not callable(getattr(orm_instance, attr_name)):
                        data[attr_name] = getattr(orm_instance, attr_name)
        
        # Convert enum values to enum instances
        data = convert_enum_values(data, pydantic_cls)
        
        # Create and return the Pydantic model
        return pydantic_cls(**data)
    
    except ValidationError:
        # Re-raise ValidationError
        raise
    except TypeConversionError:
        # Re-raise TypeConversionError
        raise
    except Exception as e:
        # Wrap other exceptions in ConversionError
        raise ConversionError(f"Error converting to Pydantic model: {str(e)}", orm_instance)


def convert_to_orm(
    pydantic_instance: T, 
    orm_cls: Type[U],
    existing_instance: Optional[U] = None
) -> U:
    """
    Convert a Pydantic model to an ORM model.
    
    Args:
        pydantic_instance: The Pydantic model instance to convert
        orm_cls: The ORM model class to convert to
        existing_instance: Optional existing ORM instance to update
        
    Returns:
        An instance of the ORM model
        
    Raises:
        ValidationError: If the data fails validation
        TypeConversionError: If a type conversion error occurs
    """
    try:
        # Convert Pydantic instance to dictionary
        if hasattr(pydantic_instance, 'dict') and callable(getattr(pydantic_instance, 'dict')):
            data = pydantic_instance.dict()
        else:
            data = {k: v for k, v in pydantic_instance.__dict__.items() if not k.startswith('_')}
        
        # Handle metadata field mapping
        if 'metadata' in data:
            tablename = getattr(orm_cls, '__tablename__', None)
            if tablename:
                metadata_col = f"{tablename}_metadata"
                data[metadata_col] = data.pop('metadata')
        
        # Convert enum instances to string values
        for key, value in list(data.items()):
            if isinstance(value, Enum):
                data[key] = value.value
        
        # Create new instance or update existing
        if existing_instance is not None:
            for key, value in data.items():
                if hasattr(existing_instance, key):
                    setattr(existing_instance, key, value)
            
            # Update the updated_at field if it exists
            if hasattr(existing_instance, 'updated_at'):
                setattr(existing_instance, 'updated_at', datetime.utcnow())
            
            return existing_instance
        
        # Create and return the ORM model
        return orm_cls(**data)
    
    except ValidationError:
        # Re-raise ValidationError
        raise
    except TypeConversionError:
        # Re-raise TypeConversionError
        raise
    except Exception as e:
        # Wrap other exceptions in ConversionError
        raise ConversionError(f"Error converting to ORM model: {str(e)}", pydantic_instance)


def convert_enum_values(data: Dict[str, Any], model_cls: Type) -> Dict[str, Any]:
    """
    Convert string values to enum instances based on the model class type hints.
    
    Args:
        data: The data dictionary to convert
        model_cls: The model class with type hints
        
    Returns:
        The converted data dictionary
    """
    result = data.copy()
    
    # Try to get type hints from the model class
    try:
        type_hints = get_type_hints(model_cls)
        
        # Convert string values to enum instances
        for field_name, field_type in type_hints.items():
            if field_name in result and result[field_name] is not None:
                # Check if the field type is an enum class
                if is_enum_type(field_type):
                    enum_cls = get_enum_class(field_type)
                    if enum_cls:
                        try:
                            result[field_name] = convert_to_enum(result[field_name], enum_cls)
                        except ValueError as e:
                            # Log the error but don't raise an exception
                            logger.warning(f"Error converting enum value: {str(e)}")
    
    except (TypeError, NameError):
        # If type hints can't be resolved, return the original data
        pass
    
    return result


def is_enum_type(field_type: Type) -> bool:
    """
    Check if a field type is an enum type.
    
    Args:
        field_type: The field type to check
        
    Returns:
        True if the field type is an enum type, False otherwise
    """
    # Check if the field type is an enum class
    if inspect.isclass(field_type) and issubclass(field_type, Enum):
        return True
    
    # Check if the field type is Optional[Enum]
    origin = get_origin(field_type)
    if origin is Union:
        args = get_args(field_type)
        for arg in args:
            if inspect.isclass(arg) and issubclass(arg, Enum):
                return True
    
    return False


def get_enum_class(field_type: Type) -> Optional[Type[Enum]]:
    """
    Get the enum class from a field type.
    
    Args:
        field_type: The field type to check
        
    Returns:
        The enum class, or None if not found
    """
    # If field_type is an enum class, return it
    if inspect.isclass(field_type) and issubclass(field_type, Enum):
        return field_type
    
    # If field_type is Optional[Enum], extract the enum class
    origin = get_origin(field_type)
    if origin is Union:
        args = get_args(field_type)
        for arg in args:
            if inspect.isclass(arg) and issubclass(arg, Enum):
                return arg
    
    return None


def convert_to_enum(value: Any, enum_class: Type[Enum]) -> Enum:
    """
    Convert a value to an enum instance.
    
    Args:
        value: The value to convert
        enum_class: The enum class to convert to
        
    Returns:
        An instance of the enum class
        
    Raises:
        ValueError: If the value cannot be converted to an enum instance
    """
    # If value is already an enum instance, return it
    if isinstance(value, enum_class):
        return value
    
    # If value is a string, try to match it to an enum value
    if isinstance(value, str):
        # Try to match by value
        for enum_item in enum_class:
            if value == enum_item.value:
                return enum_item
        
        # Try to match by name (case insensitive)
        for enum_item in enum_class:
            if value.upper() == enum_item.name.upper():
                return enum_item
    
    # If value is not a string, try to convert it
    try:
        # Try to get the enum by name
        return enum_class[str(value).upper()]
    except (KeyError, ValueError):
        # If that fails, try to get the enum by value
        for enum_item in enum_class:
            if value == enum_item.value:
                return enum_item
    
    # If all else fails, raise an error
    valid_values = [f"{e.name} ({e.value})" for e in enum_class]
    raise ValueError(
        f"Invalid value '{value}' for enum {enum_class.__name__}. "
        f"Valid values are: {', '.join(valid_values)}"
    )


def batch_convert_to_pydantic(
    orm_instances: List[Union[Any, Dict[str, Any]]], 
    pydantic_cls: Type[T]
) -> List[T]:
    """
    Convert a list of ORM instances or dictionaries to Pydantic models.
    
    Args:
        orm_instances: The ORM instances or dictionaries to convert
        pydantic_cls: The Pydantic model class to convert to
        
    Returns:
        List of converted Pydantic model instances
    """
    return [convert_to_pydantic(instance, pydantic_cls) for instance in orm_instances]


def batch_convert_to_orm(
    pydantic_instances: List[T], 
    orm_cls: Type[U]
) -> List[U]:
    """
    Convert a list of Pydantic models to ORM models.
    
    Args:
        pydantic_instances: The Pydantic model instances to convert
        orm_cls: The ORM model class to convert to
        
    Returns:
        List of converted ORM model instances
    """
    return [convert_to_orm(instance, orm_cls) for instance in pydantic_instances]
