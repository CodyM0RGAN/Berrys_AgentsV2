"""
Cross-service validation utilities for the Berrys_AgentsV2 system.

This module provides utilities for validating data that crosses service boundaries.
It includes decorators for validating requests and responses, as well as common
validators for entity IDs.
"""

import functools
import inspect
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, get_type_hints

import logging
from pydantic import BaseModel, ValidationError

from shared.utils.src.exceptions import ValidationError as ServiceValidationError
from shared.utils.src.validation import (
    validate_boolean,
    validate_datetime,
    validate_dict,
    validate_enum,
    validate_list,
    validate_model,
    validate_number,
    validate_string,
    validate_type,
    validate_uuid,
)


logger = logging.getLogger(__name__)


class CrossServiceValidationError(Exception):
    """Exception raised for cross-service validation errors."""
    
    def __init__(self, message: str, validation_errors: Dict[str, str]):
        """
        Initialize CrossServiceValidationError.
        
        Args:
            message: Error message
            validation_errors: Dictionary of field-specific validation errors
        """
        self.message = message
        self.validation_errors = validation_errors
        super().__init__(message)


def validate_project_id(project_id: Any) -> str:
    """
    Validate a project ID.
    
    Args:
        project_id: Project ID to validate
        
    Returns:
        The validated project ID
        
    Raises:
        ServiceValidationError: If the project ID is not valid
    """
    return validate_uuid(project_id, "project_id")


def validate_agent_id(agent_id: Any) -> str:
    """
    Validate an agent ID.
    
    Args:
        agent_id: Agent ID to validate
        
    Returns:
        The validated agent ID
        
    Raises:
        ServiceValidationError: If the agent ID is not valid
    """
    return validate_uuid(agent_id, "agent_id")


def validate_task_id(task_id: Any) -> str:
    """
    Validate a task ID.
    
    Args:
        task_id: Task ID to validate
        
    Returns:
        The validated task ID
        
    Raises:
        ServiceValidationError: If the task ID is not valid
    """
    return validate_uuid(task_id, "task_id")


def validate_model_id(model_id: Any) -> str:
    """
    Validate a model ID.
    
    Args:
        model_id: Model ID to validate
        
    Returns:
        The validated model ID
        
    Raises:
        ServiceValidationError: If the model ID is not valid
    """
    return validate_uuid(model_id, "model_id")


def validate_tool_id(tool_id: Any) -> str:
    """
    Validate a tool ID.
    
    Args:
        tool_id: Tool ID to validate
        
    Returns:
        The validated tool ID
        
    Raises:
        ServiceValidationError: If the tool ID is not valid
    """
    return validate_uuid(tool_id, "tool_id")


def validate_user_id(user_id: Any) -> str:
    """
    Validate a user ID.
    
    Args:
        user_id: User ID to validate
        
    Returns:
        The validated user ID
        
    Raises:
        ServiceValidationError: If the user ID is not valid
    """
    return validate_uuid(user_id, "user_id")


def validate_plan_id(plan_id: Any) -> str:
    """
    Validate a plan ID.
    
    Args:
        plan_id: Plan ID to validate
        
    Returns:
        The validated plan ID
        
    Raises:
        ServiceValidationError: If the plan ID is not valid
    """
    return validate_uuid(plan_id, "plan_id")


