"""
Enum validation utilities for SQLAlchemy models.

This module provides utilities for validating enum values in SQLAlchemy string columns,
ensuring that only valid enum values are stored in the database while maintaining
the flexibility of string columns.
"""

from enum import Enum
from typing import Type, Any, List, Dict, Optional, Union, Set, Callable
from sqlalchemy import event, Column, String
from sqlalchemy.orm import declarative_base, DeclarativeMeta, validates

# Type aliases for clarity
EnumType = Type[Enum]
ValidationFunction = Callable[[Any, str, Any], Any]


class EnumValidator:
    """
    Utility class for validating enum values in SQLAlchemy string columns.
    """
    
    @staticmethod
    def validate_enum(enum_class: EnumType, value: Any) -> str:
        """
        Validate that a value is a valid enum value.
        
        Args:
            enum_class: The Enum class to validate against
            value: The value to validate
            
        Returns:
            The string representation of the enum value
            
        Raises:
            ValueError: If the value is not a valid enum value
        """
        # If value is already an enum instance, convert to string
        if isinstance(value, enum_class):
            return value.value
            
        # If value is a string, check if it's a valid enum value
        if isinstance(value, str):
            # If lowercase is provided, convert to uppercase but add a warning
            if value != value.upper() and any(value.upper() == e.value.upper() for e in enum_class):
                import warnings
                warnings.warn(
                    f"Lowercase enum value '{value}' provided. Please use uppercase values "
                    f"('{value.upper()}') for consistency. Support for lowercase values "
                    f"will be removed in a future version.",
                    DeprecationWarning, stacklevel=2
                )
                value = value.upper()
                
            # Check if the string matches any enum value
            for enum_item in enum_class:
                if value == enum_item.value:
                    return value
                    
            # Check if the string matches any enum name (case insensitive)
            for enum_item in enum_class:
                if value.upper() == enum_item.name:  # Removed .upper() from enum_item.name since names should be uppercase
                    return enum_item.value
                    
        # If value is not a string or enum instance, try to convert it
        try:
            # Try to get the enum by name
            enum_item = enum_class[str(value).upper()]
            return enum_item.value
        except (KeyError, ValueError):
            pass
            
        # If we get here, the value is not valid
        valid_values = [f"{e.name} ({e.value})" for e in enum_class]
        raise ValueError(
            f"Invalid value '{value}' for enum {enum_class.__name__}. "
            f"Valid values are: {', '.join(valid_values)}"
        )


class EnumColumnMixin:
    """
    Mixin class for adding enum validation to SQLAlchemy models.
    
    Usage:
        class MyModel(Base, EnumColumnMixin):
            __tablename__ = 'my_model'
            
            id = Column(Integer, primary_key=True)
            status = Column(String, nullable=False)
            
            __enum_columns__ = {
                'status': MyStatusEnum
            }
    """
    
    # Dictionary mapping column names to enum classes
    __enum_columns__: Dict[str, EnumType] = {}
    
    @classmethod
    def __declare_last__(cls):
        """
        SQLAlchemy hook that runs after the model is fully declared.
        Used to set up validators for enum columns.
        """
        for column_name, enum_class in cls.__enum_columns__.items():
            # Set up validator for the column
            validates_method_name = f'validate_{column_name}'
            
            # Define the validator method
            def make_validator(enum_cls):
                def validator(self, key, value):
                    return EnumValidator.validate_enum(enum_cls, value)
                return validator
                
            # Add the validator method to the class
            setattr(cls, validates_method_name, validates(column_name)(make_validator(enum_class)))


def enum_column(enum_class: EnumType, **kwargs) -> Column:
    """
    Create a string column with enum validation.
    
    Args:
        enum_class: The Enum class to validate against
        **kwargs: Additional arguments to pass to Column constructor
        
    Returns:
        A Column object with enum validation
        
    Usage:
        class MyModel(Base):
            __tablename__ = 'my_model'
            
            id = Column(Integer, primary_key=True)
            status = enum_column(MyStatusEnum, nullable=False)
    """
    # Get the maximum length of enum values
    max_length = max(len(str(e.value)) for e in enum_class)
    
    # Create the column with appropriate length
    column = Column(String(max_length), **kwargs)
    
    # Add validator
    @validates(column.name)
    def validate_enum_column(self, key, value):
        return EnumValidator.validate_enum(enum_class, value)
        
    return column


