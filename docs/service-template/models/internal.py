from sqlalchemy import Column, String, ForeignKey, JSON, DateTime, Enum, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from typing import List, Optional, Dict, Any

from shared.utils.src.database import Base
from .api import ResourceStatus, ResourceType


class ResourceModel(Base):
    """
    SQLAlchemy model for resources.
    """
    __tablename__ = "resources"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    type = Column(Enum(ResourceType), nullable=False)
    status = Column(Enum(ResourceStatus), nullable=False, default=ResourceStatus.DRAFT)
    
    # Ownership
    owner_id = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Additional data
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    # Example of a one-to-many relationship
    # child_resources = relationship("ChildResourceModel", back_populates="parent", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Resource(id={self.id}, name='{self.name}', type='{self.type}', status='{self.status}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "type": self.type.value if self.type else None,
            "status": self.status.value if self.status else None,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata or {},
        }


# Example of a many-to-many relationship with an association table
"""
resource_tag_association = Table(
    'resource_tags',
    Base.metadata,
    Column('resource_id', UUID(as_uuid=True), ForeignKey('resources.id'), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id'), primary_key=True),
)


class TagModel(Base):
    __tablename__ = "tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True)
    
    # Relationships
    resources = relationship("ResourceModel", secondary=resource_tag_association, back_populates="tags")
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"
"""


# Example of a child model with a foreign key relationship
"""
class ChildResourceModel(Base):
    __tablename__ = "child_resources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    parent = relationship("ResourceModel", back_populates="child_resources")
    
    def __repr__(self):
        return f"<ChildResource(id={self.id}, name='{self.name}', parent_id='{self.parent_id}')>"
"""
