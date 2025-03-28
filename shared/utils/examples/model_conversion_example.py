"""
Example usage of the ModelConverter class.

This module demonstrates how to use the ModelConverter class to convert between
SQLAlchemy ORM models and API models, with special handling for enum values.
"""

from datetime import datetime
import uuid
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates

from shared.utils.src.model_conversion import ModelConverter
from shared.utils.src.enum_validation import EnumColumnMixin, enum_column, add_enum_validation
from shared.models.src.enums import ProjectStatus, UserStatus, UserRole

# Create a base class for SQLAlchemy models
Base = declarative_base()

# Define a SQLAlchemy model
class UserDB(Base, EnumColumnMixin):
    """SQLAlchemy model for users."""
    __tablename__ = "user"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, default=True)
    status = Column(String(20), nullable=False, default=UserStatus.ACTIVE.value)
    role = Column(String(20), nullable=False, default=UserRole.VIEWER.value)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_metadata = Column(JSON, nullable=True)
    
    # Define enum columns for validation
    __enum_columns__ = {
        'status': UserStatus,
        'role': UserRole
    }
    
    # Relationships
    projects = relationship("ProjectDB", back_populates="owner")


class ProjectDB(Base):
    """SQLAlchemy model for projects."""
    __tablename__ = "project"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # Using enum_column helper function
    status = enum_column(ProjectStatus, nullable=False, default=ProjectStatus.DRAFT.value)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    project_metadata = Column(JSON, nullable=True)
    
    # Relationships
    owner = relationship("UserDB", back_populates="projects")


# Define Pydantic models for API
class UserBase(BaseModel):
    """Base Pydantic model for users."""
    username: str
    email: str
    is_active: bool = True
    status: UserStatus = UserStatus.ACTIVE
    role: UserRole = UserRole.VIEWER
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        orm_mode = True


class UserCreate(UserBase):
    """Pydantic model for creating users."""
    password: str


class UserResponse(UserBase):
    """Pydantic model for user responses."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ProjectBase(BaseModel):
    """Base Pydantic model for projects."""
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.DRAFT
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        orm_mode = True


class ProjectCreate(ProjectBase):
    """Pydantic model for creating projects."""
    owner_id: uuid.UUID


class ProjectResponse(ProjectBase):
    """Pydantic model for project responses."""
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# Example usage
def example_usage():
    """Example usage of the ModelConverter class."""
    # Create a user database model
    user_db = UserDB(
        id=uuid.uuid4(),
        username="johndoe",
        email="john.doe@example.com",
        is_active=True,
        status=UserStatus.ACTIVE.value,  # String value for SQLAlchemy
        role=UserRole.ADMIN.value,       # String value for SQLAlchemy
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        user_metadata={"preferences": {"theme": "dark", "language": "en"}}
    )
    
    # Convert from database model to API model
    user_api = ModelConverter.to_api_model(user_db, UserResponse)
    print(f"User API model: {user_api}")
    print(f"User status is enum: {isinstance(user_api.status, UserStatus)}")  # Should be True
    print(f"User role is enum: {isinstance(user_api.role, UserRole)}")        # Should be True
    
    # Create a project API model
    project_api = ProjectCreate(
        name="My Project",
        description="A sample project",
        status=ProjectStatus.PLANNING,  # Enum instance for Pydantic
        metadata={"tags": ["sample", "example"]},
        owner_id=user_db.id
    )
    
    # Convert from API model to database model
    project_db = ModelConverter.to_db_model(project_api, ProjectDB)
    print(f"Project DB model: {project_db.__dict__}")
    print(f"Project status is string: {isinstance(project_db.status, str)}")  # Should be True
    
    # Update a database model with values from an API model
    updated_project_api = ProjectBase(
        name="Updated Project Name",
        description="Updated project description",
        status=ProjectStatus.IN_PROGRESS,  # Enum instance for Pydantic
        metadata={"tags": ["updated", "example"]}
    )
    ModelConverter.update_db_model(updated_project_api, project_db, exclude=["owner_id"])
    print(f"Updated Project DB model: {project_db.__dict__}")
    print(f"Updated project status is string: {isinstance(project_db.status, str)}")  # Should be True
    print(f"Updated project status value: {project_db.status}")  # Should be "in_progress"
    
    # Demonstrate validation
    try:
        # This should raise a ValueError because "invalid_status" is not a valid ProjectStatus
        invalid_project = ProjectDB(
            name="Invalid Project",
            status="invalid_status"
        )
        print("Validation failed: invalid status was accepted")
    except ValueError as e:
        print(f"Validation succeeded: {e}")


if __name__ == "__main__":
    example_usage()
