"""
Validation utilities for the Berrys_AgentsV2 system.

This module provides utilities for validating data in the system.
It includes functions for validating different types of data,
such as strings, numbers, UUIDs, enums, and more.
"""

import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel, ValidationError

from shared.utils.src.exceptions import ValidationError as ServiceValidationError


T = TypeVar('T')


class ValidationException(Exception):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        """
        Initialize ValidationException.
        
        Args:
            message: Error message
            field: Field that failed validation
        """
        self.message = message
        self.field = field
        super().__init__(message)


def validate_type(value: Any, expected_type: Type[T], field_name: str) -> T:
    """
    Validate that a value is of the expected type.
    
    Args:
        value: Value to validate
        expected_type: Expected type
        field_name: Name of the field being validated
        
    Returns:
        The validated value
        
    Raises:
        ServiceValidationError: If the value is not of the expected type
    """
    if value is None:
        return value
    
    if not isinstance(value, expected_type):
        raise ServiceValidationError(
            message=f"{field_name} must be of type {expected_type.__name__}",
            validation_errors={field_name: f"Expected {expected_type.__name__}, got {type(value).__name__}"}
        )
    
    return value


def validate_string(
    value: Any,
    field_name: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    pattern: Optional[str] = None,
) -> str:
    """
    Validate a string value.
    
    Args:
        value: Value to validate
        field_name: Name of the field being validated
        min_length: Minimum length of the string
        max_length: Maximum length of the string
        pattern: Regular expression pattern to match
        
    Returns:
        The validated string
        
    Raises:
        ServiceValidationError: If the value is not a valid string
    """
    if value is None:
        return value
    
    # Validate type
    if not isinstance(value, str):
        raise ServiceValidationError(
            message=f"{field_name} must be a string",
            validation_errors={field_name: f"Expected string, got {type(value).__name__}"}
        )
    
    # Validate length
    if min_length is not None and len(value) < min_length:
        raise ServiceValidationError(
            message=f"{field_name} must be at least {min_length} characters",
            validation_errors={field_name: f"String is too short ({len(value)} < {min_length})"}
        )
    
    if max_length is not None and len(value) > max_length:
        raise ServiceValidationError(
            message=f"{field_name} must be at most {max_length} characters",
            validation_errors={field_name: f"String is too long ({len(value)} > {max_length})"}
        )
    
    # Validate pattern
    if pattern is not None and not re.match(pattern, value):
        raise ServiceValidationError(
            message=f"{field_name} must match pattern {pattern}",
            validation_errors={field_name: f"String does not match pattern {pattern}"}
        )
    
    return value


def validate_number(
    value: Any,
    field_name: str,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    integer_only: bool = False,
) -> Union[int, float]:
    """
    Validate a numeric value.
    
    Args:
        value: Value to validate
        field_name: Name of the field being validated
        min_value: Minimum value
        max_value: Maximum value
        integer_only: Whether to only allow integers
        
    Returns:
        The validated number
        
    Raises:
        ServiceValidationError: If the value is not a valid number
    """
    if value is None:
        return value
    
    # Validate type
    if integer_only:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ServiceValidationError(
                message=f"{field_name} must be an integer",
                validation_errors={field_name: f"Expected integer, got {type(value).__name__}"}
            )
    else:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ServiceValidationError(
                message=f"{field_name} must be a number",
                validation_errors={field_name: f"Expected number, got {type(value).__name__}"}
            )
    
    # Validate range
    if min_value is not None and value < min_value:
        raise ServiceValidationError(
            message=f"{field_name} must be at least {min_value}",
            validation_errors={field_name: f"Value is too small ({value} < {min_value})"}
        )
    
    if max_value is not None and value > max_value:
        raise ServiceValidationError(
            message=f"{field_name} must be at most {max_value}",
            validation_errors={field_name: f"Value is too large ({value} > {max_value})"}
        )
    
    return value


def validate_boolean(value: Any, field_name: str) -> bool:
    """
    Validate a boolean value.
    
    Args:
        value: Value to validate
        field_name: Name of the field being validated
        
    Returns:
        The validated boolean
        
    Raises:
        ServiceValidationError: If the value is not a valid boolean
    """
    if value is None:
        return value
    
    # Validate type
    if not isinstance(value, bool):
        raise ServiceValidationError(
            message=f"{field_name} must be a boolean",
            validation_errors={field_name: f"Expected boolean, got {type(value).__name__}"}
        )
    
    return value


