from sqlalchemy import Column, String, Boolean, Float, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import BaseModel


class AIModelModel(BaseModel):
    """
    SQLAlchemy model for AI models.
    """
    
    # Primary key (using model ID as primary key)
    id = Column(String(100), primary_key=True)
    
    # Basic information
    provider = Column(String(50), nullable=False)
    version = Column(String(50), nullable=False)
    
    # Capabilities
    capabilities = Column(JSON, nullable=False)
    context_window = Column(Integer, nullable=False)
    
    # Cost information
    cost_per_1k_input = Column(Float, nullable=True)
    cost_per_1k_output = Column(Float, nullable=True)
    
    # Status
    is_local = Column(Boolean, nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    
    # Relationships
    performance_metrics = relationship("ModelPerformanceMetricModel", back_populates="model", cascade="all, delete-orphan")
    usage_records = relationship("ModelUsageModel", back_populates="model", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AIModel(id='{self.id}', provider='{self.provider}', version='{self.version}', status='{self.status}')>"


class ModelPerformanceMetricModel(BaseModel):
    """
    SQLAlchemy model for model performance metrics.
    """
    
    # Primary key
    id = Column(String(100), primary_key=True)
    
    # Metric details
    model_id = Column(String(100), ForeignKey("ai_model.id", ondelete="CASCADE"), nullable=False)
    task_type = Column(String(50), nullable=False)
    success = Column(Boolean, nullable=False)
    latency_ms = Column(Integer, nullable=False)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    error_message = Column(String, nullable=True)
    
    # Relationships
    model = relationship("AIModelModel", back_populates="performance_metrics")
    
    def __repr__(self):
        return f"<ModelPerformanceMetric(id='{self.id}', model_id='{self.model_id}', task_type='{self.task_type}', success={self.success})>"


class ModelUsageModel(BaseModel):
    """
    SQLAlchemy model for model usage records.
    """
    
    # Primary key
    id = Column(String(100), primary_key=True)
    
    # Usage details
    model_id = Column(String(100), ForeignKey("ai_model.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    
    # Token usage
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    cost = Column(Float, nullable=True)
    
    # Relationships
    model = relationship("AIModelModel", back_populates="usage_records")
    
    def __repr__(self):
        return f"<ModelUsage(id='{self.id}', model_id='{self.model_id}', input_tokens={self.input_tokens}, output_tokens={self.output_tokens})>"


class ModelBudgetModel(BaseModel):
    """
    SQLAlchemy model for model budgets.
    """
    
    # Primary key
    id = Column(String(100), primary_key=True)
    
    # Budget details
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    monthly_limit = Column(Float, nullable=False)
    current_usage = Column(Float, nullable=False, default=0.0)
    last_reset = Column(DateTime(timezone=True), nullable=False)
    alert_percentage = Column(Integer, nullable=False, default=80)
    
    def __repr__(self):
        return f"<ModelBudget(id='{self.id}', project_id='{self.project_id}', monthly_limit={self.monthly_limit}, current_usage={self.current_usage})>"
