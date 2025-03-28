"""
Standardized Error Response Models

This module provides standardized error response models for use across all services.
These models ensure consistent error handling and reporting throughout the system.

Usage:
    ```python
    from shared.models.src.api.errors import ErrorResponse, ErrorDetail
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from datetime import datetime
    
    app = FastAPI()
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        error = ErrorResponse(
            code="VALIDATION_ERROR" if exc.status_code == 422 else "API_ERROR",
            message=str(exc.detail),
            details={"status_code": exc.status_code},
            request_id=request.state.request_id,
            timestamp=datetime.utcnow()
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": error.dict()}
        )
    
    @app.get("/items/{item_id}")
    async def read_item(item_id: int):
        if item_id < 0:
            error = ErrorResponse(
                code="INVALID_ITEM_ID",
                message="Item ID must be a positive integer",
                details={"item_id": item_id},
                request_id=request.state.request_id,
                timestamp=datetime.utcnow()
            )
            return JSONResponse(
                status_code=400,
                content={"error": error.dict()}
            )
        # ...
    ```
"""

from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, validator


class ErrorDetail(BaseModel):
    """
    Detailed information about a specific error.
    
    Attributes:
        field: The field that caused the error
        code: Error code specific to this field
        message: Human-readable error message
    """
    field: str
    code: str
    message: str


class ErrorResponse(BaseModel):
    """
    Standardized error response model.
    
    Attributes:
        code: Error code (e.g., "VALIDATION_ERROR", "RESOURCE_NOT_FOUND")
        message: Human-readable error message
        details: Additional error details (field-specific errors or context)
        request_id: Unique identifier for the request (for tracing)
        timestamp: Time when the error occurred
    """
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('code')
    def code_must_be_uppercase(cls, v):
        """Ensure error codes are uppercase."""
        return v.upper()
    
    class Config:
        schema_extra = {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": {
                    "name": "Field is required",
                    "age": "Must be a positive integer"
                },
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-03-26T19:45:00Z"
            }
        }


class ValidationErrorResponse(ErrorResponse):
    """
    Error response model specifically for validation errors.
    
    Attributes:
        code: Always "VALIDATION_ERROR"
        message: Human-readable error message
        details: Dictionary of field-specific validation errors
        request_id: Unique identifier for the request (for tracing)
        timestamp: Time when the error occurred
    """
    code: str = "VALIDATION_ERROR"
    details: Dict[str, str] = Field(default_factory=dict)


class ResourceNotFoundResponse(ErrorResponse):
    """
    Error response model for resource not found errors.
    
    Attributes:
        code: Always "RESOURCE_NOT_FOUND"
        message: Human-readable error message
        details: Details about the resource that was not found
        request_id: Unique identifier for the request (for tracing)
        timestamp: Time when the error occurred
    """
    code: str = "RESOURCE_NOT_FOUND"
    details: Dict[str, Any] = Field(default_factory=dict)


class ServiceUnavailableResponse(ErrorResponse):
    """
    Error response model for service unavailable errors.
    
    Attributes:
        code: Always "SERVICE_UNAVAILABLE"
        message: Human-readable error message
        details: Details about the service that is unavailable
        request_id: Unique identifier for the request (for tracing)
        timestamp: Time when the error occurred
    """
    code: str = "SERVICE_UNAVAILABLE"
    details: Dict[str, Any] = Field(default_factory=dict)


class UnauthorizedResponse(ErrorResponse):
    """
    Error response model for unauthorized access errors.
    
    Attributes:
        code: Always "UNAUTHORIZED"
        message: Human-readable error message
        details: Additional details about the authorization failure
        request_id: Unique identifier for the request (for tracing)
        timestamp: Time when the error occurred
    """
    code: str = "UNAUTHORIZED"
    details: Dict[str, Any] = Field(default_factory=dict)


