"""
Human Interaction model for the web dashboard application.

This module defines the HumanInteraction model for tracking human interactions.
"""

from sqlalchemy import Column, String, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from shared.models.src.human import (
    HumanInteraction as SharedHumanInteractionModel,
    InteractionType,
    InteractionStatus,
    InteractionPriority
)

from app.models.base import BaseModel

class HumanInteraction(BaseModel):
    """
    Human interaction tracking.
    
    Attributes:
        id: Unique identifier
        entity_id: ID of the related entity
        entity_type: Type of entity (PROJECT, AGENT, etc.)
        interaction_type: Type of interaction (QUESTION, APPROVAL, etc.)
        content: The interaction content
        response: The human response
        response_time: When the response was provided
        status: The interaction status (PENDING, COMPLETED, etc.)
        priority: The interaction priority (1-5)
        assignee_id: The ID of the user assigned to handle the interaction
    """
    __tablename__ = 'human_interaction'
    
    # Override id from BaseModel to add docstring
    id = Column(BaseModel.id.type, primary_key=True, default=BaseModel.id.default.arg)
    
    # Human interaction attributes
    entity_id = Column(String(50), nullable=False, index=True)  # Using String to support both UUID and string IDs
    entity_type = Column(String(50), nullable=False, index=True)
    interaction_type = Column(String(50), nullable=False, index=True)
    content = Column(JSON, nullable=False)
    response = Column(JSON, nullable=True)
    response_time = Column(BaseModel.created_at.type, nullable=True)
    status = Column(String(20), nullable=False, default='PENDING', index=True)
    priority = Column(String(20), nullable=False, default='MEDIUM', index=True)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=True, index=True)
    
    # Relationships
    assignee = relationship("User")
    
    # Create composite index on entity_id and entity_type
    __table_args__ = (
        Index('ix_human_interaction_entity', 'entity_id', 'entity_type'),
    )
    
    def __init__(self, entity_id, entity_type, interaction_type, content, 
                 status='PENDING', priority='MEDIUM', assignee_id=None):
        """
        Initialize a new HumanInteraction.
        
        Args:
            entity_id: ID of the related entity
            entity_type: Type of entity (PROJECT, AGENT, etc.)
            interaction_type: Type of interaction (QUESTION, APPROVAL, etc.)
            content: The interaction content
            status: The interaction status (default: 'PENDING')
            priority: The interaction priority (default: 'MEDIUM')
            assignee_id: The ID of the user assigned to handle the interaction (optional)
        """
        self.entity_id = str(entity_id)  # Convert UUID to string if needed
        self.entity_type = entity_type
        self.interaction_type = interaction_type
        self.content = content
        self.status = status
        self.priority = priority
        self.assignee_id = assignee_id
    
    def to_api_model(self) -> SharedHumanInteractionModel:
        """
        Convert to shared API model.
        
        Returns:
            A SharedHumanInteractionModel instance with this interaction's data
        """
        return SharedHumanInteractionModel(
            id=self.id,
            entity_id=self.entity_id,
            entity_type=self.entity_type,
            type=InteractionType(self.interaction_type),
            content=self.content,
            response=self.response,
            response_time=self.response_time,
            status=InteractionStatus(self.status),
            priority=InteractionPriority(int(self.priority)) if self.priority.isdigit() else InteractionPriority.MEDIUM,
            assignee_id=self.assignee_id,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    @classmethod
    def from_api_model(cls, api_model: SharedHumanInteractionModel) -> 'HumanInteraction':
        """
        Create from shared API model.
        
        Args:
            api_model: The SharedHumanInteractionModel to convert
            
        Returns:
            A new HumanInteraction instance
        """
        return cls(
            entity_id=api_model.entity_id,
            entity_type=api_model.entity_type,
            interaction_type=api_model.type.value,
            content=api_model.content,
            status=api_model.status.value if api_model.status else 'PENDING',
            priority=str(api_model.priority.value) if api_model.priority else 'MEDIUM',
            assignee_id=api_model.assignee_id
        )
    
    def respond(self, response, user_id=None):
        """
        Record a response to this interaction.
        
        Args:
            response: The human response
            user_id: The ID of the user who responded (optional)
            
        Returns:
            Self for method chaining
        """
        self.response = response
        self.response_time = datetime.utcnow()
        self.status = 'COMPLETED'
        
        if user_id and not self.assignee_id:
            self.assignee_id = user_id
        
        from app import db
        db.session.commit()
        
        return self
    
    def assign(self, user_id):
        """
        Assign this interaction to a user.
        
        Args:
            user_id: The ID of the user to assign
            
        Returns:
            Self for method chaining
        """
        self.assignee_id = user_id
        
        from app import db
        db.session.commit()
        
        return self
    
    def __repr__(self):
        """
        Get a string representation of the HumanInteraction.
        
        Returns:
            A string representation of the HumanInteraction
        """
        return f'<HumanInteraction {self.interaction_type} {self.entity_type}:{self.entity_id} ({self.status})>'


# Utility functions for human interactions

def request_approval(entity_id, entity_type, content, assignee_id=None, priority='MEDIUM'):
    """
    Request approval from a human.
    
    Args:
        entity_id: ID of the related entity
        entity_type: Type of entity (PROJECT, AGENT, etc.)
        content: The approval request content
        assignee_id: The ID of the user to assign (optional)
        priority: The interaction priority (default: 'MEDIUM')
        
    Returns:
        The created HumanInteraction instance
    """
    interaction = HumanInteraction(
        entity_id=entity_id,
        entity_type=entity_type,
        interaction_type='APPROVAL',
        content=content,
        status='PENDING',
        priority=priority,
        assignee_id=assignee_id
    )
    
    from app import db
    db.session.add(interaction)
    db.session.commit()
    
    return interaction

def ask_question(entity_id, entity_type, content, assignee_id=None, priority='MEDIUM'):
    """
    Ask a question to a human.
    
    Args:
        entity_id: ID of the related entity
        entity_type: Type of entity (PROJECT, AGENT, etc.)
        content: The question content
        assignee_id: The ID of the user to assign (optional)
        priority: The interaction priority (default: 'MEDIUM')
        
    Returns:
        The created HumanInteraction instance
    """
    interaction = HumanInteraction(
        entity_id=entity_id,
        entity_type=entity_type,
        interaction_type='QUESTION',
        content=content,
        status='PENDING',
        priority=priority,
        assignee_id=assignee_id
    )
    
    from app import db
    db.session.add(interaction)
    db.session.commit()
    
    return interaction
