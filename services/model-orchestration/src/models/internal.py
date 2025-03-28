from sqlalchemy import Column, String, Float, Integer, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import List, Optional, Dict, Any

from shared.models.src.base import StandardModel, enum_column
from shared.utils.src.database import UUID, generate_uuid
from shared.models.src.enums import ModelProvider, ModelCapability, ModelStatus, RequestType


class ModelModel(StandardModel):
    """
    SQLAlchemy model for AI models.
    """
    __tablename__ = "model"
    
    # Basic information
    model_id = Column(String(100), nullable=False, unique=True)
    provider = enum_column(ModelProvider, nullable=False, default=ModelProvider.OPENAI)
    display_name = Column(String(100), nullable=True)
    description = Column(String, nullable=True)
    
    # Capabilities and status
    capabilities = Column(ARRAY(String), nullable=False)
    status = enum_column(ModelStatus, nullable=False, default=ModelStatus.ACTIVE)
    
    # Define enum columns for validation
    __enum_columns__ = {
        'provider': ModelProvider,
        'status': ModelStatus
    }
    
    # Token limits and costs
    max_tokens = Column(Integer, nullable=True)
    token_limit = Column(Integer, nullable=True)
    cost_per_token = Column(Float, nullable=True)
    
    # Configuration and metadata
    configuration = Column(JSON, nullable=True)
    model_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' which is reserved in SQLAlchemy
    
    # Relationships
    # requests = relationship("RequestModel", back_populates="model", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Model(id={self.id}, model_id='{self.model_id}', provider='{self.provider}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            "id": str(self.id),
            "model_id": self.model_id,
            "provider": self.provider.value if self.provider else None,
            "display_name": self.display_name,
            "description": self.description,
            "capabilities": [cap for cap in self.capabilities] if self.capabilities else [],
            "status": self.status.value if self.status else None,
            "max_tokens": self.max_tokens,
            "token_limit": self.token_limit,
            "cost_per_token": self.cost_per_token,
            "configuration": self.configuration or {},
            "metadata": self.model_metadata or {},  # Still return as 'metadata' for API compatibility
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class RequestModel(StandardModel):
    """
    SQLAlchemy model for model requests.
    """
    __tablename__ = "request"
    
    # Request information
    request_id = Column(String(100), nullable=False, unique=True)
    request_type = enum_column(RequestType, nullable=False)
    model_id = Column(String(100), nullable=False)
    provider = enum_column(ModelProvider, nullable=False)
    
    # Define enum columns for validation
    __enum_columns__ = {
        'request_type': RequestType,
        'provider': ModelProvider
    }
    
    # User and project information
    user_id = Column(String(100), nullable=True)
    project_id = Column(String(100), nullable=True)
    task_id = Column(String(100), nullable=True)
    
    # Request data
    request_data = Column(JSON, nullable=False)
    response_data = Column(JSON, nullable=True)
    
    # Metrics
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    cost = Column(Float, nullable=True)
    
    # Status
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(String, nullable=True)
    error_code = Column(String(50), nullable=True)
    
    # Additional timestamps
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    # model_id = Column(UUID(as_uuid=True), ForeignKey("model.id"), nullable=False)
    # model = relationship("ModelModel", back_populates="requests")
    
    def __repr__(self):
        return f"<Request(id={self.id}, request_id='{self.request_id}', model_id='{self.model_id}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            "id": str(self.id),
            "request_id": self.request_id,
            "request_type": self.request_type.value if self.request_type else None,
            "model_id": self.model_id,
            "provider": self.provider.value if self.provider else None,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "cost": self.cost,
            "success": self.success,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ProviderQuotaModel(StandardModel):
    """
    SQLAlchemy model for provider quotas.
    """
    __tablename__ = "provider_quota"
    
    # Provider information
    provider = enum_column(ModelProvider, nullable=False)
    
    # Define enum columns for validation
    __enum_columns__ = {
        'provider': ModelProvider
    }
    
    # Quota information
    daily_token_limit = Column(Integer, nullable=True)
    monthly_token_limit = Column(Integer, nullable=True)
    daily_cost_limit = Column(Float, nullable=True)
    monthly_cost_limit = Column(Float, nullable=True)
    
    # Usage tracking
    daily_tokens_used = Column(Integer, nullable=False, default=0)
    monthly_tokens_used = Column(Integer, nullable=False, default=0)
    daily_cost_used = Column(Float, nullable=False, default=0.0)
    monthly_cost_used = Column(Float, nullable=False, default=0.0)
    
    # Reset dates
    daily_reset_at = Column(DateTime(timezone=True), nullable=True)
    monthly_reset_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<ProviderQuota(id={self.id}, provider='{self.provider}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            "id": str(self.id),
            "provider": self.provider.value if self.provider else None,
            "daily_token_limit": self.daily_token_limit,
            "monthly_token_limit": self.monthly_token_limit,
            "daily_cost_limit": self.daily_cost_limit,
            "monthly_cost_limit": self.monthly_cost_limit,
            "daily_tokens_used": self.daily_tokens_used,
            "monthly_tokens_used": self.monthly_tokens_used,
            "daily_cost_used": self.daily_cost_used,
            "monthly_cost_used": self.monthly_cost_used,
            "daily_reset_at": self.daily_reset_at.isoformat() if self.daily_reset_at else None,
            "monthly_reset_at": self.monthly_reset_at.isoformat() if self.monthly_reset_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
