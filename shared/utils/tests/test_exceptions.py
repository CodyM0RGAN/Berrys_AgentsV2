"""
Tests for exceptions module.

This module contains tests for the exceptions module
in shared/utils/src/exceptions.py.
"""

import pytest

from shared.utils.src.exceptions import (
    ValidationError,
    ServiceError,
    ServiceUnavailableError,
    ServiceTimeoutError,
    ServiceAuthenticationError,
    ServiceAuthorizationError,
    ServiceNotFoundError,
    ServiceBadRequestError,
    ServiceInternalError,
    CircuitBreakerOpenError,
    RetryExhaustedError,
    ModelValidationError,
    EnumValidationError,
    DatabaseError,
    ConfigurationError,
)


def test_validation_error():
    """Test ValidationError."""
    # Test with message only
    error = ValidationError("Validation failed")
    assert error.message == "Validation failed"
    assert error.validation_errors == {}
    
    # Test with validation errors
    validation_errors = {"field1": "Error 1", "field2": "Error 2"}
    error = ValidationError("Validation failed", validation_errors)
    assert error.message == "Validation failed"
    assert error.validation_errors == validation_errors


def test_service_error():
    """Test ServiceError."""
    # Test with default status code
    error = ServiceError("Service error", "test-service")
    assert error.message == "Service error"
    assert error.service_name == "test-service"
    assert error.status_code == 500
    
    # Test with custom status code
    error = ServiceError("Service error", "test-service", 400)
    assert error.message == "Service error"
    assert error.service_name == "test-service"
    assert error.status_code == 400


def test_service_unavailable_error():
    """Test ServiceUnavailableError."""
    # Test with default message
    error = ServiceUnavailableError("test-service")
    assert error.message == "Service test-service is unavailable"
    assert error.service_name == "test-service"
    assert error.status_code == 503
    
    # Test with custom message
    error = ServiceUnavailableError("test-service", "Custom message")
    assert error.message == "Custom message"
    assert error.service_name == "test-service"
    assert error.status_code == 503


def test_service_timeout_error():
    """Test ServiceTimeoutError."""
    # Test with default message
    error = ServiceTimeoutError("test-service")
    assert error.message == "Request to service test-service timed out"
    assert error.service_name == "test-service"
    assert error.status_code == 504
    
    # Test with custom message
    error = ServiceTimeoutError("test-service", "Custom message")
    assert error.message == "Custom message"
    assert error.service_name == "test-service"
    assert error.status_code == 504


def test_service_authentication_error():
    """Test ServiceAuthenticationError."""
    # Test with default message
    error = ServiceAuthenticationError("test-service")
    assert error.message == "Authentication with service test-service failed"
    assert error.service_name == "test-service"
    assert error.status_code == 401
    
    # Test with custom message
    error = ServiceAuthenticationError("test-service", "Custom message")
    assert error.message == "Custom message"
    assert error.service_name == "test-service"
    assert error.status_code == 401


def test_service_authorization_error():
    """Test ServiceAuthorizationError."""
    # Test with default message
    error = ServiceAuthorizationError("test-service")
    assert error.message == "Authorization with service test-service failed"
    assert error.service_name == "test-service"
    assert error.status_code == 403
    
    # Test with custom message
    error = ServiceAuthorizationError("test-service", "Custom message")
    assert error.message == "Custom message"
    assert error.service_name == "test-service"
    assert error.status_code == 403


def test_service_not_found_error():
    """Test ServiceNotFoundError."""
    # Test with default message
    error = ServiceNotFoundError("test-service", "Project", "123")
    assert error.message == "Project with ID 123 not found in service test-service"
    assert error.service_name == "test-service"
    assert error.resource_type == "Project"
    assert error.resource_id == "123"
    assert error.status_code == 404
    
    # Test with custom message
    error = ServiceNotFoundError("test-service", "Project", "123", "Custom message")
    assert error.message == "Custom message"
    assert error.service_name == "test-service"
    assert error.resource_type == "Project"
    assert error.resource_id == "123"
    assert error.status_code == 404


def test_service_bad_request_error():
    """Test ServiceBadRequestError."""
    # Test with message only
    error = ServiceBadRequestError("test-service", "Bad request")
    assert error.message == "Bad request"
    assert error.service_name == "test-service"
    assert error.validation_errors == {}
    assert error.status_code == 400
    
    # Test with validation errors
    validation_errors = {"field1": "Error 1", "field2": "Error 2"}
    error = ServiceBadRequestError("test-service", "Bad request", validation_errors)
    assert error.message == "Bad request"
    assert error.service_name == "test-service"
    assert error.validation_errors == validation_errors
    assert error.status_code == 400


