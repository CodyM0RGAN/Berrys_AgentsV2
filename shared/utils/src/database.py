"""
Database utilities for the Berrys_AgentsV2 project.

This module provides common database utilities used across services, including:
- UUID type for SQLAlchemy models
- Common column definitions
- Database connection utilities
"""

import uuid
from typing import Any, Optional, TypeVar, cast

from sqlalchemy import TypeDecorator, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.engine.interfaces import Dialect

T = TypeVar('T')


class UUID(TypeDecorator):
    """
    Platform-independent UUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses String(36).
    
    This implementation is based on the SQLAlchemy documentation and has been
    enhanced with better error handling and cross-database compatibility.
    """

    impl = String
    cache_ok = True

    def __init__(self, as_uuid: bool = False):
        """
        Initialize the UUID type.

        Args:
            as_uuid: If True, return Python UUID objects, otherwise return strings.
        """
        self.as_uuid = as_uuid
        super().__init__(36)

    def load_dialect_impl(self, dialect: Dialect) -> Any:
        """
        Load the dialect-specific implementation of this type.

        Args:
            dialect: The SQLAlchemy dialect.

        Returns:
            The dialect-specific implementation.
        """
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID(as_uuid=self.as_uuid))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[str]:
        """
        Process the value before binding it to a statement.

        Args:
            value: The value to process.
            dialect: The SQLAlchemy dialect.

        Returns:
            The processed value.
        """
        if value is None:
            return None
        
        if dialect.name == 'postgresql' and not self.as_uuid:
            # PostgreSQL can handle UUID objects directly
            return str(value)
        
        if not isinstance(value, uuid.UUID):
            try:
                value = uuid.UUID(value)
            except (TypeError, ValueError, AttributeError):
                raise ValueError(f"Invalid UUID: {value}")
        
        if self.as_uuid:
            return value
        
        return str(value)

    def process_result_value(self, value: Any, dialect: Dialect) -> Optional[Any]:
        """
        Process the value after retrieving it from the database.

        Args:
            value: The value to process.
            dialect: The SQLAlchemy dialect.

        Returns:
            The processed value.
        """
        if value is None:
            return None
        
        if self.as_uuid:
            if isinstance(value, uuid.UUID):
                return value
            try:
                return uuid.UUID(value)
            except (TypeError, ValueError, AttributeError):
                raise ValueError(f"Invalid UUID: {value}")
        
        if isinstance(value, uuid.UUID):
            return str(value)
        
        return value


def generate_uuid() -> str:
    """
    Generate a new UUID string.

    Returns:
        A new UUID string.
    """
    return str(uuid.uuid4())


# Common column definitions
def uuid_column(nullable: bool = False, primary_key: bool = False) -> UUID:
    """
    Create a UUID column.

    Args:
        nullable: Whether the column can be NULL.
        primary_key: Whether the column is a primary key.

    Returns:
        A UUID column.
    """
    return UUID(as_uuid=False)


def timestamp_columns() -> dict:
    """
    Create created_at and updated_at column definitions.

    Returns:
        A dictionary with created_at and updated_at column definitions.
    """
    from sqlalchemy import Column, DateTime, func
    
    return {
        'created_at': Column(DateTime, nullable=False, default=func.now()),
        'updated_at': Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    }


def metadata_column(nullable: bool = True) -> String:
    """
    Create a metadata column.

    Args:
        nullable: Whether the column can be NULL.

    Returns:
        A metadata column.
    """
    return String(1024, nullable=nullable)
