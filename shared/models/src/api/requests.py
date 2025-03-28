"""
Standardized API request models for the Berrys_AgentsV2 project.

This module provides consistent request structures for all API endpoints
across services, including:
- Pagination parameters
- Filtering parameters
- Sorting parameters
- Common request base classes
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from shared.models.src.base import BaseModel as BaseApiModel


class PaginationParams(BaseApiModel):
    """Pagination parameters for list endpoints."""
    
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")


class SortDirection(str, Enum):
    """Sort direction."""
    ASC = "ASC"
    DESC = "DESC"


class SortParams(BaseApiModel):
    """Sort parameters for list endpoints."""
    
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


class FilterParams(BaseApiModel):
    """Filter parameters for list endpoints."""
    
    field: str = Field(..., description="Field name to filter on")
    operator: FilterOperator = Field(..., description="Filter operator")
    value: Any = Field(..., description="Filter value")


class ListRequestParams(BaseApiModel):
    """Common parameters for list endpoints."""
    
    pagination: Optional[PaginationParams] = Field(default=None, description="Pagination parameters")
    sort: Optional[List[SortParams]] = Field(default=None, description="Sort parameters")
    filters: Optional[List[FilterParams]] = Field(default=None, description="Filter parameters")


class SearchParams(BaseApiModel):
    """Search parameters for search endpoints."""
    
    query: str = Field(..., min_length=1, description="Search query")
    fields: Optional[List[str]] = Field(default=None, description="Fields to search in")


class DateRangeParams(BaseApiModel):
    """Date range parameters for filtering by date."""
    
    start_date: str = Field(..., description="Start date (ISO format)")
    end_date: str = Field(..., description="End date (ISO format)")
    
    @field_validator('start_date', 'end_date')
    def validate_date_format(cls, v: str) -> str:
        """Validate that the date is in ISO format."""
        from datetime import datetime
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("Date must be in ISO format (YYYY-MM-DDTHH:MM:SS)")
        return v


class IdParams(BaseApiModel):
    """ID parameters for endpoints that operate on a single resource."""
    
    id: str = Field(..., description="Resource ID")


class BulkIdParams(BaseApiModel):
    """ID parameters for endpoints that operate on multiple resources."""
    
    ids: List[str] = Field(..., min_items=1, description="Resource IDs")


class MetadataParams(BaseApiModel):
    """Metadata parameters for endpoints that accept metadata."""
    
    metadata: Dict[str, Any] = Field(..., description="Metadata")


# Base request models for common operations

class CreateRequestBase(BaseApiModel):
    """Base model for create requests."""
    pass


class UpdateRequestBase(BaseApiModel):
    """Base model for update requests."""
    pass


class DeleteRequestBase(BaseApiModel):
    """Base model for delete requests."""
    id: str = Field(..., description="Resource ID to delete")


class BulkDeleteRequestBase(BaseApiModel):
    """Base model for bulk delete requests."""
    ids: List[str] = Field(..., min_items=1, description="Resource IDs to delete")
