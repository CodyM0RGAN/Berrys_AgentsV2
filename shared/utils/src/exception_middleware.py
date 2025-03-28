"""
Exception handling middleware for FastAPI applications.

This module provides middleware for FastAPI applications to ensure consistent
exception handling across services. It converts exceptions to standardized
error responses and includes request IDs in error responses.
"""
import logging
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Type, Union

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from shared.utils.src.exceptions import (
    CircuitBreakerError,
    CircuitBreakerOpenError,
    DatabaseError,
    ServiceAuthenticationError as AuthenticationError,
    ServiceAuthorizationError as AuthorizationError,
    ServiceBadRequestError as BadRequestError,
    ServiceError as BaseServiceException,
    ServiceError as ConflictError,  # Using ServiceError as a base for ConflictError
    ServiceInternalError as InternalServerError,
    ServiceNotFoundError as ResourceNotFoundError,
    ServiceUnavailableError,
    ServiceTimeoutError as TimeoutError,
    ValidationError as ServiceValidationError,
)
from shared.utils.src.request_id import get_request_id

# Set up logger
logger = logging.getLogger(__name__)


def create_error_response(
    status_code: int,
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        code: Error code
        message: Error message
        details: Additional error details
        request_id: Request ID
        
    Returns:
        Error response dictionary
    """
    response = {
        "error": {
            "code": code,
            "message": message,
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    if request_id:
        response["error"]["request_id"] = request_id
    
    return response


def exception_to_http_response(
    exception: Exception,
    request: Optional[Request] = None,
    include_exception_details: bool = False,
) -> JSONResponse:
    """
    Convert an exception to a standardized HTTP response.
    
    Args:
        exception: Exception to convert
        request: FastAPI request (optional)
        include_exception_details: Whether to include exception details in the response
        
    Returns:
        JSONResponse with standardized error format
    """
    request_id = get_request_id(request) if request else None
    
    # Get exception details for logging and optional inclusion in response
    exception_details = {
        "type": type(exception).__name__,
        "traceback": traceback.format_exc(),
    }
    
    # Convert specific exception types to appropriate responses
    if isinstance(exception, HTTPException):
        status_code = exception.status_code
        code = f"HTTP_{status_code}"
        message = exception.detail
        details = None
    
    elif isinstance(exception, RequestValidationError):
        status_code = HTTP_422_UNPROCESSABLE_ENTITY
        code = "VALIDATION_ERROR"
        message = "Request validation error"
        details = {"validation_errors": exception.errors()}
    
    elif isinstance(exception, ValidationError):
        status_code = HTTP_422_UNPROCESSABLE_ENTITY
        code = "VALIDATION_ERROR"
        message = "Validation error"
        details = {"validation_errors": exception.errors()}
    
    elif isinstance(exception, ServiceValidationError):
        status_code = HTTP_422_UNPROCESSABLE_ENTITY
        code = getattr(exception, 'code', "VALIDATION_ERROR")
        message = exception.message
        details = {"validation_errors": exception.validation_errors}
    
    elif isinstance(exception, ResourceNotFoundError):
        status_code = HTTP_404_NOT_FOUND
        code = getattr(exception, 'code', "RESOURCE_NOT_FOUND")
        message = exception.message
        details = getattr(exception, 'details', {"service_name": exception.service_name, "resource_type": exception.resource_type, "resource_id": exception.resource_id})
    
    elif isinstance(exception, AuthenticationError):
        status_code = HTTP_401_UNAUTHORIZED
        code = getattr(exception, 'code', "AUTHENTICATION_ERROR")
        message = exception.message
        details = getattr(exception, 'details', {"service_name": exception.service_name})
    
    elif isinstance(exception, AuthorizationError):
        status_code = HTTP_403_FORBIDDEN
        code = getattr(exception, 'code', "AUTHORIZATION_ERROR")
        message = exception.message
        details = getattr(exception, 'details', {"service_name": exception.service_name})
    
    elif isinstance(exception, ConflictError):
        status_code = HTTP_409_CONFLICT
        code = getattr(exception, 'code', "CONFLICT_ERROR")
        message = exception.message
        details = getattr(exception, 'details', {"service_name": exception.service_name})
    
    elif isinstance(exception, CircuitBreakerError):
        status_code = HTTP_503_SERVICE_UNAVAILABLE
        code = "CIRCUIT_BREAKER_OPEN"
        message = exception.message
        details = {"circuit_name": exception.circuit_name}
    
    elif isinstance(exception, CircuitBreakerOpenError):
        status_code = HTTP_503_SERVICE_UNAVAILABLE
        code = getattr(exception, 'code', "CIRCUIT_BREAKER_OPEN")
        message = exception.message
        details = getattr(exception, 'details', {"service_name": exception.service_name})
    
    elif isinstance(exception, ServiceUnavailableError):
        status_code = HTTP_503_SERVICE_UNAVAILABLE
        code = getattr(exception, 'code', "SERVICE_UNAVAILABLE")
        message = exception.message
        details = getattr(exception, 'details', {"service_name": exception.service_name})
    
    elif isinstance(exception, TimeoutError):
        status_code = HTTP_503_SERVICE_UNAVAILABLE
        code = getattr(exception, 'code', "TIMEOUT_ERROR")
        message = exception.message
        details = getattr(exception, 'details', {"service_name": exception.service_name})
    
    elif isinstance(exception, DatabaseError):
        status_code = HTTP_500_INTERNAL_SERVER_ERROR
        code = getattr(exception, 'code', "DATABASE_ERROR")
        message = exception.message
        details = getattr(exception, 'details', {"operation": exception.operation, "table": exception.table})
    
    elif isinstance(exception, BadRequestError):
        status_code = HTTP_400_BAD_REQUEST
        code = getattr(exception, 'code', "BAD_REQUEST")
        message = exception.message
        details = getattr(exception, 'details', {"service_name": exception.service_name, "validation_errors": getattr(exception, 'validation_errors', {})})
    
    elif isinstance(exception, BaseServiceException):
        status_code = HTTP_500_INTERNAL_SERVER_ERROR
        code = getattr(exception, 'code', "INTERNAL_SERVER_ERROR")
        message = exception.message
        details = getattr(exception, 'details', {"service_name": exception.service_name})
    
    else:
        status_code = HTTP_500_INTERNAL_SERVER_ERROR
        code = "INTERNAL_SERVER_ERROR"
        message = str(exception) or "An unexpected error occurred"
        details = None
    
    # Log the error
    log_message = f"Exception: {code} - {message}"
    log_context = {"request_id": request_id} if request_id else {}
    
    if status_code >= 500:
        logger.error(log_message, exc_info=True, extra=log_context)
    else:
        logger.warning(log_message, extra=log_context)
    
    # Include exception details if requested
    if include_exception_details and status_code >= 500:
        if details is None:
            details = {}
        details["exception"] = exception_details
    
    # Create and return the response
    error_response = create_error_response(
        status_code=status_code,
        code=code,
        message=message,
        details=details,
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response,
    )


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for exception handling.
    
    This middleware:
    1. Catches exceptions raised during request processing
    2. Converts exceptions to standardized error responses
    3. Includes request IDs in error responses
    4. Logs exceptions with context information
    """
    
    def __init__(
        self,
        app: FastAPI,
        include_exception_details: bool = False,
    ):
        """
        Initialize ExceptionHandlingMiddleware.
        
        Args:
            app: FastAPI application
            include_exception_details: Whether to include exception details in error responses
        """
        super().__init__(app)
        self.include_exception_details = include_exception_details
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process the request and handle exceptions.
        
        Args:
            request: FastAPI request
            call_next: Next middleware or endpoint
            
        Returns:
            FastAPI response
        """
        try:
            return await call_next(request)
        except Exception as e:
            return exception_to_http_response(
                exception=e,
                request=request,
                include_exception_details=self.include_exception_details,
            )


def add_exception_handlers(
    app: FastAPI,
    include_exception_details: bool = False,
) -> None:
    """
    Add exception handlers to a FastAPI application.
    
    Args:
        app: FastAPI application
        include_exception_details: Whether to include exception details in error responses
    """
    # Define a generic exception handler
    def create_exception_handler(exception_class: Type[Exception]) -> Callable:
        async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
            return exception_to_http_response(
                exception=exc,
                request=request,
                include_exception_details=include_exception_details,
            )
        return exception_handler
    
    # Add handlers for specific exception types
    app.add_exception_handler(HTTPException, create_exception_handler(HTTPException))
    app.add_exception_handler(RequestValidationError, create_exception_handler(RequestValidationError))
    app.add_exception_handler(ValidationError, create_exception_handler(ValidationError))
    app.add_exception_handler(ServiceValidationError, create_exception_handler(ServiceValidationError))
    app.add_exception_handler(ResourceNotFoundError, create_exception_handler(ResourceNotFoundError))
    app.add_exception_handler(AuthenticationError, create_exception_handler(AuthenticationError))
    app.add_exception_handler(AuthorizationError, create_exception_handler(AuthorizationError))
    app.add_exception_handler(ConflictError, create_exception_handler(ConflictError))
    app.add_exception_handler(CircuitBreakerError, create_exception_handler(CircuitBreakerError))
    app.add_exception_handler(CircuitBreakerOpenError, create_exception_handler(CircuitBreakerOpenError))
    app.add_exception_handler(ServiceUnavailableError, create_exception_handler(ServiceUnavailableError))
    app.add_exception_handler(TimeoutError, create_exception_handler(TimeoutError))
    app.add_exception_handler(DatabaseError, create_exception_handler(DatabaseError))
    app.add_exception_handler(BadRequestError, create_exception_handler(BadRequestError))
    app.add_exception_handler(BaseServiceException, create_exception_handler(BaseServiceException))
    app.add_exception_handler(Exception, create_exception_handler(Exception))
    
    logger.info("Added exception handlers to FastAPI application")