def add_enum_validation(cls: Type, column_name: str, enum_class: EnumType, is_integer: bool = False) -> None:
    """
    Add enum validation to an existing model class for a specific column.
    
    Args:
        cls: The model class to add validation to
        column_name: The name of the column to validate
        enum_class: The Enum class to validate against
        is_integer: Whether the column is an integer column (default: False)
        
    Usage:
        class MyModel(Base):
            __tablename__ = 'my_model'
            
            id = Column(Integer, primary_key=True)
            status = Column(String, nullable=False)
            
        add_enum_validation(MyModel, 'status', MyStatusEnum)
    """
    # Add validator
    if is_integer:
        @validates(column_name)
        def validate_enum_column(self, key, value):
            # For integer columns, validate that the value is in the range of enum values
            if isinstance(value, int):
                if value < 0 or value >= len(enum_class):
                    valid_values = [f"{i}: {e.name} ({e.value})" for i, e in enumerate(enum_class)]
                    raise ValueError(
                        f"Invalid value '{value}' for enum {enum_class.__name__}. "
                        f"Valid values are: {', '.join(valid_values)}"
                    )
                return value
            else:
                # If the value is not an integer, try to convert it to an integer
                try:
                    # If it's an enum instance, get its index
                    if isinstance(value, enum_class):
                        return list(enum_class).index(value)
                    # If it's a string, try to match it to an enum name or value
                    elif isinstance(value, str):
                        for i, e in enumerate(enum_class):
                            if value.upper() == e.name.upper() or value == e.value:
                                return i
                    # If we get here, the value is not valid
                    valid_values = [f"{i}: {e.name} ({e.value})" for i, e in enumerate(enum_class)]
                    raise ValueError(
                        f"Invalid value '{value}' for enum {enum_class.__name__}. "
                        f"Valid values are: {', '.join(valid_values)}"
                    )
                except (ValueError, TypeError):
                    valid_values = [f"{i}: {e.name} ({e.value})" for i, e in enumerate(enum_class)]
                    raise ValueError(
                        f"Invalid value '{value}' for enum {enum_class.__name__}. "
                        f"Valid values are: {', '.join(valid_values)}"
                    )
    else:
        @validates(column_name)
        def validate_enum_column(self, key, value):
            return EnumValidator.validate_enum(enum_class, value)
        
    # Add the validator to the class
    setattr(cls, f'validate_{column_name}', validate_enum_column)


# Example usage:
"""
from enum import Enum
from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Define an enum
class StatusEnum(Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

# Create a base class
Base = declarative_base()

# Method 1: Using EnumColumnMixin
class Project(Base, EnumColumnMixin):
    __tablename__ = 'project'
    
    id = Column(Integer, primary_key=True)
    status = Column(String(10), nullable=False, default=StatusEnum.DRAFT.value)
    
    __enum_columns__ = {
        'status': StatusEnum
    }

# Method 2: Using enum_column function
class Task(Base):
    __tablename__ = 'task'
    
    id = Column(Integer, primary_key=True)
    status = enum_column(StatusEnum, nullable=False, default=StatusEnum.DRAFT.value)

# Method 3: Using add_enum_validation function
class Agent(Base):
    __tablename__ = 'agent'
    
    id = Column(Integer, primary_key=True)
    status = Column(String(10), nullable=False, default=StatusEnum.DRAFT.value)

add_enum_validation(Agent, 'status', StatusEnum)

# Create engine and session
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Create a project with valid status
project = Project(status=StatusEnum.ACTIVE)
session.add(project)
session.commit()

# This will raise a ValueError because "invalid" is not a valid status
try:
    project = Project(status="invalid")
    session.add(project)
    session.commit()
except ValueError as e:
    print(f"Validation error: {e}")

# This will work because "ACTIVE" matches the enum name (case insensitive)
project = Project(status="ACTIVE")
session.add(project)
session.commit()

# This will work because we're passing the enum directly
project = Project(status=StatusEnum.ARCHIVED)
session.add(project)
session.commit()
"""
