"""
Parameter Validation module.

This module defines tools for validating parameters against schemas,
providing functionality for ensuring that tool inputs match expectations.
"""

import logging
import json
import jsonschema
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ...exceptions import ToolSchemaValidationError

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation."""
    valid: bool
    errors: List[str] = None
    details: Optional[Dict[str, Any]] = None


class ParameterValidator:
    """Validator for tool parameters."""
    
    def __init__(self, schema_validation_enabled: bool = True):
        """
        Initialize the parameter validator.
        
        Args:
            schema_validation_enabled: Whether schema validation is enabled
        """
        self.schema_validation_enabled = schema_validation_enabled
    
    def validate(
        self, 
        schema: Dict[str, Any], 
        parameters: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate parameters against a schema.
        
        Args:
            schema: JSON Schema
            parameters: Parameters to validate
            
        Returns:
            ValidationResult: Validation result
        """
        if not self.schema_validation_enabled:
            logger.warning("Schema validation is disabled")
            return ValidationResult(valid=True)
        
        if not schema:
            logger.warning("No schema provided for validation")
            return ValidationResult(valid=True)
        
        try:
            # Create validator
            validator = jsonschema.Draft7Validator(schema)
            
            # Validate parameters
            errors = list(validator.iter_errors(parameters))
            
            if errors:
                # Format error messages
                error_messages = []
                for error in errors:
                    if error.path:
                        # Format path as dot notation
                        path = ".".join(str(part) for part in error.path)
                        error_messages.append(f"{path}: {error.message}")
                    else:
                        error_messages.append(error.message)
                
                logger.warning(f"Parameter validation failed: {error_messages}")
                return ValidationResult(valid=False, errors=error_messages)
            else:
                return ValidationResult(valid=True)
        except jsonschema.exceptions.SchemaError as e:
            logger.error(f"Invalid schema: {str(e)}")
            return ValidationResult(valid=False, errors=[f"Invalid schema: {str(e)}"])
        except Exception as e:
            logger.error(f"Error validating parameters: {str(e)}")
            return ValidationResult(valid=False, errors=[f"Validation error: {str(e)}"])
    
    def validate_strict(
        self,
        schema: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> None:
        """
        Validate parameters strictly, raising an exception on failure.
        
        Args:
            schema: JSON Schema
            parameters: Parameters to validate
            
        Raises:
            ToolSchemaValidationError: If validation fails
        """
        result = self.validate(schema, parameters)
        if not result.valid:
            raise ToolSchemaValidationError(result.errors)


class TypeChecker:
    """Type checker for validating parameter types."""
    
    @staticmethod
    def check_type(value: Any, expected_type: str) -> bool:
        """
        Check if a value matches an expected type.
        
        Args:
            value: Value to check
            expected_type: Expected type name
            
        Returns:
            bool: True if value matches expected type, False otherwise
        """
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        elif expected_type == "null":
            return value is None
        else:
            return False
    
    @staticmethod
    def get_type(value: Any) -> str:
        """
        Get the type name of a value.
        
        Args:
            value: Value to check
            
        Returns:
            str: Type name
        """
        if value is None:
            return "null"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return type(value).__name__
