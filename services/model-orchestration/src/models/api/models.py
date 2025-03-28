"""
API models.

This module contains the core models used by the model orchestration service API.
"""

from typing import List, Dict, Optional, Any
from pydantic import Field, model_validator, field_validator # Re-added field_validator

from shared.models.src.base import BaseModel, BaseEntityModel, BaseTimestampModel
from shared.models.src.enums import ModelProvider, ModelCapability, ModelStatus

__all__ = [
    "ModelBase",
    "ModelCreate",
    "ModelUpdate",
    "ModelInDB",
    "Model",
    "ModelList",
    "AgentList",
]


class ModelBase(BaseEntityModel):
    """
    Base model for Model with common attributes.
    """
    model_config = {
        "protected_namespaces": ()
    }
    model_id: str
    provider: ModelProvider
    capabilities: List[ModelCapability]
    status: ModelStatus = ModelStatus.ACTIVE
    display_name: Optional[str] = None
    description: Optional[str] = None
    max_tokens: Optional[int] = None
    token_limit: Optional[int] = None
    cost_per_token: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    configuration: Optional[Dict[str, Any]] = None # Added configuration here
    
    @field_validator('model_id')
    def model_id_must_not_be_empty(cls, v, info):
        if not v or not v.strip():
            raise ValueError('model_id must not be empty')
        return v.strip()


class ModelCreate(BaseModel):
    """
    Model for creating a new Model.
    """
    model_config = {
        "protected_namespaces": (),
        "schema_extra": {
            "example": {
                "model_id": "gpt-4",
                "provider": "OPENAI",
                "capabilities": ["CHAT"],
                "display_name": "GPT-4",
                "description": "OpenAI's most advanced model",
                "max_tokens": 8192,
                "token_limit": 8192,
                "cost_per_token": 0.00003,
                "configuration": {
                    "temperature": 0.7,
                    "top_p": 1.0
                }
            }
        }
    }


class ModelUpdate(BaseModel):
    """
    Model for updating an existing Model.
    """
    model_config = {
        "protected_namespaces": ()
    }
    display_name: Optional[str] = None
    description: Optional[str] = None
    capabilities: Optional[List[ModelCapability]] = None
    status: Optional[ModelStatus] = None
    max_tokens: Optional[int] = None
    token_limit: Optional[int] = None
    cost_per_token: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    
    @model_validator(mode='after')
    def check_at_least_one_field(cls, values, info):
        fields = [
            'display_name', 'description', 'capabilities', 'status',
            'max_tokens', 'token_limit', 'cost_per_token', 'metadata', 'configuration'
        ]
        if not any(getattr(cls, field) is not None for field in fields):
            raise ValueError('at least one field must be provided')
        return values
    
    model_config = {
        "schema_extra": {
            "example": {
                "status": "INACTIVE",
                "description": "Updated description"
            }
        }
    }


class ModelInDB(ModelBase, BaseTimestampModel):
    """
    Model for Model as stored in the database. Includes all fields from ModelBase plus timestamps.
    """
    model_config = {
        "protected_namespaces": (),
        "from_attributes": True
    }
    # Configuration is now inherited from ModelBase


class Model(ModelInDB):
    """
    Complete Model model with all attributes.
    """
    pass


class ModelList(BaseModel):
    """
    Paginated list of models.
    """
    items: List[Model]
    total: int
    page: int
    page_size: int


class AgentList(BaseModel):
    """
    Paginated list of agents.
    
    This class is added for compatibility with the model registry.
    """
    items: List[Any] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
