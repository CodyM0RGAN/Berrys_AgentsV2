"""
Audit model for the web dashboard application.

This module defines the AuditLog model for tracking system changes.
"""

from sqlalchemy import Column, String, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from shared.models.src.audit import (
    AuditLog as SharedAuditLogModel,
    ActionType,
    EntityType,
    AuditSummary
)

from app.models.base import BaseModel

class AuditLog(BaseModel):
    """
    Audit log for tracking system changes.
    
    Attributes:
        id: Unique identifier
        entity_id: ID of the entity that changed
        entity_type: Type of entity (PROJECT, AGENT, etc.)
        action: What action was taken (CREATE, UPDATE, etc.)
        previous_state: The entity state before the change
        new_state: The entity state after the change
        actor_id: Who made the change
    """
    __tablename__ = 'audit_log'
    
    # Override id from BaseModel to add docstring
    id = Column(BaseModel.id.type, primary_key=True, default=BaseModel.id.default.arg)
    
    # Audit attributes
    entity_id = Column(String(50), nullable=False, index=True)  # Using String to support both UUID and string IDs
    entity_type = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    actor_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=True, index=True)
    
    # Relationships
    actor = relationship("User")
    
    # Create composite index on entity_id and entity_type
    __table_args__ = (
        Index('ix_audit_log_entity', 'entity_id', 'entity_type'),
    )
    
    def __init__(self, entity_id, entity_type, action, previous_state=None, new_state=None, actor_id=None):
        """
        Initialize a new AuditLog.
        
        Args:
            entity_id: ID of the entity that changed
            entity_type: Type of entity (PROJECT, AGENT, etc.)
            action: What action was taken (CREATE, UPDATE, etc.)
            previous_state: The entity state before the change (optional)
            new_state: The entity state after the change (optional)
            actor_id: Who made the change (optional)
        """
        self.entity_id = str(entity_id)  # Convert UUID to string if needed
        self.entity_type = entity_type
        self.action = action
        self.previous_state = previous_state or {}
        self.new_state = new_state or {}
        self.actor_id = actor_id
    
    def to_api_model(self) -> SharedAuditLogModel:
        """
        Convert to shared API model.
        
        Returns:
            A SharedAuditLogModel instance with this audit log's data
        """
        return SharedAuditLogModel(
            id=self.id,
            entity_id=self.entity_id,
            entity_type=EntityType(self.entity_type),
            action=ActionType(self.action),
            previous_state=self.previous_state,
            new_state=self.new_state,
            actor_id=self.actor_id,
            timestamp=self.created_at
        )
    
    def to_summary(self) -> AuditSummary:
        """
        Convert to audit summary model.
        
        Returns:
            An AuditSummary instance with this audit log's data
        """
        return AuditSummary(
            id=self.id,
            entity_id=self.entity_id,
            entity_type=EntityType(self.entity_type),
            action=ActionType(self.action),
            actor_id=self.actor_id,
            timestamp=self.created_at
        )
    
    @classmethod
    def from_api_model(cls, api_model: SharedAuditLogModel) -> 'AuditLog':
        """
        Create from shared API model.
        
        Args:
            api_model: The SharedAuditLogModel to convert
            
        Returns:
            A new AuditLog instance
        """
        return cls(
            entity_id=api_model.entity_id,
            entity_type=api_model.entity_type.value,
            action=api_model.action.value,
            previous_state=api_model.previous_state,
            new_state=api_model.new_state,
            actor_id=api_model.actor_id
        )
    
    def __repr__(self):
        """
        Get a string representation of the AuditLog.
        
        Returns:
            A string representation of the AuditLog
        """
        return f'<AuditLog {self.action} {self.entity_type}:{self.entity_id}>'


# Utility functions for audit logging

def log_create(entity, entity_type, actor_id=None):
    """
    Log entity creation.
    
    Args:
        entity: The entity that was created
        entity_type: The type of entity
        actor_id: The ID of the user who created the entity (optional)
        
    Returns:
        The created AuditLog instance
    """
    audit_log = AuditLog(
        entity_id=entity.id,
        entity_type=entity_type,
        action='CREATE',
        new_state=entity.to_dict() if hasattr(entity, 'to_dict') else {},
        actor_id=actor_id
    )
    
    from app import db
    db.session.add(audit_log)
    db.session.commit()
    
    return audit_log

def log_update(entity, entity_type, previous_state, actor_id=None):
    """
    Log entity update.
    
    Args:
        entity: The entity that was updated
        entity_type: The type of entity
        previous_state: The entity state before the update
        actor_id: The ID of the user who updated the entity (optional)
        
    Returns:
        The created AuditLog instance
    """
    audit_log = AuditLog(
        entity_id=entity.id,
        entity_type=entity_type,
        action='UPDATE',
        previous_state=previous_state,
        new_state=entity.to_dict() if hasattr(entity, 'to_dict') else {},
        actor_id=actor_id
    )
    
    from app import db
    db.session.add(audit_log)
    db.session.commit()
    
    return audit_log

def log_delete(entity_id, entity_type, previous_state, actor_id=None):
    """
    Log entity deletion.
    
    Args:
        entity_id: The ID of the entity that was deleted
        entity_type: The type of entity
        previous_state: The entity state before the deletion
        actor_id: The ID of the user who deleted the entity (optional)
        
    Returns:
        The created AuditLog instance
    """
    audit_log = AuditLog(
        entity_id=entity_id,
        entity_type=entity_type,
        action='DELETE',
        previous_state=previous_state,
        actor_id=actor_id
    )
    
    from app import db
    db.session.add(audit_log)
    db.session.commit()
    
    return audit_log
