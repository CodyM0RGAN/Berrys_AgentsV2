"""
Project entity converter implementation.

This module provides an implementation of the EntityConverter interface
for the Project entity, converting between SQLAlchemy ORM models and
Pydantic models.
"""

from typing import Dict, Any, Optional, List, Type
from uuid import UUID

from shared.models.src.project import Project as ProjectPydantic
from shared.utils.src.conversion.base.interfaces import EntityConverter
from shared.utils.src.conversion.base.utils import convert_enum_values
from shared.utils.src.conversion.exceptions import ConversionError, ValidationError, TypeConversionError

class ProjectEntityConverter(EntityConverter[ProjectPydantic]):
    """
    Converter for Project entities between ORM and Pydantic models.
    
    This class provides methods for converting between SQLAlchemy ORM models
    and Pydantic models for the Project entity.
    """
    
    def __init__(self, orm_model_cls: Type):
        """
        Initialize the converter.
        
        Args:
            orm_model_cls: The SQLAlchemy ORM model class
        """
        self.orm_model_cls = orm_model_cls
    
    def to_pydantic(self, orm_model: Any) -> ProjectPydantic:
        """
        Convert ORM model to Pydantic model.
        
        Args:
            orm_model: The SQLAlchemy ORM model instance to convert
            
        Returns:
            The converted Pydantic model instance
            
        Raises:
            ConversionError: If the conversion fails
        """
        if not isinstance(orm_model, self.orm_model_cls):
            raise ConversionError(
                f"Expected {self.orm_model_cls.__name__}, got {type(orm_model).__name__}",
                orm_model
            )
        
        try:
            # Extract metadata with correct key mapping
            metadata = getattr(orm_model, "project_metadata", {}) or {}
            
            # Create Pydantic model with consistent field mapping
            return ProjectPydantic(
                id=orm_model.id,
                name=orm_model.name,
                description=getattr(orm_model, "description", None),
                status=orm_model.status,
                owner_id=getattr(orm_model, "owner_id", None),
                created_at=orm_model.created_at,
                updated_at=orm_model.updated_at,
                metadata=metadata
            )
        except Exception as e:
            raise ConversionError(f"Error converting to Pydantic model: {str(e)}", orm_model)
    
    def to_orm(self, pydantic_model: ProjectPydantic) -> Any:
        """
        Convert Pydantic model to ORM model.
        
        Args:
            pydantic_model: The Pydantic model instance to convert
            
        Returns:
            The converted SQLAlchemy ORM model instance
            
        Raises:
            ConversionError: If the conversion fails
        """
        try:
            # Handle metadata field mapping
            project_metadata = pydantic_model.metadata if hasattr(pydantic_model, "metadata") else {}
            
            # Convert enum values to strings
            status = pydantic_model.status.value if hasattr(pydantic_model.status, "value") else pydantic_model.status
            
            # Create ORM model
            return self.orm_model_cls(
                id=pydantic_model.id,
                name=pydantic_model.name,
                description=pydantic_model.description,
                status=status,
                owner_id=pydantic_model.owner_id,
                created_at=pydantic_model.created_at,
                updated_at=pydantic_model.updated_at,
                project_metadata=project_metadata
            )
        except Exception as e:
            raise ConversionError(f"Error converting to ORM model: {str(e)}", pydantic_model)
    
    def to_external(self, orm_model: Any) -> Dict[str, Any]:
        """
        Convert ORM model to external dictionary representation.
        
        Args:
            orm_model: The SQLAlchemy ORM model instance to convert
            
        Returns:
            Dictionary representation of the ORM model
            
        Raises:
            ConversionError: If the conversion fails
        """
        try:
            # Convert to Pydantic model first
            pydantic_model = self.to_pydantic(orm_model)
            
            # Convert Pydantic model to dictionary
            return pydantic_model.dict()
        except Exception as e:
            raise ConversionError(f"Error converting to external representation: {str(e)}", orm_model)
    
    def from_external(self, data: Dict[str, Any]) -> ProjectPydantic:
        """
        Create Pydantic model from external dictionary representation.
        
        Args:
            data: Dictionary representation of the model
            
        Returns:
            The created Pydantic model instance
            
        Raises:
            ValidationError: If the data fails validation
        """
        try:
            # Convert enum values
            data = convert_enum_values(data, ProjectPydantic)
            
            # Create Pydantic model
            return ProjectPydantic(**data)
        except Exception as e:
            raise ValidationError(f"Invalid project data: {str(e)}", data, ProjectPydantic)
    
    def update_orm(self, pydantic_model: ProjectPydantic, orm_model: Any) -> Any:
        """
        Update an existing ORM model with values from a Pydantic model.
        
        Args:
            pydantic_model: The Pydantic model instance to get values from
            orm_model: The SQLAlchemy ORM model instance to update
            
        Returns:
            The updated SQLAlchemy ORM model instance
            
        Raises:
            ConversionError: If the update fails
        """
        try:
            # Update fields
            orm_model.name = pydantic_model.name
            orm_model.description = pydantic_model.description
            
            # Convert enum values to strings
            orm_model.status = pydantic_model.status.value if hasattr(pydantic_model.status, "value") else pydantic_model.status
            
            # Update owner_id if it exists
            if hasattr(orm_model, "owner_id") and hasattr(pydantic_model, "owner_id"):
                orm_model.owner_id = pydantic_model.owner_id
            
            # Update metadata
            if hasattr(orm_model, "project_metadata") and hasattr(pydantic_model, "metadata"):
                orm_model.project_metadata = pydantic_model.metadata
            
            return orm_model
        except Exception as e:
            raise ConversionError(f"Error updating ORM model: {str(e)}", pydantic_model)
