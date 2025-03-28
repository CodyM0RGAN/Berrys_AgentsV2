"""
Custom exceptions for service boundary adapters.

This module defines exceptions that can be raised during entity conversion
between different service representations.
"""

from typing import Any, Dict, Optional, Type


class AdapterValidationError(Exception):
    """
    Exception raised when entity validation fails during conversion.
    
    This exception is raised when an entity fails validation against
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
        self.message = message
        self.source_data = source_data
        self.target_model = target_model
        super().__init__(message)


class EntityConversionError(Exception):
    """
    Exception raised when entity conversion fails.
    
    This exception is raised when an error occurs during the conversion
    process, such as missing required fields or type conversion errors.
    """
    
    def __init__(
        self, 
        message: str, 
        source_entity: Optional[Any] = None, 
        error_details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            source_entity: The source entity that failed conversion
            error_details: Additional details about the error
        """
        self.message = message
        self.source_entity = source_entity
        self.error_details = error_details or {}
        super().__init__(message)
