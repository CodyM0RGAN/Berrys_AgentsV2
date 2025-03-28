from sqlalchemy import Column, String, JSON, ForeignKey, Integer, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import BaseModel


class HumanInteractionModel(BaseModel):
    """
    SQLAlchemy model for human interactions.
    """
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Interaction details
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    entity_type = Column(String(50), nullable=False)
    interaction_type = Column(String(50), nullable=False)
    
    # Content
    content = Column(JSON, nullable=False)
    response = Column(JSON, nullable=True)
    
    # User
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user = relationship("UserModel")
    
    # Status
    status = Column(String(20), nullable=False, default="PENDING")
    priority = Column(Integer, nullable=False, default=2)  # 1-4, 4 being highest
    
    # Timing
    response_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<HumanInteraction(id={self.id}, type='{self.interaction_type}', status='{self.status}', priority={self.priority})>"


class ApprovalRequestModel(HumanInteractionModel):
    """
    SQLAlchemy model for approval requests.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': 'APPROVAL_REQUEST',
    }
    
    # Additional fields specific to approval requests
    approved = Column(Boolean, nullable=True)
    comment = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<ApprovalRequest(id={self.id}, status='{self.status}', approved={self.approved})>"


class FeedbackRequestModel(HumanInteractionModel):
    """
    SQLAlchemy model for feedback requests.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': 'FEEDBACK_REQUEST',
    }
    
    # Additional fields specific to feedback requests
    feedback = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<FeedbackRequest(id={self.id}, status='{self.status}')>"


class ClarificationRequestModel(HumanInteractionModel):
    """
    SQLAlchemy model for clarification requests.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': 'CLARIFICATION_REQUEST',
    }
    
    # Additional fields specific to clarification requests
    answer = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<ClarificationRequest(id={self.id}, status='{self.status}')>"


class NotificationModel(HumanInteractionModel):
    """
    SQLAlchemy model for notifications.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': 'NOTIFICATION',
    }
    
    # Additional fields specific to notifications
    level = Column(String(20), nullable=False, default="info")
    requires_acknowledgement = Column(Boolean, nullable=False, default=False)
    acknowledged = Column(Boolean, nullable=False, default=False)
    
    def __repr__(self):
        return f"<Notification(id={self.id}, level='{self.level}', acknowledged={self.acknowledged})>"
