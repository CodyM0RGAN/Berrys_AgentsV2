"""
SQLAlchemy models for the Agent Template Engine.

This module contains the SQLAlchemy models for the Agent Template Engine functionality.
"""

from sqlalchemy import Column, String, ForeignKey, JSON, DateTime, Table, Text, Boolean, Integer, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import List, Optional, Dict, Any
import hashlib
import json

from shared.models.src.base import StandardModel, enum_column
from shared.models.src.enums import AgentType
from shared.utils.src.database import UUID, generate_uuid

from .template_engine import TemplateType


class AgentTemplateEngineModel(StandardModel):
    """
    SQLAlchemy model for agent templates in the Template Engine.
    """
    __tablename__ = "agent_template"
    
    # Basic information
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    template_type = enum_column(TemplateType, nullable=False)
    base_agent_type = enum_column(AgentType, nullable=False)
    template_content = Column(JSON, nullable=False, default={})
    category = Column(String(50), nullable=True)
    is_system_template = Column(Boolean, nullable=False, default=False)
    is_public = Column(Boolean, nullable=False, default=False)
    owner_id = Column(UUID, nullable=True)
    checksum = Column(String(64), nullable=True, index=True)
    
    # Relationships
    versions = relationship("AgentTemplateVersionModel", back_populates="template", cascade="all, delete-orphan")
    analytics = relationship("TemplateAnalyticsModel", back_populates="template", uselist=False, cascade="all, delete-orphan")
    tag_mappings = relationship("TemplateTagMappingModel", back_populates="template", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'base_agent_type', name='uq_template_name_agent_type'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f"<AgentTemplateEngine(id={self.id}, name='{self.name}', type='{self.template_type}')>"
    
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
            "template_type": self.template_type,
            "base_agent_type": self.base_agent_type,
            "template_content": self.template_content or {},
            "category": self.category,
            "is_system_template": self.is_system_template,
            "is_public": self.is_public,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "checksum": self.checksum,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def generate_checksum(self) -> str:
        """
        Generate a checksum for the template content.
        
        Returns:
            str: Checksum of the template content
        """
        content_str = json.dumps(self.template_content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def update_checksum(self) -> None:
        """
        Update the checksum based on the current template content.
        """
        self.checksum = self.generate_checksum()


class AgentTemplateVersionModel(StandardModel):
    """
    SQLAlchemy model for agent template versions.
    """
    __tablename__ = "agent_template_version"
    
    # Template association
    template_id = Column(UUID, ForeignKey("agent_template.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    template_content = Column(JSON, nullable=False, default={})
    changelog = Column(Text, nullable=True)
    created_by = Column(UUID, nullable=True)
    
    # Relationships
    template = relationship("AgentTemplateEngineModel", back_populates="versions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('template_id', 'version_number', name='uq_template_version'),
    )
    
    def __repr__(self):
        return f"<AgentTemplateVersion(template_id={self.template_id}, version={self.version_number})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            "id": str(self.id),
            "template_id": str(self.template_id),
            "version_number": self.version_number,
            "template_content": self.template_content or {},
            "changelog": self.changelog,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TemplateTagModel(StandardModel):
    """
    SQLAlchemy model for template tags.
    """
    __tablename__ = "template_tag"
    
    # Basic information
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    tag_mappings = relationship("TemplateTagMappingModel", back_populates="tag", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TemplateTag(id={self.id}, name='{self.name}')>"
    
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
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TemplateTagMappingModel(StandardModel):
    """
    SQLAlchemy model for template tag mappings.
    """
    __tablename__ = "template_tag_mapping"
    
    # Associations
    template_id = Column(UUID, ForeignKey("agent_template.id", ondelete="CASCADE"), nullable=False, index=True)
    tag_id = Column(UUID, ForeignKey("template_tag.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Relationships
    template = relationship("AgentTemplateEngineModel", back_populates="tag_mappings")
    tag = relationship("TemplateTagModel", back_populates="tag_mappings")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('template_id', 'tag_id', name='uq_template_tag'),
    )
    
    def __repr__(self):
        return f"<TemplateTagMapping(template_id={self.template_id}, tag_id={self.tag_id})>"


class TemplateAnalyticsModel(StandardModel):
    """
    SQLAlchemy model for template analytics.
    """
    __tablename__ = "template_analytics"
    
    # Template association
    template_id = Column(UUID, ForeignKey("agent_template.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    
    # Analytics data
    usage_count = Column(Integer, nullable=False, default=0)
    last_used = Column(DateTime(timezone=True), nullable=True)
    success_rate = Column(Float, nullable=True)
    
    # Relationships
    template = relationship("AgentTemplateEngineModel", back_populates="analytics")
    
    def __repr__(self):
        return f"<TemplateAnalytics(template_id={self.template_id}, usage_count={self.usage_count})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            "template_id": str(self.template_id),
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "success_rate": self.success_rate,
        }
