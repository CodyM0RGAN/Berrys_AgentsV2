"""
AI Model model for the web dashboard application.

This module defines the AI Model model for model management.
"""

from sqlalchemy import Column, String, Float, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from shared.models.src.model import (
    Model as SharedModelModel,
    ModelProvider,
    ModelStatus,
    ModelCapability,
    ModelSummary
)

from app.models.base import BaseModel

class AIModel(BaseModel):
    """
    AI Model for model management.
    
    Attributes:
        id: The model's identifier (string like "gpt-4o")
        provider: The model's provider (OPENAI, ANTHROPIC, etc.)
        version: The model's version
        capabilities: Capabilities and their scores
        context_window: Maximum context window size
        cost metrics: Input and output costs
        is_local: Whether the model runs locally
        status: The model's status (ACTIVE, INACTIVE, etc.)
    """
    __tablename__ = 'ai_model'  # Using ai_model to avoid SQL keyword conflicts
    
    # Using string ID since model IDs are often strings like "gpt-4o"
    id = Column(String(50), primary_key=True)
    provider = Column(String(20), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    capabilities = Column(JSON, nullable=True)
    context_window = Column(Integer, nullable=False)
    cost_per_1k_input = Column(Float, nullable=True)
    cost_per_1k_output = Column(Float, nullable=True)
    is_local = Column(Boolean, default=False)
    status = Column(String(20), nullable=False, default='ACTIVE', index=True)
    
    # Override created_at and updated_at from BaseModel
    # Since we're using a string primary key, we need to define these explicitly
    created_at = Column(BaseModel.created_at.type, default=datetime.utcnow, nullable=False)
    updated_at = Column(BaseModel.updated_at.type, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __init__(self, id, provider, version, context_window, capabilities=None, 
                 cost_per_1k_input=None, cost_per_1k_output=None, is_local=False, status='ACTIVE'):
        """
        Initialize a new AIModel.
        
        Args:
            id: The model's identifier (string like "gpt-4o")
            provider: The model's provider (OPENAI, ANTHROPIC, etc.)
            version: The model's version
            context_window: Maximum context window size
            capabilities: Capabilities and their scores (optional)
            cost_per_1k_input: Cost per 1000 input tokens (optional)
            cost_per_1k_output: Cost per 1000 output tokens (optional)
            is_local: Whether the model runs locally (default: False)
            status: The model's status (default: 'ACTIVE')
        """
        self.id = id
        self.provider = provider
        self.version = version
        self.context_window = context_window
        self.capabilities = capabilities or {}
        self.cost_per_1k_input = cost_per_1k_input
        self.cost_per_1k_output = cost_per_1k_output
        self.is_local = is_local
        self.status = status
    
    def to_api_model(self) -> SharedModelModel:
        """
        Convert to shared API model.
        
        Returns:
            A SharedModelModel instance with this model's data
        """
        # Convert capabilities dict to enum-keyed dict
        capabilities = {}
        for key, value in self.capabilities.items():
            try:
                capability_enum = ModelCapability(key)
                capabilities[capability_enum] = float(value)
            except (ValueError, TypeError):
                # Skip invalid capabilities
                pass
        
        return SharedModelModel(
            id=self.id,
            provider=ModelProvider(self.provider),
            version=self.version,
            capabilities=capabilities,
            context_window=self.context_window,
            cost_per_1k_input=self.cost_per_1k_input,
            cost_per_1k_output=self.cost_per_1k_output,
            is_local=self.is_local,
            status=ModelStatus(self.status),
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    def to_summary(self) -> ModelSummary:
        """
        Convert to model summary.
        
        Returns:
            A ModelSummary instance with this model's data
        """
        return ModelSummary(
            id=self.id,
            provider=ModelProvider(self.provider),
            version=self.version,
            is_local=self.is_local,
            status=ModelStatus(self.status)
        )
    
    @classmethod
    def from_api_model(cls, api_model: SharedModelModel) -> 'AIModel':
        """
        Create from shared API model.
        
        Args:
            api_model: The SharedModelModel to convert
            
        Returns:
            A new AIModel instance
        """
        # Convert capabilities enum-keyed dict to string-keyed dict
        capabilities = {}
        for key, value in api_model.capabilities.items():
            capabilities[key.value] = value
        
        return cls(
            id=api_model.id,
            provider=api_model.provider.value,
            version=api_model.version,
            context_window=api_model.context_window,
            capabilities=capabilities,
            cost_per_1k_input=api_model.cost_per_1k_input,
            cost_per_1k_output=api_model.cost_per_1k_output,
            is_local=api_model.is_local,
            status=api_model.status.value if api_model.status else 'ACTIVE'
        )
    
    def __repr__(self):
        """
        Get a string representation of the AIModel.
        
        Returns:
            A string representation of the AIModel
        """
        return f'<AIModel {self.id} ({self.provider}, {self.status})>'


class ModelUsage(BaseModel):
    """
    Model usage tracking.
    
    Attributes:
        id: Unique identifier
        model_id: The ID of the model used
        project_id: The project context (optional)
        agent_id: The agent context (optional)
        task_id: The task context (optional)
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cost: Estimated cost
        timestamp: When the usage occurred
    """
    __tablename__ = 'model_usage'
    
    id = Column(BaseModel.id.type, primary_key=True, default=BaseModel.id.default.arg)
    model_id = Column(String(50), ForeignKey('ai_model.id'), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey('project.id'), nullable=True, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agent.id'), nullable=True, index=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey('task.id'), nullable=True, index=True)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    cost = Column(Float, nullable=True)
    timestamp = Column(BaseModel.created_at.type, default=datetime.utcnow, index=True)
    
    # Relationships
    model = relationship("AIModel")
    project = relationship("Project")
    agent = relationship("Agent")
    task = relationship("Task")
    
    def __init__(self, model_id, input_tokens, output_tokens, project_id=None, 
                 agent_id=None, task_id=None, cost=None):
        """
        Initialize a new ModelUsage.
        
        Args:
            model_id: The ID of the model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            project_id: The project context (optional)
            agent_id: The agent context (optional)
            task_id: The task context (optional)
            cost: Estimated cost (optional)
        """
        self.model_id = model_id
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.project_id = project_id
        self.agent_id = agent_id
        self.task_id = task_id
        self.cost = cost
        self.timestamp = datetime.utcnow()
    
    def __repr__(self):
        """
        Get a string representation of the ModelUsage.
        
        Returns:
            A string representation of the ModelUsage
        """
        return f'<ModelUsage {self.model_id} ({self.input_tokens}in/{self.output_tokens}out)>'
