"""
Enhanced base models for the Berrys_AgentsV2 project.

This module provides improved base classes for SQLAlchemy and Pydantic models
with additional functionality, including:
- Timestamp mixins
- Soft delete functionality
- UUID primary key generation
- Enum validation
- Metadata handling
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Set, Type, TypeVar, get_type_hints

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field, field_validator
from sqlalchemy import Column, DateTime, String, func, schema as sqlalchemy_schema
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from shared.utils.src.database import UUID, generate_uuid

# Simple implementation of ModelRegistry to fix import issues
class ModelRegistry:
    """
    Registry for model mappings.
    
    This class provides a registry for mapping between SQLAlchemy and Pydantic models.
    """
    
    def __init__(self):
        """Initialize the model registry."""
        self._mappings = {}
    
    def register_entity_converter(self, entity_name, pydantic_model):
        """
        Register an entity converter.
        
        Args:
            entity_name: The name of the entity
            pydantic_model: The Pydantic model to register
        """
        self._mappings[entity_name] = pydantic_model

# Create a global instance
model_registry = ModelRegistry()

def register_models(sqlalchemy_model, pydantic_model, model_type):
    """
    Register a mapping between SQLAlchemy and Pydantic models.
    
    Args:
        sqlalchemy_model: The SQLAlchemy model class
        pydantic_model: The Pydantic model class
        model_type: The type of model (e.g., 'default', 'create', 'update')
    """
    model_registry.register_entity_converter(sqlalchemy_model.__tablename__, pydantic_model)

T = TypeVar('T')


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    
    # Class variables
    __abstract__ = True
    
    # Type annotations for SQLAlchemy 2.0
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=generate_uuid)
    
    def to_dict(self, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert the model to a dictionary.

        Args:
            exclude: A list of attribute names to exclude from the result.

        Returns:
            A dictionary representation of the model.
        """
        if exclude is None:
            exclude = []
        
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude:
                result[column.name] = getattr(self, column.name)
        
        return result


class TimestampMixin:
    """Mixin for adding created_at and updated_at columns to a model."""
    
    # Type annotations for SQLAlchemy 2.0
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )


class SoftDeleteMixin:
    """Mixin for adding soft delete functionality to a model."""
    
    # Type annotations for SQLAlchemy 2.0
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    @property
    def is_deleted(self) -> bool:
        """
        Check if the model is deleted.

        Returns:
            True if the model is deleted, False otherwise.
        """
        return self.deleted_at is not None
    
    def delete(self) -> None:
        """Mark the model as deleted."""
        self.deleted_at = datetime.now()
    
    def restore(self) -> None:
        """Restore the model."""
        self.deleted_at = None


class EnumColumnMixin:
    """Mixin for adding enum validation to a model."""
    
    # Class variable to store enum column mappings
    __enum_columns__: ClassVar[Dict[str, Type[Enum]]] = {}
    
    @classmethod
    def __declare_last__(cls) -> None:
        """
        Hook called after the model is fully declared.

        This method is used to set up enum validation for columns.
        """
        for column_name, enum_class in cls.__enum_columns__.items():
            # Add check constraint for enum values
            if hasattr(cls, '__table__'):
                valid_values = [e.value for e in enum_class]
                constraint_name = f"{cls.__tablename__}_{column_name}_check"
                
                # Check if the constraint already exists
                for constraint in cls.__table__.constraints:
                    if constraint.name == constraint_name:
                        break
                else:
                    # Add the constraint
                    column = getattr(cls.__table__.c, column_name)
                    check_clause = column.in_(valid_values)
                    cls.__table__.append_constraint(
                        sqlalchemy_schema.CheckConstraint(
                            check_clause,
                            name=constraint_name
                        )
                    )


class MetadataMixin:
    """Mixin for adding metadata column to a model."""
    
    @declared_attr
    def metadata(cls) -> Column:
        """
        Add a metadata column to the model.

        Returns:
            A SQLAlchemy Column for metadata.
        """
        # Use the table name as a prefix to avoid conflicts with SQLAlchemy's metadata
        return Column(f"{cls.__tablename__}_metadata", String(1024), nullable=True)


class StandardModel(Base, TimestampMixin, EnumColumnMixin):
    """Standard model with timestamps and enum validation."""
    
    __abstract__ = True


class SoftDeleteModel(StandardModel, SoftDeleteMixin):
    """Standard model with soft delete functionality."""
    
    __abstract__ = True


class MetadataModel(StandardModel, MetadataMixin):
    """Standard model with metadata column."""
    
    __abstract__ = True


