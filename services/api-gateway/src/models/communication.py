from sqlalchemy import Column, String, ForeignKey, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import BaseModel


class CommunicationModel(BaseModel):
    """
    SQLAlchemy model for agent communications.
    """
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Communication details
    from_agent_id = Column(UUID(as_uuid=True), ForeignKey("agent.id", ondelete="CASCADE"), nullable=False)
    to_agent_id = Column(UUID(as_uuid=True), ForeignKey("agent.id", ondelete="CASCADE"), nullable=False)
    
    # Content
    content = Column(JSON, nullable=False)
    type = Column(String(50), nullable=False)
    communication_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' which is reserved in SQLAlchemy
    
    # Timestamp
    sent_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships - using string references and explicit join conditions to avoid circular imports
    from_agent = relationship(
        "AgentModel", 
        foreign_keys=[from_agent_id],
        primaryjoin="CommunicationModel.from_agent_id == AgentModel.id",
        back_populates="sent_communications"
    )
    to_agent = relationship(
        "AgentModel", 
        foreign_keys=[to_agent_id],
        primaryjoin="CommunicationModel.to_agent_id == AgentModel.id",
        back_populates="received_communications"
    )
    
    def __repr__(self):
        return f"<Communication(id={self.id}, from='{self.from_agent_id}', to='{self.to_agent_id}', type='{self.type}')>"
