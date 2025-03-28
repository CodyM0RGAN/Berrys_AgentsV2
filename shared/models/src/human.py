from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class InteractionType(str, Enum):
    APPROVAL_REQUEST = "APPROVAL_REQUEST"
    FEEDBACK_REQUEST = "FEEDBACK_REQUEST"
    CLARIFICATION_REQUEST = "CLARIFICATION_REQUEST"
    NOTIFICATION = "NOTIFICATION"
    MANUAL_INTERVENTION = "MANUAL_INTERVENTION"
    DECISION_POINT = "DECISION_POINT"


class InteractionStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ANSWERED = "ANSWERED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class InteractionPriority(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class HumanInteraction(BaseModel):
    """Model for human interactions."""
    id: UUID = Field(default_factory=uuid4)
    entity_id: UUID
    entity_type: str
    interaction_type: InteractionType
    content: Dict[str, Any]
    response: Optional[Dict[str, Any]] = None
    user_id: Optional[UUID] = None
    status: InteractionStatus = InteractionStatus.PENDING
    priority: InteractionPriority = InteractionPriority.MEDIUM
    created_at: datetime = Field(default_factory=datetime.utcnow)
    response_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "protected_namespaces": ()
    }


class ApprovalRequest(BaseModel):
    """Model for requesting human approval."""
    entity_id: UUID
    entity_type: str
    title: str
    description: str
    options: List[str] = ["Approve", "Reject"]
    context: Optional[Dict[str, Any]] = None
    priority: InteractionPriority = InteractionPriority.MEDIUM
    expires_in_minutes: Optional[int] = None  # None means no expiration


class FeedbackRequest(BaseModel):
    """Model for requesting human feedback."""
    entity_id: UUID
    entity_type: str
    title: str
    questions: List[Dict[str, Any]]  # [{question: str, type: str, options: List[str]}]
    context: Optional[Dict[str, Any]] = None
    priority: InteractionPriority = InteractionPriority.MEDIUM
    expires_in_minutes: Optional[int] = None


class ClarificationRequest(BaseModel):
    """Model for requesting clarification from a human."""
    entity_id: UUID
    entity_type: str
    title: str
    question: str
    context: Optional[Dict[str, Any]] = None
    priority: InteractionPriority = InteractionPriority.MEDIUM
    expires_in_minutes: Optional[int] = None


class Notification(BaseModel):
    """Model for sending notifications to humans."""
    entity_id: UUID
    entity_type: str
    title: str
    message: str
    level: str = "info"  # info, warning, error, success
    requires_acknowledgement: bool = False
    priority: InteractionPriority = InteractionPriority.MEDIUM


class ApprovalResponse(BaseModel):
    """Model for human approval response."""
    interaction_id: UUID
    approved: bool
    comment: Optional[str] = None
    user_id: UUID


class FeedbackResponse(BaseModel):
    """Model for human feedback response."""
    interaction_id: UUID
    answers: List[Dict[str, Any]]
    user_id: UUID


class ClarificationResponse(BaseModel):
    """Model for human clarification response."""
    interaction_id: UUID
    answer: str
    user_id: UUID


class InteractionQuery(BaseModel):
    """Model for querying human interactions."""
    entity_id: Optional[UUID] = None
    entity_type: Optional[str] = None
    interaction_type: Optional[InteractionType] = None
    status: Optional[InteractionStatus] = None
    user_id: Optional[UUID] = None
    min_priority: Optional[InteractionPriority] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


class InteractionStats(BaseModel):
    """Model for interaction statistics."""
    total_interactions: int
    pending_interactions: int
    interactions_by_type: Dict[InteractionType, int]
    interactions_by_status: Dict[InteractionStatus, int]
    average_response_time: Optional[float] = None  # in seconds
    interactions_by_priority: Dict[InteractionPriority, int]