class FullFeaturedModel(StandardModel, SoftDeleteMixin, MetadataMixin):
    """Model with all features: timestamps, soft delete, enum validation, and metadata."""
    
    __abstract__ = True


# Pydantic base models

class BaseModel(PydanticBaseModel):
    """Base model for all Pydantic models."""
    
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        json_schema_extra={
            "example": {}
        }
    )


class BaseEntityModel(BaseModel):
    """Base model for all entity models."""
    
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier"
    )


class BaseTimestampModel(BaseModel):
    """Base model with timestamps."""
    
    created_at: Optional[datetime] = Field(
        default=None,
        description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )


class BaseSoftDeleteModel(BaseModel):
    """Base model with soft delete functionality."""
    
    deleted_at: Optional[datetime] = Field(
        default=None,
        description="Deletion timestamp"
    )
    
    @property
    def is_deleted(self) -> bool:
        """
        Check if the model is deleted.

        Returns:
            True if the model is deleted, False otherwise.
        """
        return self.deleted_at is not None


class BaseMetadataModel(BaseModel):
    """Base model with metadata."""
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )


class StandardEntityModel(BaseEntityModel, BaseTimestampModel):
    """Standard entity model with timestamps."""
    pass


class SoftDeleteEntityModel(StandardEntityModel, BaseSoftDeleteModel):
    """Standard entity model with soft delete functionality."""
    pass


class MetadataEntityModel(StandardEntityModel, BaseMetadataModel):
    """Standard entity model with metadata."""
    pass


class FullFeaturedEntityModel(StandardEntityModel, BaseSoftDeleteModel, BaseMetadataModel):
    """Entity model with all features: timestamps, soft delete, and metadata."""
    pass


class APIModel(BaseModel):
    """Base model for API requests and responses."""
    
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        json_schema_extra={
            "example": {}
        }
    )


# Enum validation for Pydantic models

def enum_validator(enum_class: Type[Enum]):
    """
    Create a validator for enum values.

    Args:
        enum_class: The enum class to validate against.

    Returns:
        A validator function.
    """
    
    def validate(cls, value: Any) -> Any:
        """
        Validate that a value is a valid enum value.

        Args:
            cls: The model class.
            value: The value to validate.

        Returns:
            The validated enum value.

        Raises:
            ValueError: If the value is not a valid enum value.
        """
        if value is None:
            return None
        
        if isinstance(value, enum_class):
            return value
        
        if isinstance(value, str):
            # Case-insensitive matching
            for enum_item in enum_class:
                if value.upper() == enum_item.value.upper():
                    return enum_item
        
        # Try direct conversion
        try:
            return enum_class(value)
        except (ValueError, TypeError):
            valid_values = [e.value for e in enum_class]
            raise ValueError(
                f"Invalid value. Must be one of: {', '.join(valid_values)}"
            )
    
    return validate


def add_enum_validators(model_class: Type[BaseModel]) -> None:
    """
    Add enum validators to a Pydantic model.

    Args:
        model_class: The model class to add validators to.
    """
    type_hints = get_type_hints(model_class)
    
    for field_name, field_type in type_hints.items():
        # Check if field type is an enum
        if hasattr(field_type, '__origin__'):
            # Handle Optional[Enum]
            args = getattr(field_type, '__args__', [])
            for arg in args:
                if isinstance(arg, type) and issubclass(arg, Enum):
                    validator_name = f"validate_{field_name}"
                    setattr(
                        model_class,
                        validator_name,
                        field_validator(field_name)(enum_validator(arg))
                    )
                    break
        elif isinstance(field_type, type) and issubclass(field_type, Enum):
            # Handle direct Enum type
            validator_name = f"validate_{field_name}"
            setattr(
                model_class,
                validator_name,
                field_validator(field_name)(enum_validator(field_type))
            )


# Helper function to create enum column
def enum_column(enum_class: Type[Enum], nullable: bool = False, default: Optional[Any] = None) -> Column:
    """
    Create a string column with enum validation.

    Args:
        enum_class: The enum class to validate against.
        nullable: Whether the column can be NULL.
        default: The default value for the column.

    Returns:
        A SQLAlchemy Column with enum validation.
    """
    # Get the maximum length of enum values
    max_length = max(len(str(e.value)) for e in enum_class)
    
    # Add some padding for safety
    max_length = max(max_length + 5, 20)
    
    # Convert default to string if it's an enum
    if default is not None and isinstance(default, enum_class):
        default = default.value
    
    return Column(String(max_length), nullable=nullable, default=default)