def create_field_validator(
    field_type: Type,
    field_name: str,
    **kwargs
) -> Callable[[Any], Any]:
    """
    Create a validator function for a specific field type.
    
    Args:
        field_type: Type of the field
        field_name: Name of the field
        **kwargs: Additional arguments for the validator
        
    Returns:
        A validator function for the field
        
    Raises:
        ValueError: If the field type is not supported
    """
    # Handle None type
    if field_type is type(None):
        return lambda value: None if value is None else None
    
    # Handle Union types
    if hasattr(field_type, "__origin__") and field_type.__origin__ is Union:
        # Extract the non-None types from the Union
        types = [t for t in field_type.__args__ if t is not type(None)]
        if len(types) == 1:
            # If there's only one non-None type, use its validator
            return create_field_validator(types[0], field_name, **kwargs)
        else:
            # If there are multiple types, try each one
            def union_validator(value):
                if value is None:
                    return None
                
                for t in types:
                    try:
                        return create_field_validator(t, field_name, **kwargs)(value)
                    except ServiceValidationError:
                        continue
                
                raise ServiceValidationError(
                    message=f"{field_name} must be one of the following types: {', '.join(str(t) for t in types)}",
                    validation_errors={field_name: f"Expected one of {', '.join(str(t) for t in types)}, got {type(value).__name__}"}
                )
            
            return union_validator
    
    # Handle List types
    if hasattr(field_type, "__origin__") and field_type.__origin__ is list:
        item_type = field_type.__args__[0]
        item_validator = create_field_validator(item_type, f"{field_name}[i]", **kwargs)
        
        def list_validator(value):
            if value is None:
                return None
            
            # Validate the list itself
            value = validate_list(value, field_name)
            
            # Validate each item in the list
            for i, item in enumerate(value):
                try:
                    value[i] = item_validator(item)
                except ServiceValidationError as e:
                    raise ServiceValidationError(
                        message=f"Item at index {i} in {field_name} is invalid: {e.message}",
                        validation_errors={f"{field_name}[{i}]": e.validation_errors.get(f"{field_name}[i]", str(e))}
                    )
            
            return value
        
        return list_validator
    
    # Handle Dict types
    if hasattr(field_type, "__origin__") and field_type.__origin__ is dict:
        key_type, value_type = field_type.__args__
        key_validator = create_field_validator(key_type, f"{field_name}.key", **kwargs)
        value_validator = create_field_validator(value_type, f"{field_name}.value", **kwargs)
        
        def dict_validator(value):
            if value is None:
                return None
            
            # Validate the dict itself
            value = validate_dict(value, field_name)
            
            # Validate each key and value in the dict
            for k, v in list(value.items()):
                try:
                    new_k = key_validator(k)
                    if new_k != k:
                        value[new_k] = value.pop(k)
                        k = new_k
                except ServiceValidationError as e:
                    raise ServiceValidationError(
                        message=f"Key {k} in {field_name} is invalid: {e.message}",
                        validation_errors={f"{field_name}.{k}": e.validation_errors.get(f"{field_name}.key", str(e))}
                    )
                
                try:
                    value[k] = value_validator(v)
                except ServiceValidationError as e:
                    raise ServiceValidationError(
                        message=f"Value for key {k} in {field_name} is invalid: {e.message}",
                        validation_errors={f"{field_name}.{k}": e.validation_errors.get(f"{field_name}.value", str(e))}
                    )
            
            return value
        
        return dict_validator
    
    # Handle string type
    if field_type is str:
        min_length = kwargs.get("min_length")
        max_length = kwargs.get("max_length")
        pattern = kwargs.get("pattern")
        
        return lambda value: validate_string(value, field_name, min_length=min_length, max_length=max_length, pattern=pattern)
    
    # Handle numeric types
    if field_type is int:
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")
        
        return lambda value: validate_number(value, field_name, min_value=min_value, max_value=max_value, integer_only=True)
    
    if field_type is float:
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")
        
        return lambda value: validate_number(value, field_name, min_value=min_value, max_value=max_value)
    
    # Handle boolean type
    if field_type is bool:
        return lambda value: validate_boolean(value, field_name)
    
    # Handle datetime type
    if field_type is datetime:
        return lambda value: validate_datetime(value, field_name)
    
    # Handle UUID type
    if field_type is uuid.UUID:
        return lambda value: validate_uuid(value, field_name)
    
    # Handle Enum types
    if isinstance(field_type, type) and issubclass(field_type, Enum):
        return lambda value: validate_enum(value, field_type, field_name)
    
    # Handle Pydantic models
    if isinstance(field_type, type) and issubclass(field_type, BaseModel):
        return lambda value: validate_model(value, field_type, field_name)
    
    # Default validator for other types
    return lambda value: validate_type(value, field_type, field_name)


def create_validators_from_model(model_class: Type[BaseModel]) -> Dict[str, Callable[[Any], Any]]:
    """
    Create field validators from a Pydantic model.
    
    Args:
        model_class: Pydantic model class
        
    Returns:
        Dictionary of field validators
    """
    validators = {}
    
    # Get field definitions from the model
    for field_name, field in model_class.__annotations__.items():
        field_info = model_class.model_fields.get(field_name)
        if field_info is None:
            continue
        
        # Extract validation parameters
        kwargs = {}
        
        # String validation
        if hasattr(field_info, "min_length"):
            kwargs["min_length"] = field_info.min_length
        if hasattr(field_info, "max_length"):
            kwargs["max_length"] = field_info.max_length
        if hasattr(field_info, "pattern"):
            kwargs["pattern"] = field_info.pattern
        
        # Numeric validation
        if hasattr(field_info, "ge"):
            kwargs["min_value"] = field_info.ge
        if hasattr(field_info, "gt"):
            kwargs["min_value"] = field_info.gt
            if kwargs["min_value"] is not None:
                kwargs["min_value"] += 1
        if hasattr(field_info, "le"):
            kwargs["max_value"] = field_info.le
        if hasattr(field_info, "lt"):
            kwargs["max_value"] = field_info.lt
            if kwargs["max_value"] is not None:
                kwargs["max_value"] -= 1
        
        # Create validator for the field
        validators[field_name] = create_field_validator(field, field_name, **kwargs)
    
    return validators


