"""
Exceptions for the Berrys_AgentsV2 system.

This module provides custom exceptions for the system.
"""

from typing import Dict, Optional


class ValidationError(Exception):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, validation_errors: Optional[Dict[str, str]] = None):
        """
        Initialize ValidationError.
        
        Args:
            message: Error message
            validation_errors: Dictionary of field-specific validation errors
        """
        self.message = message
        self.validation_errors = validation_errors or {}
        super().__init__(message)


class ServiceError(Exception):
    """Exception raised for service errors."""
    
    def __init__(self, message: str, service_name: str, status_code: int = 500):
        """
        Initialize ServiceError.
        
        Args:
            message: Error message
            service_name: Name of the service that raised the error
            status_code: HTTP status code
        """
        self.message = message
        self.service_name = service_name
        self.status_code = status_code
        super().__init__(message)


class ServiceUnavailableError(ServiceError):
    """Exception raised when a service is unavailable."""
    
    def __init__(self, service_name: str, message: Optional[str] = None):
        """
        Initialize ServiceUnavailableError.
        
        Args:
            service_name: Name of the service that is unavailable
            message: Error message
        """
        message = message or f"Service {service_name} is unavailable"
        super().__init__(message, service_name, 503)


class ServiceTimeoutError(ServiceError):
    """Exception raised when a service request times out."""
    
    def __init__(self, service_name: str, message: Optional[str] = None):
        """
        Initialize ServiceTimeoutError.
        
        Args:
            service_name: Name of the service that timed out
            message: Error message
        """
        message = message or f"Request to service {service_name} timed out"
        super().__init__(message, service_name, 504)


class ServiceAuthenticationError(ServiceError):
    """Exception raised when authentication with a service fails."""
    
    def __init__(self, service_name: str, message: Optional[str] = None):
        """
        Initialize ServiceAuthenticationError.
        
        Args:
            service_name: Name of the service that authentication failed for
            message: Error message
        """
        message = message or f"Authentication with service {service_name} failed"
        super().__init__(message, service_name, 401)


class ServiceAuthorizationError(ServiceError):
    """Exception raised when authorization with a service fails."""
    
    def __init__(self, service_name: str, message: Optional[str] = None):
        """
        Initialize ServiceAuthorizationError.
        
        Args:
            service_name: Name of the service that authorization failed for
            message: Error message
        """
        message = message or f"Authorization with service {service_name} failed"
        super().__init__(message, service_name, 403)


class ServiceNotFoundError(ServiceError):
    """Exception raised when a service resource is not found."""
    
    def __init__(self, service_name: str, resource_type: str, resource_id: str, message: Optional[str] = None):
        """
        Initialize ServiceNotFoundError.
        
        Args:
            service_name: Name of the service that the resource was not found in
            resource_type: Type of resource that was not found
            resource_id: ID of the resource that was not found
            message: Error message
        """
        self.resource_type = resource_type
        self.resource_id = resource_id
        message = message or f"{resource_type} with ID {resource_id} not found in service {service_name}"
        super().__init__(message, service_name, 404)


class ServiceBadRequestError(ServiceError):
    """Exception raised when a service request is invalid."""
    
    def __init__(self, service_name: str, message: str, validation_errors: Optional[Dict[str, str]] = None):
        """
        Initialize ServiceBadRequestError.
        
        Args:
            service_name: Name of the service that the request was invalid for
            message: Error message
            validation_errors: Dictionary of field-specific validation errors
        """
        self.validation_errors = validation_errors or {}
        super().__init__(message, service_name, 400)


class ServiceInternalError(ServiceError):
    """Exception raised when a service encounters an internal error."""
    
    def __init__(self, service_name: str, message: Optional[str] = None):
        """
        Initialize ServiceInternalError.
        
        Args:
            service_name: Name of the service that encountered the error
            message: Error message
        """
        message = message or f"Service {service_name} encountered an internal error"
        super().__init__(message, service_name, 500)


class CircuitBreakerOpenError(ServiceError):
    """Exception raised when a circuit breaker is open."""
    
    def __init__(self, service_name: str, message: Optional[str] = None):
        """
        Initialize CircuitBreakerOpenError.
        
        Args:
            service_name: Name of the service that the circuit breaker is open for
            message: Error message
        """
        message = message or f"Circuit breaker for service {service_name} is open"
        super().__init__(message, service_name, 503)


class RetryExhaustedError(ServiceError):
    """Exception raised when all retry attempts have been exhausted."""
    
    def __init__(self, service_name: str, operation: str, attempts: int, message: Optional[str] = None):
        """
        Initialize RetryExhaustedError.
        
        Args:
            service_name: Name of the service that the retry attempts were exhausted for
            operation: Name of the operation that was being retried
            attempts: Number of retry attempts that were made
            message: Error message
        """
        self.operation = operation
        self.attempts = attempts
        message = message or f"All {attempts} retry attempts for operation {operation} on service {service_name} have been exhausted"
        super().__init__(message, service_name, 503)


class ModelValidationError(ValidationError):
    """Exception raised for model validation errors."""
    
    def __init__(self, message: str, model_name: str, validation_errors: Optional[Dict[str, str]] = None):
        """
        Initialize ModelValidationError.
        
        Args:
            message: Error message
            model_name: Name of the model that validation failed for
            validation_errors: Dictionary of field-specific validation errors
        """
        self.model_name = model_name
        super().__init__(message, validation_errors)


class EnumValidationError(ValidationError):
    """Exception raised for enum validation errors."""
    
    def __init__(self, message: str, enum_name: str, value: str, valid_values: list, field_name: Optional[str] = None):
        """
        Initialize EnumValidationError.
        
        Args:
            message: Error message
            enum_name: Name of the enum that validation failed for
            value: Value that failed validation
            valid_values: List of valid values for the enum
            field_name: Name of the field that validation failed for
        """
        self.enum_name = enum_name
        self.value = value
        self.valid_values = valid_values
        validation_errors = {}
        if field_name:
            validation_errors[field_name] = f"Invalid {enum_name} value: {value}. Valid values are: {valid_values}"
        super().__init__(message, validation_errors)


class DatabaseError(Exception):
    """Exception raised for database errors."""
    
    def __init__(self, message: str, operation: str, table: Optional[str] = None):
        """
        Initialize DatabaseError.
        
        Args:
            message: Error message
            operation: Database operation that failed
            table: Table that the operation was performed on
        """
        self.message = message
        self.operation = operation
        self.table = table
        super().__init__(message)


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        """
        Initialize ConfigurationError.
        
        Args:
            message: Error message
            config_key: Configuration key that caused the error
        """
        self.message = message
        self.config_key = config_key
        super().__init__(message)
