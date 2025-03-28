"""
Example usage of the standardized conversion layer.

This module demonstrates how to use the standardized conversion layer to convert
between different model representations, such as SQLAlchemy ORM models and
Pydantic models.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from shared.models.src.project import Project as ProjectPydantic
from shared.models.src.api.project import ProjectResponse, ProjectCreate, ProjectUpdate, ProjectSummary
from shared.models.src.enums import ProjectStatus
from shared.utils.src.conversion import (
    ProjectEntityConverter,
    ProjectApiConverter,
    convert_to_pydantic,
    convert_to_orm,
    model_registry
)

# Create a base class for SQLAlchemy models
Base = declarative_base()

# Define a SQLAlchemy model for Project
class ProjectDB(Base):
    """SQLAlchemy model for projects."""
    __tablename__ = "project"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default=ProjectStatus.DRAFT.value)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    project_metadata = Column(JSON, nullable=True)


def example_entity_converter():
    """Example usage of the ProjectEntityConverter."""
    print("\n=== Entity Converter Example ===\n")
    
    # Create a ProjectDB instance
    project_db = ProjectDB(
        id=uuid.uuid4(),
        name="Test Project",
        description="A test project for the conversion layer",
        status=ProjectStatus.DRAFT.value,
        owner_id=uuid.uuid4(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        project_metadata={"key": "value"}
    )
    
    # Create a ProjectEntityConverter
    converter = ProjectEntityConverter(ProjectDB)
    
    # Convert from ORM model to Pydantic model
    project_pydantic = converter.to_pydantic(project_db)
    print(f"Converted to Pydantic model: {project_pydantic}")
    print(f"Status is enum: {isinstance(project_pydantic.status, ProjectStatus)}")
    
    # Convert from Pydantic model to ORM model
    new_project_db = converter.to_orm(project_pydantic)
    print(f"Converted to ORM model: {new_project_db.__dict__}")
    
    # Convert to external representation
    external_data = converter.to_external(project_db)
    print(f"External representation: {external_data}")
    
    # Create from external representation
    new_project_pydantic = converter.from_external(external_data)
    print(f"Created from external representation: {new_project_pydantic}")
    
    # Update an existing ORM model
    updated_project_pydantic = ProjectPydantic(
        id=project_db.id,
        name="Updated Project Name",
        description="Updated project description",
        status=ProjectStatus.IN_PROGRESS,
        owner_id=project_db.owner_id,
        created_at=project_db.created_at,
        updated_at=datetime.utcnow(),
        metadata={"key": "updated_value"}
    )
    updated_project_db = converter.update_orm(updated_project_pydantic, project_db)
    print(f"Updated ORM model: {updated_project_db.__dict__}")


def example_api_converter():
    """Example usage of the ProjectApiConverter."""
    print("\n=== API Converter Example ===\n")
    
    # Create a ProjectPydantic instance
    project_pydantic = ProjectPydantic(
        id=uuid.uuid4(),
        name="Test Project",
        description="A test project for the conversion layer",
        status=ProjectStatus.DRAFT,
        owner_id=uuid.uuid4(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        metadata={"key": "value"}
    )
    
    # Create a ProjectApiConverter
    converter = ProjectApiConverter()
    
    # Convert from internal model to API model
    project_response = converter.to_api(project_pydantic)
    print(f"Converted to API model: {project_response}")
    
    # Convert from API model to internal model
    new_project_pydantic = converter.from_api(project_response)
    print(f"Converted to internal model: {new_project_pydantic}")
    
    # Convert from create request
    create_request = ProjectCreate(
        name="New Project",
        description="A new project from a create request",
        status=ProjectStatus.PLANNING,
        owner_id=uuid.uuid4(),
        metadata={"key": "new_value"}
    )
    new_project = converter.from_create_request(create_request)
    print(f"Created from create request: {new_project}")
    
    # Apply update request
    update_request = ProjectUpdate(
        name="Updated Project Name",
        description="Updated project description",
        status=ProjectStatus.IN_PROGRESS
    )
    updated_project = converter.from_update_request(update_request, project_pydantic)
    print(f"Updated from update request: {updated_project}")
    
    # Convert to summary
    project_summary = converter.to_summary(project_pydantic)
    print(f"Converted to summary: {project_summary}")
    
    # Convert batch to summary
    projects = [project_pydantic, new_project, updated_project]
    summaries = converter.batch_to_summary(projects)
    print(f"Batch converted to summaries: {summaries}")


def example_utility_functions():
    """Example usage of the utility functions."""
    print("\n=== Utility Functions Example ===\n")
    
    # Create a ProjectDB instance
    project_db = ProjectDB(
        id=uuid.uuid4(),
        name="Test Project",
        description="A test project for the conversion layer",
        status=ProjectStatus.DRAFT.value,
        owner_id=uuid.uuid4(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        project_metadata={"key": "value"}
    )
    
    # Convert from ORM model to Pydantic model using utility function
    project_pydantic = convert_to_pydantic(project_db, ProjectPydantic)
    print(f"Converted to Pydantic model: {project_pydantic}")
    
    # Convert from Pydantic model to ORM model using utility function
    new_project_db = convert_to_orm(project_pydantic, ProjectDB)
    print(f"Converted to ORM model: {new_project_db.__dict__}")


def example_model_registry():
    """Example usage of the model registry."""
    print("\n=== Model Registry Example ===\n")
    
    # Register converters in the model registry
    project_entity_converter = ProjectEntityConverter(ProjectDB)
    project_api_converter = ProjectApiConverter()
    
    model_registry.register_entity_converter("project", project_entity_converter)
    model_registry.register_api_converter("project", project_api_converter)
    
    # Get converters from the model registry
    entity_converter = model_registry.get_entity_converter("project")
    api_converter = model_registry.get_api_converter("project")
    
    # Create a ProjectDB instance
    project_db = ProjectDB(
        id=uuid.uuid4(),
        name="Test Project",
        description="A test project for the conversion layer",
        status=ProjectStatus.DRAFT.value,
        owner_id=uuid.uuid4(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        project_metadata={"key": "value"}
    )
    
    # Use the entity converter from the registry
    project_pydantic = entity_converter.to_pydantic(project_db)
    print(f"Converted to Pydantic model using registry: {project_pydantic}")
    
    # Use the API converter from the registry
    project_response = api_converter.to_api(project_pydantic)
    print(f"Converted to API model using registry: {project_response}")


def main():
    """Run all examples."""
    example_entity_converter()
    example_api_converter()
    example_utility_functions()
    example_model_registry()


if __name__ == "__main__":
    main()
