"""
Collaboration pattern models.

This module contains models for collaboration pattern functionality.
"""

from typing import List, Dict, Optional, Any
from uuid import UUID
from pydantic import Field, validator

from shared.models.src.base import BaseModel, BaseEntityModel, BaseTimestampModel
from shared.models.src.api.responses import create_data_response_model, create_list_response_model
from shared.models.src.enums import AgentType


class CollaborationPatternBase(BaseModel):
    """
    Base model for collaboration pattern.
    """
    source_agent_type: str
    target_agent_type: str
    interaction_type: str
    description: Optional[str] = None
    priority: Optional[int] = 1  # 1 = normal, 2 = medium, 3 = high
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "source_agent_type": "DEVELOPER",
                "target_agent_type": "DESIGNER",
                "interaction_type": "REQUEST_REVIEW",
                "description": "Request UI design review",
                "priority": 2,
                "metadata": {
                    "tags": ["design", "review"],
                    "frequency": "as-needed"
                }
            }
        }


class CollaborationPatternCreate(CollaborationPatternBase):
    """
    Model for creating a collaboration pattern.
    """
    pass


class CollaborationPatternUpdate(BaseModel):
    """
    Model for updating a collaboration pattern.
    """
    target_agent_type: Optional[str] = None
    interaction_type: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "target_agent_type": "DESIGNER",
                "interaction_type": "REQUEST_FEEDBACK",
                "description": "Request design feedback",
                "priority": 3,
                "metadata": {
                    "tags": ["design", "feedback"],
                    "frequency": "weekly"
                }
            }
        }


class CollaborationPattern(CollaborationPatternBase, BaseEntityModel, BaseTimestampModel):
    """
    Model for a collaboration pattern.
    """
    id: UUID
    source_agent_id: Optional[UUID] = None
    target_agent_id: Optional[UUID] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "source_agent_type": "DEVELOPER",
                "target_agent_type": "DESIGNER",
                "interaction_type": "REQUEST_REVIEW",
                "description": "Request UI design review",
                "priority": 2,
                "metadata": {
                    "tags": ["design", "review"],
                    "frequency": "as-needed"
                },
                "source_agent_id": "123e4567-e89b-12d3-a456-426614174001",
                "target_agent_id": "123e4567-e89b-12d3-a456-426614174002",
                "created_at": "2025-03-28T12:00:00Z",
                "updated_at": "2025-03-28T12:00:00Z"
            }
        }


class CollaborationGraphNode(BaseModel):
    """
    Model for a node in the collaboration graph.
    """
    agent_type: str
    agent_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "agent_type": "DEVELOPER",
                "agent_id": "123e4567-e89b-12d3-a456-426614174001",
                "metadata": {
                    "name": "Developer Agent",
                    "skills": ["Web Development", "API Integration"]
                }
            }
        }


class CollaborationGraphEdge(BaseModel):
    """
    Model for an edge in the collaboration graph.
    """
    source: str  # Agent type
    target: str  # Agent type
    interaction_type: str
    patterns: List[UUID]  # List of pattern IDs
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "source": "DEVELOPER",
                "target": "DESIGNER",
                "interaction_type": "REQUEST_REVIEW",
                "patterns": ["123e4567-e89b-12d3-a456-426614174000"],
                "metadata": {
                    "strength": 0.8,
                    "frequency": "high"
                }
            }
        }


class CollaborationGraph(BaseModel):
    """
    Model for a collaboration graph.
    """
    project_id: UUID
    nodes: List[CollaborationGraphNode]
    edges: List[CollaborationGraphEdge]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "nodes": [
                    {
                        "agent_type": "DEVELOPER",
                        "agent_id": "123e4567-e89b-12d3-a456-426614174001",
                        "metadata": {
                            "name": "Developer Agent",
                            "skills": ["Web Development", "API Integration"]
                        }
                    },
                    {
                        "agent_type": "DESIGNER",
                        "agent_id": "123e4567-e89b-12d3-a456-426614174002",
                        "metadata": {
                            "name": "Designer Agent",
                            "skills": ["UI/UX Design", "Visual Design"]
                        }
                    }
                ],
                "edges": [
                    {
                        "source": "DEVELOPER",
                        "target": "DESIGNER",
                        "interaction_type": "REQUEST_REVIEW",
                        "patterns": ["123e4567-e89b-12d3-a456-426614174000"],
                        "metadata": {
                            "strength": 0.8,
                            "frequency": "high"
                        }
                    }
                ],
                "metadata": {
                    "created_at": "2025-03-28T12:00:00Z",
                    "updated_at": "2025-03-28T12:00:00Z"
                }
            }
        }


# Create response models using shared utilities
CollaborationPatternResponse = create_data_response_model(CollaborationPattern)
CollaborationPatternListResponse = create_list_response_model(CollaborationPattern)
CollaborationGraphResponse = create_data_response_model(CollaborationGraph)
