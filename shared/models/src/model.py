from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class ModelProvider(str, Enum):
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    OLLAMA = "OLLAMA"
    CUSTOM = "CUSTOM"


class ModelStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"
    TESTING = "TESTING"


class ModelCapability(str, Enum):
    REASONING = "REASONING"
    CODE_GENERATION = "CODE_GENERATION"
    CREATIVE = "CREATIVE"
    SUMMARIZATION = "SUMMARIZATION"
    CLASSIFICATION = "CLASSIFICATION"
    EXTRACTION = "EXTRACTION"
    TOOL_USE = "TOOL_USE"
    VISION = "VISION"


class ModelBase(BaseModel):
    """Base model for AI Model with common attributes."""
    id: str  # e.g., "gpt-4o", "claude-3-opus", "llama3:latest"
    provider: ModelProvider
    version: str
    capabilities: Dict[ModelCapability, float] = Field(default_factory=dict)  # capability -> score (0.0-1.0)
    context_window: int
    cost_per_1k_input: Optional[float] = None
    cost_per_1k_output: Optional[float] = None
    is_local: bool
    
    model_config = {
        "protected_namespaces": ()
    }


class ModelCreate(ModelBase):
    """Model for creating a new AI Model."""
    pass


class ModelUpdate(BaseModel):
    """Model for updating an existing AI Model."""
    capabilities: Optional[Dict[ModelCapability, float]] = None
    context_window: Optional[int] = None
    cost_per_1k_input: Optional[float] = None
    cost_per_1k_output: Optional[float] = None
    status: Optional[ModelStatus] = None


class ModelInDB(ModelBase):
    """Model for AI Model as stored in the database."""
    status: ModelStatus = ModelStatus.ACTIVE
    created_at: datetime
    updated_at: datetime

    model_config = {
        "protected_namespaces": (),
        "from_attributes": True
    }


class Model(ModelInDB):
    """Complete AI Model with all attributes."""
    pass


class ModelSummary(BaseModel):
    """Simplified AI Model for list views."""
    id: str
    provider: ModelProvider
    version: str
    is_local: bool
    status: ModelStatus

    model_config = {
        "protected_namespaces": (),
        "from_attributes": True
    }


class ModelRequest(BaseModel):
    """Model for requesting a prediction from an AI model."""
    prompt: str
    model_preference: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    response_format: Optional[Dict[str, Any]] = None
    task_type: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None
    
    model_config = {
        "protected_namespaces": ()
    }


class ModelResponse(BaseModel):
    """Model for AI model response."""
    content: str
    model_used: str
    usage: Dict[str, int]
    latency_ms: int
    metrics: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "protected_namespaces": ()
    }


class ModelPerformanceMetric(BaseModel):
    """Model for recording model performance metrics."""
    model_id: str
    task_type: str
    success: bool
    latency_ms: int
    input_tokens: int
    output_tokens: int
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "protected_namespaces": ()
    }


class ModelUsage(BaseModel):
    """Model for tracking model usage."""
    model_id: str
    project_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    input_tokens: int
    output_tokens: int
    cost: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "protected_namespaces": ()
    }


class ModelBudget(BaseModel):
    """Model for managing model usage budgets."""
    id: UUID = Field(default_factory=uuid4)
    project_id: Optional[UUID] = None  # None means global budget
    monthly_limit: float
    current_usage: float = 0.0
    last_reset: datetime = Field(default_factory=datetime.utcnow)
    alert_percentage: int = 80
    
    model_config = {
        "protected_namespaces": ()
    }
