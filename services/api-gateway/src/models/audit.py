from sqlalchemy import Column, String, Float, JSON, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import BaseModel


class AuditLogModel(BaseModel):
    """
    SQLAlchemy model for audit logs.
    """
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Audit details
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    entity_type = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    
    # State changes
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    
    # Actor
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor = relationship("UserModel")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, entity_type='{self.entity_type}', action='{self.action}')>"


class PerformanceMetricModel(BaseModel):
    """
    SQLAlchemy model for performance metrics.
    """
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metric details
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    entity_type = Column(String(50), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    
    # Additional context
    context = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<PerformanceMetric(id={self.id}, entity_type='{self.entity_type}', metric_name='{self.metric_name}', value={self.metric_value})>"


class OptimizationSuggestionModel(BaseModel):
    """
    SQLAlchemy model for optimization suggestions.
    """
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Suggestion details
    category = Column(String(50), nullable=False)
    description = Column(String, nullable=False)
    evidence = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    impact_score = Column(Float, nullable=False)
    
    def __repr__(self):
        return f"<OptimizationSuggestion(id={self.id}, category='{self.category}', status='{self.status}', impact_score={self.impact_score})>"


class OptimizationImplementationModel(BaseModel):
    """
    SQLAlchemy model for implemented optimizations.
    """
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Implementation details
    suggestion_id = Column(UUID(as_uuid=True), ForeignKey("optimization_suggestion.id", ondelete="CASCADE"), nullable=False)
    suggestion = relationship("OptimizationSuggestionModel")
    
    implementation_details = Column(JSON, nullable=False)
    implemented_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    implementer = relationship("UserModel")
    
    result_metrics = Column(JSON, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    
    def __repr__(self):
        return f"<OptimizationImplementation(id={self.id}, suggestion_id={self.suggestion_id}, success={self.success})>"