def test_service_internal_error():
    """Test ServiceInternalError."""
    # Test with default message
    error = ServiceInternalError("test-service")
    assert error.message == "Service test-service encountered an internal error"
    assert error.service_name == "test-service"
    assert error.status_code == 500
    
    # Test with custom message
    error = ServiceInternalError("test-service", "Custom message")
    assert error.message == "Custom message"
    assert error.service_name == "test-service"
    assert error.status_code == 500


def test_circuit_breaker_open_error():
    """Test CircuitBreakerOpenError."""
    # Test with default message
    error = CircuitBreakerOpenError("test-service")
    assert error.message == "Circuit breaker for service test-service is open"
    assert error.service_name == "test-service"
    assert error.status_code == 503
    
    # Test with custom message
    error = CircuitBreakerOpenError("test-service", "Custom message")
    assert error.message == "Custom message"
    assert error.service_name == "test-service"
    assert error.status_code == 503


def test_retry_exhausted_error():
    """Test RetryExhaustedError."""
    # Test with default message
    error = RetryExhaustedError("test-service", "create_project", 3)
    assert error.message == "All 3 retry attempts for operation create_project on service test-service have been exhausted"
    assert error.service_name == "test-service"
    assert error.operation == "create_project"
    assert error.attempts == 3
    assert error.status_code == 503
    
    # Test with custom message
    error = RetryExhaustedError("test-service", "create_project", 3, "Custom message")
    assert error.message == "Custom message"
    assert error.service_name == "test-service"
    assert error.operation == "create_project"
    assert error.attempts == 3
    assert error.status_code == 503


def test_model_validation_error():
    """Test ModelValidationError."""
    # Test with message only
    error = ModelValidationError("Validation failed", "Project")
    assert error.message == "Validation failed"
    assert error.model_name == "Project"
    assert error.validation_errors == {}
    
    # Test with validation errors
    validation_errors = {"field1": "Error 1", "field2": "Error 2"}
    error = ModelValidationError("Validation failed", "Project", validation_errors)
    assert error.message == "Validation failed"
    assert error.model_name == "Project"
    assert error.validation_errors == validation_errors


def test_enum_validation_error():
    """Test EnumValidationError."""
    # Test without field name
    error = EnumValidationError(
        "Invalid status",
        "ProjectStatus",
        "INVALID",
        ["PLANNING", "IN_PROGRESS", "COMPLETED"]
    )
    assert error.message == "Invalid status"
    assert error.enum_name == "ProjectStatus"
    assert error.value == "INVALID"
    assert error.valid_values == ["PLANNING", "IN_PROGRESS", "COMPLETED"]
    assert error.validation_errors == {}
    
    # Test with field name
    error = EnumValidationError(
        "Invalid status",
        "ProjectStatus",
        "INVALID",
        ["PLANNING", "IN_PROGRESS", "COMPLETED"],
        "status"
    )
    assert error.message == "Invalid status"
    assert error.enum_name == "ProjectStatus"
    assert error.value == "INVALID"
    assert error.valid_values == ["PLANNING", "IN_PROGRESS", "COMPLETED"]
    assert error.validation_errors == {
        "status": "Invalid ProjectStatus value: INVALID. Valid values are: ['PLANNING', 'IN_PROGRESS', 'COMPLETED']"
    }


def test_database_error():
    """Test DatabaseError."""
    # Test without table
    error = DatabaseError("Database error", "SELECT")
    assert error.message == "Database error"
    assert error.operation == "SELECT"
    assert error.table is None
    
    # Test with table
    error = DatabaseError("Database error", "SELECT", "project")
    assert error.message == "Database error"
    assert error.operation == "SELECT"
    assert error.table == "project"


def test_configuration_error():
    """Test ConfigurationError."""
    # Test without config key
    error = ConfigurationError("Configuration error")
    assert error.message == "Configuration error"
    assert error.config_key is None
    
    # Test with config key
    error = ConfigurationError("Configuration error", "DATABASE_URL")
    assert error.message == "Configuration error"
    assert error.config_key == "DATABASE_URL"
