"""
Enhanced communication API models.

This module provides API models for enhanced agent communication functionality.
"""

from datetime import datetime
from typing import List, Dict, Optional, Any, Set, Union
from uuid import UUID
from pydantic import Field, validator, root_validator, model_validator

from shared.models.src.base import BaseModel, BaseEntityModel, BaseTimestampModel
from shared.models.src.api.responses import create_data_response_model, create_list_response_model, ErrorResponse
from shared.models.src.api.requests import ListRequestParams

from .api import AgentCommunicationResponse, AgentCommunicationResponseData


class TopicSubscriptionRequest(BaseModel):
    """
    Model for topic subscription request.
    """
    agent_id: UUID
    topic: str
    
    class Config:
        schema_extra = {
            "example": {
                "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "topic": "project.updates"
            }
        }


class TopicSubscriptionResponse(BaseModel):
    """
    Model for topic subscription response.
    """
    agent_id: UUID
    topic: str
    status: str  # "subscribed" or "unsubscribed"
    
    class Config:
        schema_extra = {
            "example": {
                "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "topic": "project.updates",
                "status": "subscribed"
            }
        }


class TopicPublishRequest(BaseModel):
    """
    Model for topic publish request.
    """
    agent_id: UUID
    topic: str
    content: Dict[str, Any]
    message_type: str = "topic_message"
    
    class Config:
        schema_extra = {
            "example": {
                "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "topic": "project.updates",
                "content": {
                    "message": "Project status updated",
                    "data": {
                        "status": "in_progress",
                        "completion_percentage": 75
                    }
                },
                "message_type": "status_update"
            }
        }


class TopicPublishResponse(BaseModel):
    """
    Model for topic publish response.
    """
    message_id: str
    agent_id: UUID
    topic: str
    status: str  # "published"
    
    class Config:
        schema_extra = {
            "example": {
                "message_id": "msg_123456789",
                "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "topic": "project.updates",
                "status": "published"
            }
        }


class BroadcastRequest(BaseModel):
    """
    Model for broadcast request.
    """
    from_agent_id: UUID
    to_agent_ids: List[UUID]
    content: Dict[str, Any]
    message_type: str = "broadcast"
    
    class Config:
        schema_extra = {
            "example": {
                "from_agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "to_agent_ids": [
                    "123e4567-e89b-12d3-a456-426614174001",
                    "123e4567-e89b-12d3-a456-426614174002"
                ],
                "content": {
                    "message": "Attention all agents",
                    "data": {
                        "priority": "high",
                        "action_required": True
                    }
                },
                "message_type": "alert"
            }
        }


class BroadcastResponse(BaseModel):
    """
    Model for broadcast response.
    """
    message_ids: List[str]
    from_agent_id: UUID
    to_agent_ids: List[UUID]
    status: str  # "broadcast"
    
    class Config:
        schema_extra = {
            "example": {
                "message_ids": [
                    "msg_123456789",
                    "msg_987654321"
                ],
                "from_agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "to_agent_ids": [
                    "123e4567-e89b-12d3-a456-426614174001",
                    "123e4567-e89b-12d3-a456-426614174002"
                ],
                "status": "broadcast"
            }
        }


class RequestReplyRequest(BaseModel):
    """
    Model for request-reply request.
    """
    from_agent_id: UUID
    to_agent_id: UUID
    content: Dict[str, Any]
    timeout: float = 60.0  # seconds
    
    class Config:
        schema_extra = {
            "example": {
                "from_agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "to_agent_id": "123e4567-e89b-12d3-a456-426614174001",
                "content": {
                    "message": "What is the status of task X?",
                    "data": {
                        "task_id": "task_123456789"
                    }
                },
                "timeout": 30.0
            }
        }


class RequestReplyResponse(BaseModel):
    """
    Model for request-reply response.
    """
    correlation_id: str
    from_agent_id: UUID
    to_agent_id: UUID
    status: str  # "replied" or "timeout"
    reply: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "correlation_id": "corr_123456789",
                "from_agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "to_agent_id": "123e4567-e89b-12d3-a456-426614174001",
                "status": "replied",
                "reply": {
                    "message": "Task X is in progress",
                    "data": {
                        "status": "in_progress",
                        "completion_percentage": 50
                    }
                }
            }
        }


class RoutingRuleRequest(BaseModel):
    """
    Model for routing rule request.
    """
    rule: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "rule": {
                    "name": "task_assignment_rule",
                    "conditions": [
                        {
                            "type": "field",
                            "field": "task_type",
                            "operator": "eq",
                            "value": "research"
                        }
                    ],
                    "actions": [
                        {
                            "type": "route",
                            "destination": "123e4567-e89b-12d3-a456-426614174000"
                        }
                    ],
                    "is_terminal": True
                }
            }
        }


class RoutingRuleResponse(BaseModel):
    """
    Model for routing rule response.
    """
    rule_name: str
    status: str  # "added"
    
    class Config:
        schema_extra = {
            "example": {
                "rule_name": "task_assignment_rule",
                "status": "added"
            }
        }


# Create list response model for agent communications
AgentCommunicationListResponse = create_list_response_model(AgentCommunicationResponseData)