def validate_datetime(value: Any, field_name: str) -> datetime:
    """
    Validate a datetime value.
    
    Args:
        value: Value to validate
        field_name: Name of the field being validated
        
    Returns:
        The validated datetime
        
    Raises:
        ServiceValidationError: If the value is not a valid datetime
    """
    if value is None:
        return value
    
    # If it's already a datetime, return it
    if isinstance(value, datetime):
        return value
    
    # If it's a string, try to parse it
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            raise ServiceValidationError(
                message=f"{field_name} must be a valid ISO 8601 datetime",
                validation_errors={field_name: "Invalid datetime format"}
            )
    
    # Otherwise, it's an invalid type
    raise ServiceValidationError(
        message=f"{field_name} must be a datetime",
        validation_errors={field_name: f"Expected datetime, got {type(value).__name__}"}
    )


def validate_uuid(value: Any, field_name: str) -> str:
    """
    Validate a UUID value.
    
    Args:
        value: Value to validate
        field_name: Name of the field being validated
        
    Returns:
        The validated UUID as a string
        
    Raises:
        ServiceValidationError: If the value is not a valid UUID
    """
    if value is None:
        return value
    
    # If it's a UUID object, convert it to a string
    if isinstance(value, uuid.UUID):
        return str(value)
    
    # If it's a string, validate it
    if isinstance(value, str):
        try:
            uuid.UUID(value)
            return value
        except ValueError:
            raise ServiceValidationError(
                message=f"{field_name} must be a valid UUID",
                validation_errors={field_name: "Invalid UUID format"}
            )
    
    # Otherwise, it's an invalid type
    raise ServiceValidationError(
        message=f"{field_name} must be a UUID",
        validation_errors={field_name: f"Expected UUID, got {type(value).__name__}"}
    )


def validate_enum(value: Any, enum_class: Type[Enum], field_name: str) -> Union[Enum, str]:
    """
    Validate an enum value.
    
    Args:
        value: Value to validate
        enum_class: Enum class to validate against
        field_name: Name of the field being validated
        
    Returns:
        The validated enum value
        
    Raises:
        ServiceValidationError: If the value is not a valid enum value
    """
    if value is None:
        return value
    
    # If it's already an enum value, return it
    if isinstance(value, enum_class):
        return value
    
    # If it's a string, try to convert it to an enum value
    if isinstance(value, str):
        try:
            # Try to get the enum value by name
            return enum_class[value]
        except KeyError:
            # If that fails, try to get the enum value by value
            try:
                return next(e for e in enum_class if e.value == value)
            except StopIteration:
                raise ServiceValidationError(
                    message=f"{field_name} must be a valid {enum_class.__name__} value",
                    validation_errors={
                        field_name: f"Invalid enum value: {value}. "
                                    f"Valid values are: {[e.name for e in enum_class]}"
                    }
                )
    
    # Otherwise, it's an invalid type
    raise ServiceValidationError(
        message=f"{field_name} must be a {enum_class.__name__} value",
        validation_errors={field_name: f"Expected {enum_class.__name__}, got {type(value).__name__}"}
    )


def validate_list(
    value: Any,
    field_name: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    item_validator: Optional[Callable[[Any, int], Any]] = None,
) -> List[Any]:
    """
    Validate a list value.
    
    Args:
        value: Value to validate
        field_name: Name of the field being validated
        min_length: Minimum length of the list
        max_length: Maximum length of the list
        item_validator: Function to validate each item in the list
        
    Returns:
        The validated list
        
    Raises:
        ServiceValidationError: If the value is not a valid list
    """
    if value is None:
        return value
    
    # Validate type
    if not isinstance(value, list):
        raise ServiceValidationError(
            message=f"{field_name} must be a list",
            validation_errors={field_name: f"Expected list, got {type(value).__name__}"}
        )
    
    # Validate length
    if min_length is not None and len(value) < min_length:
        raise ServiceValidationError(
            message=f"{field_name} must have at least {min_length} items",
            validation_errors={field_name: f"List is too short ({len(value)} < {min_length})"}
        )
    
    if max_length is not None and len(value) > max_length:
        raise ServiceValidationError(
            message=f"{field_name} must have at most {max_length} items",
            validation_errors={field_name: f"List is too long ({len(value)} > {max_length})"}
        )
    
    # Validate items
    if item_validator is not None:
        validation_errors = {}
        
        for i, item in enumerate(value):
            try:
                value[i] = item_validator(item, i)
            except ServiceValidationError as e:
                for field, error in e.validation_errors.items():
                    validation_errors[f"{field_name}[{i}].{field}"] = error
            except Exception as e:
                validation_errors[f"{field_name}[{i}]"] = str(e)
        
        if validation_errors:
            raise ServiceValidationError(
                message=f"{field_name} contains invalid items",
                validation_errors=validation_errors
            )
    
    return value


