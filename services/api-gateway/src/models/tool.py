from sqlalchemy import Column, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import BaseModel


class ToolModel(BaseModel):
    """
    SQLAlchemy model for tools.
    """
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    capability = Column(String(100), nullable=False)
    source = Column(String(50), nullable=False)
    
    # Tool details
    documentation_url = Column(String, nullable=True)
    schema = Column(JSON, nullable=True)
    integration_type = Column(String(50), nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="DISCOVERED")
    
    # Relationships - using string references to avoid circular imports
    agents = relationship(
        "AgentModel", 
        secondary="agent_tool", 
        back_populates="tools"
    )
    
    def __repr__(self):
        return f"<Tool(id={self.id}, name='{self.name}', capability='{self.capability}', source='{self.source}')>"
