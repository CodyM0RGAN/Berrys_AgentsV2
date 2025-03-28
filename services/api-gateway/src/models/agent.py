from sqlalchemy import Column, String, ForeignKey, JSON, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import BaseModel

# Association table for agent-tool many-to-many relationship
# Defined after model classes to avoid circular imports
agent_tool_association = None


class AgentModel(BaseModel):
    """
    SQLAlchemy model for agents.
    """
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="CREATED")
    
    # Agent configuration
    configuration = Column(JSON, nullable=False, default={})
    prompt_template = Column(String, nullable=True)
    
    # Relationships
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    project = relationship("ProjectModel", back_populates="agents")
    
    # Relationships with other models
    tasks = relationship("TaskModel", back_populates="agent", cascade="all, delete-orphan")
    
    # Tools relationship - using string reference to avoid circular imports
    # The actual secondary table is defined after all models
    tools = relationship(
        "ToolModel", 
        secondary="agent_tool",
        back_populates="agents"
    )
    
    # Communication relationships
    sent_communications = relationship(
        "CommunicationModel",
        foreign_keys="CommunicationModel.from_agent_id",
        back_populates="from_agent",
        cascade="all, delete-orphan",
    )
    received_communications = relationship(
        "CommunicationModel",
        foreign_keys="CommunicationModel.to_agent_id",
        back_populates="to_agent",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}', type='{self.type}', status='{self.status}')>"


# Define the association table after model classes to avoid circular imports
# Import Base directly to avoid using BaseModel.metadata which conflicts with SQLAlchemy's reserved name
from ..database import Base

agent_tool_association = Table(
    'agent_tools',
    Base.metadata,  # Use Base.metadata instead of BaseModel.metadata
    Column('agent_id', UUID(as_uuid=True), ForeignKey('agent.id', ondelete="CASCADE"), primary_key=True),
    Column('tool_id', UUID(as_uuid=True), ForeignKey('tool.id', ondelete="CASCADE"), primary_key=True),
    Column('configuration', JSON, nullable=True),
)
