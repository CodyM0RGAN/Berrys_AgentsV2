from fastapi import status
from typing import Optional, Any, Dict


class ServiceError(Exception):
    """
    Base exception for service-specific errors.
    """
    def __init__(
        self,
        message: str,
        code: str = "service_error",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ResourceNotFoundError(ServiceError):
    """
    Exception for resource not found errors.
    """
    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None,
        code: str = "resource_not_found",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = message or f"{resource_type} with ID {resource_id} not found"
        details = details or {"resource_type": resource_type, "resource_id": resource_id}
        super().__init__(message, code, status.HTTP_404_NOT_FOUND, details)


class ValidationError(ServiceError):
    """
    Exception for validation errors.
    """
    def __init__(
        self,
        message: str = "Validation error",
        code: str = "validation_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, status.HTTP_400_BAD_REQUEST, details)


class AuthenticationError(ServiceError):
    """
    Exception for authentication errors.
    """
    def __init__(
        self,
        message: str = "Authentication failed",
        code: str = "authentication_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, status.HTTP_401_UNAUTHORIZED, details)


class AuthorizationError(ServiceError):
    """
    Exception for authorization errors.
    """
    def __init__(
        self,
        message: str = "Not authorized to perform this action",
        code: str = "authorization_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, status.HTTP_403_FORBIDDEN, details)


class ConflictError(ServiceError):
    """
    Exception for conflict errors (e.g., duplicate resources).
    """
    def __init__(
        self,
        message: str = "Resource conflict",
        code: str = "conflict_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, status.HTTP_409_CONFLICT, details)


class ExternalServiceError(ServiceError):
    """
    Exception for errors from external services.
    """
    def __init__(
        self,
        service: str,
        message: str = "External service error",
        code: str = "external_service_error",
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.service = service
        details = details or {"service": service}
        super().__init__(message, code, status_code, details)


class DatabaseError(ServiceError):
    """
    Exception for database errors.
    """
    def __init__(
        self,
        message: str = "Database error",
        code: str = "database_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


class RateLimitError(ServiceError):
    """
    Exception for rate limit errors.
    """
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        code: str = "rate_limit_exceeded",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, status.HTTP_429_TOO_MANY_REQUESTS, details)