def validate_cross_service_request(
    target_service: str,
    request_model: Optional[Type[BaseModel]] = None,
    field_validators: Optional[Dict[str, Callable[[Any], Any]]] = None,
):
    """
    Decorator for validating cross-service requests.
    
    Args:
        target_service: Name of the target service
        request_model: Pydantic model for validating the request
        field_validators: Dictionary of field validators
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get the request data
            request_data = None
            
            # Check if the first argument is self
            if len(args) > 0 and not isinstance(args[0], dict):
                # If the function has a positional parameter for request data
                if len(args) > 1:
                    request_data = args[1]
                # If the function has keyword parameters
                elif kwargs:
                    # Find the parameter that's a dict
                    for param_name, param_value in kwargs.items():
                        if isinstance(param_value, dict):
                            request_data = param_value
                            break
            else:
                # If the first argument is the request data
                if len(args) > 0:
                    request_data = args[0]
                # If the function has keyword parameters
                elif kwargs:
                    # Find the parameter that's a dict
                    for param_name, param_value in kwargs.items():
                        if isinstance(param_value, dict):
                            request_data = param_value
                            break
            
            # If we couldn't find the request data, try to get it from the function signature
            if request_data is None:
                # Get the function signature
                sig = inspect.signature(func)
                
                # Find the parameter that's a dict
                for param_name, param in sig.parameters.items():
                    if param_name in kwargs and isinstance(kwargs[param_name], dict):
                        request_data = kwargs[param_name]
                        break
            
            # If we still couldn't find the request data, log a warning and continue
            if request_data is None:
                logger.warning(f"Could not find request data for {func.__name__}")
                return await func(*args, **kwargs)
            
            # Validate the request data
            validation_errors = {}
            
            # If a request model is provided, validate against it
            if request_model is not None:
                try:
                    # Validate the request data against the model
                    model_instance = request_model(**request_data)
                    
                    # Convert the model instance back to a dict
                    validated_data = model_instance.model_dump()
                    
                    # Update the request data with the validated data
                    if isinstance(request_data, dict):
                        request_data.clear()
                        request_data.update(validated_data)
                except ValidationError as e:
                    # Convert Pydantic validation errors to our format
                    for error in e.errors():
                        field_path = '.'.join(str(loc) for loc in error['loc'])
                        validation_errors[field_path] = error['msg']
            
            # If field validators are provided, validate each field
            if field_validators is not None:
                for field_name, validator in field_validators.items():
                    # Check if the field exists in the request data
                    if field_name in request_data:
                        try:
                            # Validate the field
                            request_data[field_name] = validator(request_data[field_name])
                        except ServiceValidationError as e:
                            # Add the validation error
                            for field, error in e.validation_errors.items():
                                validation_errors[field] = error
                        except Exception as e:
                            # Add the validation error
                            validation_errors[field_name] = str(e)
            
            # If there are validation errors, raise an exception
            if validation_errors:
                raise ServiceValidationError(
                    message=f"Invalid request to {target_service}",
                    validation_errors=validation_errors
                )
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def validate_service_response(
    source_service: str,
    response_model: Optional[Type[BaseModel]] = None,
    field_validators: Optional[Dict[str, Callable[[Any], Any]]] = None,
):
    """
    Decorator for validating service responses.
    
    Args:
        source_service: Name of the source service
        response_model: Pydantic model for validating the response
        field_validators: Dictionary of field validators
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Call the original function
            response = await func(*args, **kwargs)
            
            # Validate the response
            validation_errors = {}
            
            # If a response model is provided, validate against it
            if response_model is not None:
                try:
                    # Validate the response against the model
                    return response_model(**response)
                except ValidationError as e:
                    # Convert Pydantic validation errors to our format
                    for error in e.errors():
                        field_path = '.'.join(str(loc) for loc in error['loc'])
                        validation_errors[field_path] = error['msg']
            
            # If field validators are provided, validate each field
            if field_validators is not None:
                for field_name, validator in field_validators.items():
                    # Check if the field exists in the response
                    if field_name in response:
                        try:
                            # Validate the field
                            response[field_name] = validator(response[field_name])
                        except ServiceValidationError as e:
                            # Add the validation error
                            for field, error in e.validation_errors.items():
                                validation_errors[field] = error
                        except Exception as e:
                            # Add the validation error
                            validation_errors[field_name] = str(e)
            
            # If there are validation errors, raise an exception
            if validation_errors:
                raise ServiceValidationError(
                    message=f"Invalid response from {source_service}",
                    validation_errors=validation_errors
                )
            
            # Return the response
            return response
        
        return wrapper
    
    return decorator
