"""
Project API converter implementation.

This module provides an implementation of the ApiConverter interface
for the Project entity, converting between internal Pydantic models and
API models.
"""

from typing import Dict, Any, Optional, List, Type
from uuid import UUID

from shared.models.src.project import Project as ProjectPydantic
from shared.models.src.api.project import (
    ProjectResponse, 
    ProjectCreate, 
    ProjectUpdate, 
    ProjectSummary
)
from shared.utils.src.conversion.base.interfaces import ApiConverter
from shared.utils.src.conversion.base.utils import convert_enum_values
from shared.utils.src.conversion.exceptions import ConversionError, ValidationError

class ProjectApiConverter(ApiConverter[ProjectPydantic, ProjectResponse]):
    """
    Converter for Project entities between internal Pydantic models and API models.
    
    This class provides methods for converting between internal Pydantic models
    and API models for the Project entity.
    """
    
    def to_api(self, internal_model: ProjectPydantic) -> ProjectResponse:
        """
        Convert internal model to API model.
        
        Args:
            internal_model: The internal model instance to convert
            
        Returns:
            The converted API model instance
            
        Raises:
            ConversionError: If the conversion fails
        """
        try:
            # Create API model with consistent field mapping
            return ProjectResponse(
                id=internal_model.id,
                name=internal_model.name,
                description=internal_model.description,
                status=internal_model.status,
                owner_id=internal_model.owner_id,
                created_at=internal_model.created_at,
                updated_at=internal_model.updated_at,
                metadata=internal_model.metadata
            )
        except Exception as e:
            raise ConversionError(f"Error converting to API model: {str(e)}", internal_model)
    
    def from_api(self, api_model: ProjectResponse) -> ProjectPydantic:
        """
        Convert API model to internal model.
        
        Args:
            api_model: The API model instance to convert
            
        Returns:
            The converted internal model instance
            
        Raises:
            ConversionError: If the conversion fails
        """
        try:
            # Create internal model with consistent field mapping
            return ProjectPydantic(
                id=api_model.id,
                name=api_model.name,
                description=api_model.description,
                status=api_model.status,
                owner_id=api_model.owner_id,
                created_at=api_model.created_at,
                updated_at=api_model.updated_at,
                metadata=api_model.metadata
            )
        except Exception as e:
            raise ConversionError(f"Error converting to internal model: {str(e)}", api_model)
    
    def from_create_request(self, request: ProjectCreate) -> ProjectPydantic:
        """
        Convert create request to internal model.
        
        Args:
            request: The create request to convert
            
        Returns:
            The converted internal model instance
            
        Raises:
            ValidationError: If the data fails validation
        """
        try:
            # Create internal model from create request
            return ProjectPydantic(
                name=request.name,
                description=request.description,
                status=request.status,
                owner_id=request.owner_id,
                metadata=request.metadata
            )
        except Exception as e:
            raise ValidationError(f"Invalid project create data: {str(e)}", request, ProjectPydantic)
    
    def from_update_request(self, request: ProjectUpdate, existing: ProjectPydantic) -> ProjectPydantic:
        """
        Apply update request to existing internal model.
        
        Args:
            request: The update request to apply
            existing: The existing internal model to update
            
        Returns:
            The updated internal model instance
            
        Raises:
            ValidationError: If the data fails validation
        """
        try:
            # Get update data, excluding unset fields
            update_data = request.dict(exclude_unset=True)
            
            # Create a copy of the existing model with updated fields
            return existing.copy(update=update_data)
        except Exception as e:
            raise ValidationError(f"Invalid project update data: {str(e)}", request, ProjectPydantic)
    
    def to_summary(self, internal_model: ProjectPydantic) -> ProjectSummary:
        """
        Convert internal model to summary model.
        
        Args:
            internal_model: The internal model instance to convert
            
        Returns:
            The converted summary model instance
            
        Raises:
            ConversionError: If the conversion fails
        """
        try:
            # Create summary model with subset of fields
            return ProjectSummary(
                id=internal_model.id,
                name=internal_model.name,
                status=internal_model.status,
                owner_id=internal_model.owner_id
            )
        except Exception as e:
            raise ConversionError(f"Error converting to summary model: {str(e)}", internal_model)
    
    def batch_to_summary(self, internal_models: List[ProjectPydantic]) -> List[ProjectSummary]:
        """
        Convert a list of internal models to summary models.
        
        Args:
            internal_models: The internal model instances to convert
            
        Returns:
            List of converted summary model instances
        """
        return [self.to_summary(model) for model in internal_models]