def validate_dict(
    value: Any,
    field_name: str,
    required_keys: Optional[List[str]] = None,
    key_validator: Optional[Callable[[str], str]] = None,
    value_validator: Optional[Callable[[Any, str], Any]] = None,
) -> Dict[str, Any]:
    """
    Validate a dictionary value.
    
    Args:
        value: Value to validate
        field_name: Name of the field being validated
        required_keys: List of keys that must be present
        key_validator: Function to validate each key
        value_validator: Function to validate each value
        
    Returns:
        The validated dictionary
        
    Raises:
        ServiceValidationError: If the value is not a valid dictionary
    """
    if value is None:
        return value
    
    # Validate type
    if not isinstance(value, dict):
        raise ServiceValidationError(
            message=f"{field_name} must be a dictionary",
            validation_errors={field_name: f"Expected dictionary, got {type(value).__name__}"}
        )
    
    # Validate required keys
    if required_keys is not None:
        missing_keys = [key for key in required_keys if key not in value]
        if missing_keys:
            raise ServiceValidationError(
                message=f"{field_name} is missing required keys: {', '.join(missing_keys)}",
                validation_errors={field_name: f"Missing required keys: {', '.join(missing_keys)}"}
            )
    
    # Validate keys and values
    validation_errors = {}
    
    for key, val in list(value.items()):
        # Validate key
        if key_validator is not None:
            try:
                new_key = key_validator(key)
                if new_key != key:
                    value[new_key] = value.pop(key)
                    key = new_key
            except ServiceValidationError as e:
                for field, error in e.validation_errors.items():
                    validation_errors[f"{field_name}.{field}"] = error
            except Exception as e:
                validation_errors[f"{field_name}.{key}"] = str(e)
        
        # Validate value
        if value_validator is not None:
            try:
                value[key] = value_validator(val, key)
            except ServiceValidationError as e:
                for field, error in e.validation_errors.items():
                    validation_errors[f"{field_name}.{key}.{field}"] = error
            except Exception as e:
                validation_errors[f"{field_name}.{key}"] = str(e)
    
    if validation_errors:
        raise ServiceValidationError(
            message=f"{field_name} contains invalid keys or values",
            validation_errors=validation_errors
        )
    
    return value


def validate_model(value: Any, model_class: Type[BaseModel], field_name: str) -> Union[BaseModel, Dict[str, Any]]:
    """
    Validate a value against a Pydantic model.
    
    Args:
        value: Value to validate
        model_class: Pydantic model class to validate against
        field_name: Name of the field being validated
        
    Returns:
        The validated model or dictionary
        
    Raises:
        ServiceValidationError: If the value is not valid according to the model
    """
    if value is None:
        return value
    
    # If it's already a model instance, return it
    if isinstance(value, model_class):
        return value
    
    # If it's a dictionary, try to validate it
    if isinstance(value, dict):
        try:
            return model_class(**value)
        except ValidationError as e:
            validation_errors = {}
            for error in e.errors():
                field_path = '.'.join(str(loc) for loc in error['loc'])
                validation_errors[f"{field_name}.{field_path}"] = error['msg']
            
            raise ServiceValidationError(
                message=f"{field_name} is not a valid {model_class.__name__}",
                validation_errors=validation_errors
            )
    
    # Otherwise, it's an invalid type
    raise ServiceValidationError(
        message=f"{field_name} must be a {model_class.__name__}",
        validation_errors={field_name: f"Expected {model_class.__name__}, got {type(value).__name__}"}
    )
