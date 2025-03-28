from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import BaseModel


class ProjectModel(BaseModel):
    """
    SQLAlchemy model for projects.
    """
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    status = Column(String(20), nullable=False, default="DRAFT")
    
    # Relationships
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    owner = relationship("UserModel", back_populates="projects")
    
    # Relationships with other models
    agents = relationship("AgentModel", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("TaskModel", back_populates="project", cascade="all, delete-orphan")
    
    # Additional data
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"
