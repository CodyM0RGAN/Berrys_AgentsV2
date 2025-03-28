from sqlalchemy import Column, String, ForeignKey, JSON, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import BaseModel


# Association table for agent-tool many-to-many relationship
agent_tool_association = Table(
    'agent_tools',
    BaseModel.metadata,
    Column('agent_id', UUID(as_uuid=True), ForeignKey('agents.id'), primary_key=True),
    Column('tool_id', UUID(as_uuid=True), ForeignKey('tools.id'), primary_key=True),
    Column('configuration', JSON, nullable=True),
)


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
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    project = relationship("ProjectModel", back_populates="agents")
    
    # Relationships with other models
    tasks = relationship("TaskModel", back_populates="agent", cascade="all, delete-orphan")
    tools = relationship("ToolModel", secondary=agent_tool_association, back_populates="agents")
    
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
