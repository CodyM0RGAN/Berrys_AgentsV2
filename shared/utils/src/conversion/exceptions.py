"""
Custom exceptions for model conversion.

This module defines exceptions that can be raised during model conversion
between different representations.
"""

from typing import Any, Dict, Optional, Type


class ConversionError(Exception):
    """
    Base exception for conversion errors.
    
    This exception is the base class for all conversion-related exceptions.
    """
    
    def __init__(self, message: str, source_data: Optional[Any] = None):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            source_data: The source data that caused the error
        """
        self.message = message
        self.source_data = source_data
        super().__init__(message)


class ValidationError(ConversionError):
    """
    Exception raised when data validation fails during conversion.
    
    This exception is raised when data fails validation against
    the target model schema.
    """
    
    def __init__(
        self, 
        message: str, 
        source_data: Optional[Any] = None, 
        target_model: Optional[Type] = None
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            source_data: The source data that failed validation
            target_model: The target model class that validation was attempted against
        """
        self.target_model = target_model
        super().__init__(message, source_data)


class TypeConversionError(ConversionError):
    """
    Exception raised when type conversion fails.
    
    This exception is raised when a type conversion error occurs during
    the conversion process, such as trying to convert a string to a date.
    """
    
    def __init__(
        self, 
        message: str, 
        source_field: str, 
        target_field: str, 
        source_value: Any, 
        source_data: Optional[Any] = None
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            source_field: The name of the source field
            target_field: The name of the target field
            source_value: The value that failed conversion
            source_data: The source data that contained the field
        """
        self.source_field = source_field
        self.target_field = target_field
        self.source_value = source_value
        super().__init__(message, source_data)


class MissingFieldError(ConversionError):
    """
    Exception raised when a required field is missing.
    
    This exception is raised when a required field is missing from
    the source data during conversion.
    """
    
    def __init__(self, field_name: str, source_data: Optional[Any] = None):
        """
        Initialize the exception.
        
        Args:
            field_name: The name of the missing field
            source_data: The source data that was missing the field
        """
        message = f"Required field '{field_name}' is missing"
        self.field_name = field_name
        super().__init__(message, source_data)


class RegistrationError(ConversionError):
    """
    Exception raised when model registration fails.
    
    This exception is raised when there is an error registering
    a model mapping in the model registry.
    """
    
    def __init__(
        self, 
        message: str, 
        source_model: Optional[Type] = None, 
        target_model: Optional[Type] = None
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            source_model: The source model class
            target_model: The target model class
        """
        self.source_model = source_model
        self.target_model = target_model
        super().__init__(message)
