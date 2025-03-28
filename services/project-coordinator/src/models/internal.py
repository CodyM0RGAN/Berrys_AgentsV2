"""
Internal data models for Project Coordinator service.

These models define the SQLAlchemy ORM models used for database operations.
"""
from enum import Enum as PyEnum
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, 
    ForeignKey, Boolean, Text, JSON, Enum, LargeBinary, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from shared.models.src.project import ProjectStatus
from shared.models.src.base import Base, StandardModel, enum_column

# Use the Base class directly from shared.models.src.base


class Project(StandardModel):
    """SQLAlchemy model for projects."""
    __tablename__ = "project"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default=ProjectStatus.DRAFT.value)
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    project_metadata = Column(String(1024), nullable=True)
    
    # Relationships
    state_history = relationship("ProjectState", back_populates="project", cascade="all, delete-orphan")
    progress_records = relationship("ProjectProgress", back_populates="project", cascade="all, delete-orphan")
    resources = relationship("ProjectResource", back_populates="project", cascade="all, delete-orphan")
    artifacts = relationship("ProjectArtifact", back_populates="project", cascade="all, delete-orphan")


class ProjectState(StandardModel):
    """SQLAlchemy model for project state transitions."""
    __tablename__ = "project_state"
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False)
    state = Column(String(20), nullable=False)
    transitioned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reason = Column(Text, nullable=True)
    transitioned_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="state_history")


class ProjectProgress(StandardModel):
    """SQLAlchemy model for project progress records."""
    __tablename__ = "project_progress"
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False)
    percentage = Column(Float, nullable=False)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    metrics = Column(JSON, nullable=True)
    milestone = Column(String(255), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="progress_records")


class ProjectResource(StandardModel):
    """SQLAlchemy model for project resource allocations."""
    __tablename__ = "project_resource"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(255), nullable=False)
    allocation = Column(Float, nullable=False)  # 0.0 to 1.0 (0% to 100%)
    allocated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    released_at = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    resource_metadata = Column(String(1024), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="resources")


class ProjectArtifact(StandardModel):
    """SQLAlchemy model for project artifacts."""
    __tablename__ = "project_artifact"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    size_bytes = Column(Integer, nullable=False, default=0)
    storage_path = Column(String(1024), nullable=False)
    artifact_metadata = Column(String(1024), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="artifacts")


class ProjectAnalytics(StandardModel):
    """SQLAlchemy model for saved project analytics."""
    __tablename__ = "project_analytic"
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id"), nullable=False)
    analytics_type = Column(String(50), nullable=False)
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    data = Column(JSON, nullable=False)
    visualization_config = Column(JSON, nullable=True)
    is_cached = Column(Boolean, nullable=False, default=True)
    expiry = Column(DateTime, nullable=True)


class AgentRole(PyEnum):
    """Enum for agent roles."""
    COORDINATOR = "COORDINATOR"
    ASSISTANT = "ASSISTANT"
    RESEARCHER = "RESEARCHER"
    DEVELOPER = "DEVELOPER"
    TESTER = "TESTER"
    REVIEWER = "REVIEWER"
    CUSTOM = "CUSTOM"


class AgentInstructions(StandardModel):
    """SQLAlchemy model for agent instructions."""
    __tablename__ = "agent_instruction"
    agent_name = Column(String(255), nullable=False, unique=True)
    purpose = Column(Text, nullable=False)
    capabilities = Column(JSON, nullable=False)
    tone_guidelines = Column(Text, nullable=False)
    knowledge_domains = Column(JSON, nullable=False)
    response_templates = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    capabilities_list = relationship("AgentCapability", back_populates="agent_instructions", cascade="all, delete-orphan")
    knowledge_domains_list = relationship("AgentKnowledgeDomain", back_populates="agent_instructions", cascade="all, delete-orphan")


class AgentCapability(StandardModel):
    """SQLAlchemy model for agent capabilities."""
    __tablename__ = "agent_capability"
    agent_instruction_id = Column(UUID(as_uuid=True), ForeignKey("agent_instruction.id"), nullable=False)
    capability_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    parameters = Column(JSON, nullable=True)
    
    # Relationships
    agent_instructions = relationship("AgentInstructions", back_populates="capabilities_list")


class AgentKnowledgeDomain(StandardModel):
    """SQLAlchemy model for agent knowledge domains."""
    __tablename__ = "agent_knowledge_domain"
    agent_instruction_id = Column(UUID(as_uuid=True), ForeignKey("agent_instruction.id"), nullable=False)
    domain_name = Column(String(255), nullable=False)
    priority_level = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=False)
    
    # Relationships
    agent_instructions = relationship("AgentInstructions", back_populates="knowledge_domains_list")


class AgentPromptTemplate(StandardModel):
    """SQLAlchemy model for agent prompt templates."""
    __tablename__ = "agent_prompt_template"
    agent_instruction_id = Column(UUID(as_uuid=True), ForeignKey("agent_instruction.id"), nullable=False)
    template_name = Column(String(255), nullable=False)
    template_version = Column(String(50), nullable=False)
    template_content = Column(Text, nullable=False)
    context_parameters = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint for agent_instruction_id, template_name, and template_version
    __table_args__ = (
        UniqueConstraint('agent_instruction_id', 'template_name', 'template_version', 
                         name='uix_agent_prompt_template'),
    )
    
    # Relationships
    agent_instructions = relationship("AgentInstructions", backref="prompt_templates")


class ChatSession(StandardModel):
    """SQLAlchemy model for chat sessions."""
    __tablename__ = "chat_session"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    session_metadata = Column(String(1024), nullable=True)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    
class ChatMessage(StandardModel):
    """SQLAlchemy model for chat messages."""
    __tablename__ = "chat_message"
    
    session_id = Column(String(36), ForeignKey("chat_session.id"), nullable=False)
    role = Column(String(10), nullable=False)  # 'user' or 'bot'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    message_metadata = Column(String(1024), nullable=True)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