class ForbiddenResponse(ErrorResponse):
    """
    Error response model for forbidden access errors.
    
    Attributes:
        code: Always "FORBIDDEN"
        message: Human-readable error message
        details: Additional details about the permission failure
        request_id: Unique identifier for the request (for tracing)
        timestamp: Time when the error occurred
    """
    code: str = "FORBIDDEN"
    details: Dict[str, Any] = Field(default_factory=dict)


class ConflictResponse(ErrorResponse):
    """
    Error response model for resource conflict errors.
    
    Attributes:
        code: Always "CONFLICT"
        message: Human-readable error message
        details: Details about the conflict
        request_id: Unique identifier for the request (for tracing)
        timestamp: Time when the error occurred
    """
    code: str = "CONFLICT"
    details: Dict[str, Any] = Field(default_factory=dict)


class RateLimitExceededResponse(ErrorResponse):
    """
    Error response model for rate limit exceeded errors.
    
    Attributes:
        code: Always "RATE_LIMIT_EXCEEDED"
        message: Human-readable error message
        details: Details about the rate limit
        request_id: Unique identifier for the request (for tracing)
        timestamp: Time when the error occurred
    """
    code: str = "RATE_LIMIT_EXCEEDED"
    details: Dict[str, Any] = Field(default_factory=dict)


class InternalServerErrorResponse(ErrorResponse):
    """
    Error response model for internal server errors.
    
    Attributes:
        code: Always "INTERNAL_SERVER_ERROR"
        message: Human-readable error message
        details: Additional details about the error
        request_id: Unique identifier for the request (for tracing)
        timestamp: Time when the error occurred
    """
    code: str = "INTERNAL_SERVER_ERROR"
    details: Dict[str, Any] = Field(default_factory=dict)


def create_error_response(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response dictionary.
    
    Args:
        code: Error code
        message: Human-readable error message
        details: Additional error details
        request_id: Unique identifier for the request
        
    Returns:
        Dictionary containing the error response
    """
    error = ErrorResponse(
        code=code,
        message=message,
        details=details,
        request_id=request_id,
        timestamp=datetime.utcnow()
    )
    return {"error": error.dict()}


def create_validation_error_response(
    validation_errors: Dict[str, str],
    message: str = "Validation error",
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized validation error response dictionary.
    
    Args:
        validation_errors: Dictionary of field-specific validation errors
        message: Human-readable error message
        request_id: Unique identifier for the request
        
    Returns:
        Dictionary containing the validation error response
    """
    error = ValidationErrorResponse(
        message=message,
        details=validation_errors,
        request_id=request_id,
        timestamp=datetime.utcnow()
    )
    return {"error": error.dict()}


def create_resource_not_found_response(
    resource_type: str,
    resource_id: Any,
    message: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized resource not found error response dictionary.
    
    Args:
        resource_type: Type of resource that was not found
        resource_id: ID of the resource that was not found
        message: Human-readable error message
        request_id: Unique identifier for the request
        
    Returns:
        Dictionary containing the resource not found error response
    """
    if message is None:
        message = f"{resource_type} with ID {resource_id} not found"
    
    error = ResourceNotFoundResponse(
        message=message,
        details={
            "resource_type": resource_type,
            "resource_id": str(resource_id)
        },
        request_id=request_id,
        timestamp=datetime.utcnow()
    )
    return {"error": error.dict()}


def create_service_unavailable_response(
    service_name: str,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized service unavailable error response dictionary.
    
    Args:
        service_name: Name of the service that is unavailable
        message: Human-readable error message
        details: Additional details about the service unavailability
        request_id: Unique identifier for the request
        
    Returns:
        Dictionary containing the service unavailable error response
    """
    if message is None:
        message = f"Service {service_name} is currently unavailable"
    
    error_details = {"service_name": service_name}
    if details:
        error_details.update(details)
    
    error = ServiceUnavailableResponse(
        message=message,
        details=error_details,
        request_id=request_id,
        timestamp=datetime.utcnow()
    )
    return {"error": error.dict()}
