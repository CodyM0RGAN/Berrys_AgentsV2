"""
Standardized API response models for the Berrys_AgentsV2 project.

This module provides consistent response structures for all API endpoints
across services, including:
- Standard success and error responses
- Pagination support
- Filtering and sorting utilities
"""

from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel, Field, create_model

T = TypeVar('T')


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    severity: ErrorSeverity = Field(default=ErrorSeverity.ERROR, description="Error severity")
    field: Optional[str] = Field(default=None, description="Field that caused the error")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    success: bool = Field(default=False, description="Always false for error responses")
    message: str = Field(..., description="Human-readable error message")
    errors: List[ErrorDetail] = Field(default_factory=list, description="List of error details")


class PaginationMetadata(BaseModel):
    """Pagination metadata."""
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class SortDirection(str, Enum):
    """Sort direction."""
    ASC = "ASC"
    DESC = "DESC"


class SortField(BaseModel):
    """Sort field specification."""
    field: str = Field(..., description="Field name to sort by")
    direction: SortDirection = Field(default=SortDirection.ASC, description="Sort direction")


class FilterOperator(str, Enum):
    """Filter operators."""
    EQ = "EQ"  # Equal
    NE = "NE"  # Not equal
    GT = "GT"  # Greater than
    GE = "GE"  # Greater than or equal
    LT = "LT"  # Less than
    LE = "LE"  # Less than or equal
    IN = "IN"  # In list
    NIN = "NIN"  # Not in list
    LIKE = "LIKE"  # Like (SQL LIKE)
    ILIKE = "ILIKE"  # Case-insensitive like
    BETWEEN = "BETWEEN"  # Between two values
    NULL = "NULL"  # Is null
    NOT_NULL = "NOT_NULL"  # Is not null


class FilterCondition(BaseModel):
    """Filter condition."""
    field: str = Field(..., description="Field name to filter on")
    operator: FilterOperator = Field(..., description="Filter operator")
    value: Any = Field(..., description="Filter value")


class QueryMetadata(BaseModel):
    """Query metadata."""
    filters: Optional[List[FilterCondition]] = Field(default=None, description="Applied filters")
    sort: Optional[List[SortField]] = Field(default=None, description="Applied sort fields")
    pagination: Optional[PaginationMetadata] = Field(default=None, description="Pagination metadata")


class BaseResponse(BaseModel):
    """Base response model."""
    success: bool = Field(default=True, description="Whether the request was successful")
    message: Optional[str] = Field(default=None, description="Human-readable message")


class DataResponse(BaseResponse, Generic[T]):
    """Response model with data."""
    data: T = Field(..., description="Response data")


class ListResponse(BaseResponse, Generic[T]):
    """Response model with a list of items."""
    items: List[T] = Field(..., description="List of items")
    metadata: Optional[QueryMetadata] = Field(default=None, description="Query metadata")


# Aliases for backward compatibility
class StandardResponse(BaseResponse):
    """Alias for BaseResponse for backward compatibility."""
    pass


class PaginatedResponse(ListResponse, Generic[T]):
    """Alias for ListResponse for backward compatibility."""
    pass


class ListRequestParams(BaseModel):
    """Parameters for list requests with pagination, filtering, and sorting."""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    filters: Optional[List[FilterCondition]] = Field(default=None, description="Filter conditions")
    sort: Optional[List[SortField]] = Field(default=None, description="Sort fields")


def create_data_response_model(
    data_model: Type[Any],
    model_name: Optional[str] = None
) -> Type[DataResponse]:
    """
    Create a DataResponse model with a specific data type.

    Args:
        data_model: The model class for the data field.
        model_name: Optional name for the created model.

    Returns:
        A new DataResponse model with the specified data type.
    """
    if model_name is None:
        model_name = f"{data_model.__name__}Response"
    
    return create_model(
        model_name,
        __base__=DataResponse,
        data=(data_model, ...),
    )


def create_list_response_model(
    item_model: Type[Any],
    model_name: Optional[str] = None
) -> Type[ListResponse]:
    """
    Create a ListResponse model with a specific item type.

    Args:
        item_model: The model class for the items.
        model_name: Optional name for the created model.

    Returns:
        A new ListResponse model with the specified item type.
    """
    if model_name is None:
        model_name = f"{item_model.__name__}ListResponse"
    
    return create_model(
        model_name,
        __base__=ListResponse,
        items=(List[item_model], ...),
    )


# Common error factories
def validation_error(message: str, field: str, details: Optional[Dict[str, Any]] = None) -> ErrorResponse:
    """
    Create a validation error response.

    Args:
        message: The error message.
        field: The field that failed validation.
        details: Optional additional details.

    Returns:
        An ErrorResponse for validation errors.
    """
    return ErrorResponse(
        message=message,
        errors=[
            ErrorDetail(
                code="VALIDATION_ERROR",
                message=message,
                severity=ErrorSeverity.ERROR,
                field=field,
                details=details
            )
        ]
    )


def not_found_error(entity_type: str, entity_id: str) -> ErrorResponse:
    """
    Create a not found error response.

    Args:
        entity_type: The type of entity that was not found.
        entity_id: The ID of the entity that was not found.

    Returns:
        An ErrorResponse for not found errors.
    """
    return ErrorResponse(
        message=f"{entity_type} with ID {entity_id} not found",
        errors=[
            ErrorDetail(
                code="NOT_FOUND",
                message=f"{entity_type} with ID {entity_id} not found",
                severity=ErrorSeverity.ERROR,
                details={"entity_type": entity_type, "entity_id": entity_id}
            )
        ]
    )


def server_error(message: str, details: Optional[Dict[str, Any]] = None) -> ErrorResponse:
    """
    Create a server error response.

    Args:
        message: The error message.
        details: Optional additional details.

    Returns:
        An ErrorResponse for server errors.
    """
    return ErrorResponse(
        message=message,
        errors=[
            ErrorDetail(
                code="SERVER_ERROR",
                message=message,
                severity=ErrorSeverity.CRITICAL,
                details=details
            )
        ]
    )


def unauthorized_error(message: str = "Unauthorized") -> ErrorResponse:
    """
    Create an unauthorized error response.

    Args:
        message: The error message.

    Returns:
        An ErrorResponse for unauthorized errors.
    """
    return ErrorResponse(
        message=message,
        errors=[
            ErrorDetail(
                code="UNAUTHORIZED",
                message=message,
                severity=ErrorSeverity.ERROR
            )
        ]
    )


def forbidden_error(message: str = "Forbidden") -> ErrorResponse:
    """
    Create a forbidden error response.

    Args:
        message: The error message.

    Returns:
        An ErrorResponse for forbidden errors.
    """
    return ErrorResponse(
        message=message,
        errors=[
            ErrorDetail(
                code="FORBIDDEN",
                message=message,
                severity=ErrorSeverity.ERROR
            )
        ]
    )
