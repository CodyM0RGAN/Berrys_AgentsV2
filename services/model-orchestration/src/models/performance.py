from sqlalchemy import Column, String, Float, Integer, JSON, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from typing import List, Optional, Dict, Any

# Updated import to use the correct Base class
from shared.models.src.base import Base


class ModelPerformanceModel(Base):
    """
    SQLAlchemy model for tracking model performance metrics.
    """
    __tablename__ = "model_performance"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Reference to model
    model_id = Column(String(100), nullable=False, index=True)
    
    # Task type and metrics
    task_type = Column(String(50), nullable=False, index=True)
    quality_score = Column(Float, nullable=False, default=0.0)
    success_rate = Column(Float, nullable=False, default=0.0)
    sample_count = Column(Integer, nullable=False, default=0)
    
    # Additional metrics as JSON
    metrics = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_model_performance_model_task', 'model_id', 'task_type', unique=True),
    )
    
    def __repr__(self):
        return f"<ModelPerformance(id={self.id}, model_id='{self.model_id}', task_type='{self.task_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            "id": str(self.id),
            "model_id": self.model_id,
            "task_type": self.task_type,
            "quality_score": self.quality_score,
            "success_rate": self.success_rate,
            "sample_count": self.sample_count,
            "metrics": self.metrics or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ModelFeedbackModel(Base):
    """
    SQLAlchemy model for storing user feedback on model responses.
    """
    __tablename__ = "model_feedback"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Reference to request and model
    request_id = Column(String(100), nullable=False, index=True)
    model_id = Column(String(100), nullable=False, index=True)
    
    # Feedback data
    task_type = Column(String(50), nullable=True, index=True)
    quality_rating = Column(Float, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    feedback_text = Column(String, nullable=True)
    
    # Corrections
    has_corrections = Column(Boolean, nullable=False, default=False)
    original_content = Column(String, nullable=True)
    corrected_content = Column(String, nullable=True)
    
    # User information
    user_id = Column(String(100), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ModelFeedback(id={self.id}, model_id='{self.model_id}', request_id='{self.request_id}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            "id": str(self.id),
            "request_id": self.request_id,
            "model_id": self.model_id,
            "task_type": self.task_type,
            "quality_rating": self.quality_rating,
            "success": self.success,
            "feedback_text": self.feedback_text,
            "has_corrections": self.has_corrections,
            "original_content": self.original_content,
            "corrected_content": self.corrected_content,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ModelPerformanceHistoryModel(Base):
    """
    SQLAlchemy model for tracking historical performance metrics.
    """
    __tablename__ = "model_performance_history"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Reference to model
    model_id = Column(String(100), nullable=False, index=True)
    
    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), nullable=False)  # 'day', 'week', 'month'
    
    # Task type and metrics
    task_type = Column(String(50), nullable=False, index=True)
    quality_score = Column(Float, nullable=False, default=0.0)
    success_rate = Column(Float, nullable=False, default=0.0)
    sample_count = Column(Integer, nullable=False, default=0)
    
    # Additional metrics as JSON
    metrics = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_model_history_model_task_period', 'model_id', 'task_type', 'period_start', 'period_type', unique=True),
    )
    
    def __repr__(self):
        return f"<ModelPerformanceHistory(id={self.id}, model_id='{self.model_id}', period='{self.period_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            "id": str(self.id),
            "model_id": self.model_id,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "period_type": self.period_type,
            "task_type": self.task_type,
            "quality_score": self.quality_score,
            "success_rate": self.success_rate,
            "sample_count": self.sample_count,
            "metrics": self.metrics or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
