"""
Project model for the web dashboard application.

This module defines the Project model for project management.
"""

from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from shared.models.src.project import (
    Project as SharedProjectModel,
    ProjectStatus,
    ProjectSummary,
    ProjectWithStats
)

from app.models.base import BaseModel

class Project(BaseModel):
    """
    Project model for project management.
    
    Attributes:
        id: The project's unique identifier (UUID)
        name: The project's name
        description: The project's description
        status: The project's status (DRAFT, PLANNING, IN_PROGRESS, PAUSED, COMPLETED, ARCHIVED)
        project_metadata: Additional project metadata (renamed from 'metadata' to avoid SQLAlchemy conflicts)
        owner_id: The ID of the user who owns the project
    """
    __tablename__ = 'project'  # Singular table name per SQLAlchemy guide
    
    # Override id from BaseModel to add docstring
    id = Column(BaseModel.id.type, primary_key=True, default=BaseModel.id.default.arg)
    
    # Project attributes
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    status = Column(String(20), nullable=False, default='DRAFT', index=True)
    project_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' which is reserved in SQLAlchemy
    
    # Relationships
    owner_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=True, index=True)
    owner = relationship("User", back_populates="projects")
    
    # Agent relationship
    agents = relationship("Agent", back_populates="project", cascade="all, delete-orphan")
    
    # Task relationship
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    
    def __init__(self, name, description=None, status='DRAFT', metadata=None, owner_id=None):
        """
        Initialize a new Project.
        
        Args:
            name: The project's name
            description: The project's description (optional)
            status: The project's status (default: 'DRAFT')
            metadata: Additional project metadata (optional, stored in project_metadata field)
            owner_id: The ID of the user who owns the project (optional)
        """
        self.name = name
        self.description = description
        self.status = status
        self.project_metadata = metadata or {}
        self.owner_id = owner_id
    
    def to_api_model(self) -> SharedProjectModel:
        """
        Convert to shared API model.
        
        Returns:
            A SharedProjectModel instance with this project's data
        """
        return SharedProjectModel(
            id=self.id,
            name=self.name,
            description=self.description,
            status=ProjectStatus(self.status),
            metadata=self.project_metadata,  # Map to 'metadata' in API for backward compatibility
            owner_id=self.owner_id,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    def to_summary(self) -> ProjectSummary:
        """
        Convert to project summary model.
        
        Returns:
            A ProjectSummary instance with this project's data
        """
        return ProjectSummary(
            id=self.id,
            name=self.name,
            status=ProjectStatus(self.status),
            created_at=self.created_at
        )
    
    def to_stats_model(self) -> ProjectWithStats:
        """
        Convert to project with stats model.
        
        Returns:
            A ProjectWithStats instance with this project's data and statistics
        """
        # Calculate statistics using the Agent and Task models
        agent_count = len(self.agents)
        task_count = len(self.tasks)
        completed_task_count = sum(1 for task in self.tasks if task.status == 'COMPLETED')
        
        # Calculate progress percentage
        progress_percentage = 0.0
        if task_count > 0:
            progress_percentage = (completed_task_count / task_count) * 100.0
        
        return ProjectWithStats(
            id=self.id,
            name=self.name,
            description=self.description,
            status=ProjectStatus(self.status),
            metadata=self.project_metadata,  # Map to 'metadata' in API for backward compatibility
            owner_id=self.owner_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            agent_count=agent_count,
            task_count=task_count,
            completed_task_count=completed_task_count,
            progress_percentage=progress_percentage
        )
    
    @classmethod
    def from_api_model(cls, api_model: SharedProjectModel) -> 'Project':
        """
        Create from shared API model.
        
        Args:
            api_model: The SharedProjectModel to convert
            
        Returns:
            A new Project instance
        """
        return cls(
            name=api_model.name,
            description=api_model.description,
            status=api_model.status.value if api_model.status else 'DRAFT',
            metadata=api_model.metadata,
            owner_id=api_model.owner_id
        )
    
    def __repr__(self):
        """
        Get a string representation of the Project.
        
        Returns:
            A string representation of the Project
        """
        return f'<Project {self.name} ({self.status})>'
