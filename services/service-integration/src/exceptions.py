"""
Custom exceptions for the Service Integration service.
"""
from fastapi import HTTPException, status
from typing import Any, Dict, Optional


class ServiceIntegrationError(Exception):
    """Base exception for all Service Integration service errors."""
    pass


class ServiceDiscoveryError(ServiceIntegrationError):
    """Raised when there's an error in service discovery."""
    pass


class ServiceRegistryError(ServiceIntegrationError):
    """Raised when there's an error in service registry operations."""
    pass


class ServiceNotFoundError(ServiceDiscoveryError):
    """Raised when a requested service is not found."""
    pass


class CircuitOpenError(ServiceIntegrationError):
    """Raised when a circuit breaker is open."""
    pass


class ServiceUnavailableError(ServiceIntegrationError):
    """Raised when a service is unavailable."""
    pass


class ServiceConnectionError(ServiceIntegrationError):
    """Raised when there's an error connecting to a service."""
    pass


class ServiceTimeoutError(ServiceIntegrationError):
    """Raised when a service request times out."""
    pass


class WorkflowError(ServiceIntegrationError):
    """Raised when there's an error in workflow execution."""
    pass


class UnknownRequestTypeError(ServiceIntegrationError):
    """Raised when an unknown request type is received."""
    pass


def service_exception_handler(exception: ServiceIntegrationError) -> HTTPException:
    """
    Convert service exceptions to HTTP exceptions.
    
    This provides a standard way to convert internal service exceptions
    to HTTP responses with appropriate status codes and details.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = str(exception)
    
    if isinstance(exception, ServiceNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exception, ServiceUnavailableError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(exception, ServiceTimeoutError):
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
    elif isinstance(exception, UnknownRequestTypeError):
        status_code = status.HTTP_400_BAD_REQUEST
    
    return HTTPException(
        status_code=status_code,
        detail=detail
    )
