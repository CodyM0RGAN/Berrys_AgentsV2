from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any, Set, Union
from uuid import UUID, uuid4
from pydantic import Field, validator, root_validator, model_validator

from shared.models.src.base import BaseModel, BaseEntityModel, BaseTimestampModel
from shared.models.src.api.responses import create_data_response_model, create_list_response_model, ErrorResponse
from shared.models.src.api.requests import ListRequestParams

# Import shared enums
from shared.models.src.enums import AgentStatus, AgentType

# Import service-specific enums
from .enums import ExecutionState, AgentStateDetail


class UserInfo(BaseModel):
    """
    User information model.
    """
    id: str
    username: str
    email: Optional[str] = None
    is_admin: bool = False
    roles: List[str] = Field(default_factory=list)


class AgentBase(BaseModel):
    """
    Base model for Agent with common attributes.
    """
    name: str
    type: AgentType  # Using shared enum
    description: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)
    prompt_template: Optional[str] = None
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('name must not be empty')
        return v.strip()


class AgentCreate(AgentBase):
    """
    Model for creating a new Agent.
    """
    project_id: UUID
    template_id: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Research Assistant",
                "type": "RESEARCHER",
                "description": "Agent for research tasks",
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "template_id": "researcher_template",
                "configuration": {
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
            }
        }


class AgentUpdate(BaseModel):
    """
    Model for updating an existing Agent.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    prompt_template: Optional[str] = None
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('name must not be empty')
        return v.strip() if v is not None else v
    
    @model_validator(mode='after')
    def check_at_least_one_field(self):
        if not any(self.model_dump(exclude_unset=True).values()):
            raise ValueError('at least one field must be provided')
        return self
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Research Assistant",
                "configuration": {
                    "max_tokens": 4000,
                    "temperature": 0.5
                }
            }
        }


class AgentResponse(AgentBase, BaseEntityModel, BaseTimestampModel):
    """
    Model for Agent response.
    """
    project_id: UUID
    status: AgentStatus  # Changed from state to status
    state_detail: Optional[AgentStateDetail] = None  # Added for detailed state
    last_active_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Research Assistant",
                "type": "RESEARCHER",
                "description": "Agent for research tasks",
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "ACTIVE",
                "state_detail": "READY",
                "configuration": {
                    "max_tokens": 2000,
                    "temperature": 0.7
                },
                "prompt_template": "You are a research assistant...",
                "created_at": "2025-03-20T10:30:00Z",
                "updated_at": "2025-03-20T10:35:00Z",
                "last_active_at": "2025-03-20T10:40:00Z"
            }
        }


# Replace with shared list response model
AgentListResponse = create_list_response_model(AgentResponse)


class AgentTemplateBase(BaseModel):
    """
    Base model for Agent Template with common attributes.
    """
    name: str
    description: Optional[str] = None
    agent_type: AgentType
    configuration_schema: Dict[str, Any] = Field(default_factory=dict)
    default_configuration: Dict[str, Any] = Field(default_factory=dict)
    prompt_template: Optional[str] = None
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('name must not be empty')
        return v.strip()


class AgentTemplateCreate(AgentTemplateBase):
    """
    Model for creating a new Agent Template.
    """
    id: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Researcher Template",
                "description": "Template for research agents",
                "agent_type": "RESEARCHER",
                "configuration_schema": {
                    "type": "object",
                    "properties": {
                        "max_tokens": {
                            "type": "integer",
                            "minimum": 100,
                            "maximum": 8000
                        },
                        "temperature": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1
                        }
                    }
                },
                "default_configuration": {
                    "max_tokens": 2000,
                    "temperature": 0.7
                },
                "prompt_template": "You are a research assistant..."
            }
        }


class AgentTemplateUpdate(BaseModel):
    """
    Model for updating an existing Agent Template.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    configuration_schema: Optional[Dict[str, Any]] = None
    default_configuration: Optional[Dict[str, Any]] = None
    prompt_template: Optional[str] = None
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('name must not be empty')
        return v.strip() if v is not None else v
    
    @model_validator(mode='after')
    def check_at_least_one_field(self):
        if not any(self.model_dump(exclude_unset=True).values()):
            raise ValueError('at least one field must be provided')
        return self
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Researcher Template",
                "default_configuration": {
                    "max_tokens": 4000,
                    "temperature": 0.5
                }
            }
        }


class AgentTemplate(AgentTemplateBase, BaseEntityModel, BaseTimestampModel):
    """
    Model for Agent Template response.
    """
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "researcher_template",
                "name": "Researcher Template",
                "description": "Template for research agents",
                "agent_type": "RESEARCHER",
                "configuration_schema": {
                    "type": "object",
                    "properties": {
                        "max_tokens": {
                            "type": "integer",
                            "minimum": 100,
                            "maximum": 8000
                        },
                        "temperature": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1
                        }
                    }
                },
                "default_configuration": {
                    "max_tokens": 2000,
                    "temperature": 0.7
                },
                "prompt_template": "You are a research assistant...",
                "created_at": "2025-03-20T10:30:00Z",
                "updated_at": "2025-03-20T10:35:00Z"
            }
        }


# Replace with shared list response model
AgentTemplateListResponse = create_list_response_model(AgentTemplate)


class AgentStatusChangeRequest(BaseModel):
    """
    Model for agent status change request.
    """
    target_status: AgentStatus  # Changed from target_state to target_status
    target_state_detail: Optional[AgentStateDetail] = None  # Added for detailed state
    reason: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "target_status": "ACTIVE",
                "target_state_detail": "READY",
                "reason": "Starting agent execution"
            }
        }


class ExecutionStatusChangeRequest(BaseModel):
    """
    Model for execution status change request.
    """
    target_state: ExecutionState
    reason: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "target_state": "PAUSED",
                "reason": "Pausing for human review"
            }
        }


class ExecutionProgressUpdate(BaseModel):
    """
    Model for execution progress updates.
    """
    progress_percentage: float  # 0.0 to 100.0
    status_message: str
    completed_steps: Optional[List[str]] = None
    current_step: Optional[str] = None
    remaining_steps: Optional[List[str]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "progress_percentage": 75.0,
                "status_message": "Processing data",
                "completed_steps": ["Initialize", "Load data", "Preprocess"],
                "current_step": "Process data",
                "remaining_steps": ["Save results", "Finalize"]
            }
        }


class ExecutionResultRequest(BaseModel):
    """
    Model for submitting execution results.
    """
    status: str  # "success" or "failure"
    result: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "result": {
                    "output": "Task completed successfully",
                    "data": {"key": "value"}
                },
                "metadata": {
                    "execution_time": 1.5,
                    "model_used": "gpt-4"
                }
            }
        }


class ExecutionResponse(BaseEntityModel, BaseTimestampModel):
    """
    Model for execution response.
    """
    agent_id: UUID
    task_id: UUID
    state: ExecutionState
    progress_percentage: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "task_id": "123e4567-e89b-12d3-a456-426614174000",
                "state": "RUNNING",
                "progress_percentage": 45.5,
                "result": None,
                "error_message": None,
                "created_at": "2025-03-20T10:30:00Z",
                "updated_at": "2025-03-20T10:35:00Z",
                "completed_at": None
            }
        }


class AgentExecutionRequest(BaseModel):
    """
    Model for agent execution request.
    """
    task_id: UUID
    context: List[Dict[str, Any]] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "123e4567-e89b-12d3-a456-426614174000",
                "context": [
                    {
                        "type": "text",
                        "content": "Research quantum computing algorithms"
                    }
                ],
                "parameters": {
                    "max_depth": 3,
                    "include_references": True
                }
            }
        }


class AgentExecutionResponseData(BaseModel):
    """
    Data model for agent execution response.
    """
    execution_id: UUID = Field(default_factory=uuid4)
    agent_id: UUID
    task_id: UUID
    status: str
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "execution_id": "123e4567-e89b-12d3-a456-426614174000",
                "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "task_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "started",
                "message": "Agent execution started successfully"
            }
        }


# Create response model using shared utility
AgentExecutionResponse = create_data_response_model(AgentExecutionResponseData)


class AgentCommunicationRequest(BaseModel):
    """
    Model for agent communication request.
    """
    to_agent_id: UUID
    content: Dict[str, Any]
    type: str
    
    class Config:
        schema_extra = {
            "example": {
                "to_agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "content": {
                    "message": "Can you help with this research task?",
                    "data": {
                        "topic": "Quantum computing"
                    }
                },
                "type": "request_assistance"
            }
        }


class AgentCommunicationResponseData(BaseModel):
    """
    Data model for agent communication response.
    """
    communication_id: UUID = Field(default_factory=uuid4)
    from_agent_id: UUID
    to_agent_id: UUID
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "communication_id": "123e4567-e89b-12d3-a456-426614174000",
                "from_agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "to_agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "delivered",
                "timestamp": "2025-03-20T10:40:00Z"
            }
        }


# Create response model using shared utility
AgentCommunicationResponse = create_data_response_model(AgentCommunicationResponseData)

# Create list response model using shared utility
AgentCommunicationListResponse = create_list_response_model(AgentCommunicationResponseData)


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
                "topic": "research.quantum_computing"
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
                "topic": "research.quantum_computing",
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
    message_type: str = "standard"
    
    class Config:
        schema_extra = {
            "example": {
                "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "topic": "research.quantum_computing",
                "content": {
                    "message": "New research paper on quantum algorithms",
                    "data": {
                        "title": "Quantum Algorithms for Machine Learning",
                        "url": "https://example.com/papers/quantum_ml.pdf"
                    }
                },
                "message_type": "research_update"
            }
        }


class TopicPublishResponse(BaseModel):
    """
    Model for topic publish response.
    """
    message_id: UUID
    agent_id: UUID
    topic: str
    status: str  # "published"
    
    class Config:
        schema_extra = {
            "example": {
                "message_id": "123e4567-e89b-12d3-a456-426614174000",
                "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "topic": "research.quantum_computing",
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
    message_type: str = "standard"
    
    class Config:
        schema_extra = {
            "example": {
                "from_agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "to_agent_ids": [
                    "223e4567-e89b-12d3-a456-426614174000",
                    "323e4567-e89b-12d3-a456-426614174000"
                ],
                "content": {
                    "message": "Team update on project status",
                    "data": {
                        "project": "Quantum Research",
                        "status": "In progress",
                        "completion": 65
                    }
                },
                "message_type": "status_update"
            }
        }


class BroadcastResponse(BaseModel):
    """
    Model for broadcast response.
    """
    message_ids: List[UUID]
    from_agent_id: UUID
    to_agent_ids: List[UUID]
    status: str  # "broadcast"
    
    class Config:
        schema_extra = {
            "example": {
                "message_ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "223e4567-e89b-12d3-a456-426614174000"
                ],
                "from_agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "to_agent_ids": [
                    "223e4567-e89b-12d3-a456-426614174000",
                    "323e4567-e89b-12d3-a456-426614174000"
                ],
                "status": "broadcast"
            }
        }


class RequestReplyRequest(BaseModel):
    """
    Model for request-reply pattern.
    """
    from_agent_id: UUID
    to_agent_id: UUID
    content: Dict[str, Any]
    timeout: float = 30.0  # Timeout in seconds
    
    class Config:
        schema_extra = {
            "example": {
                "from_agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "to_agent_id": "223e4567-e89b-12d3-a456-426614174000",
                "content": {
                    "question": "What is the status of the quantum research project?",
                    "context": {
                        "project_id": "quantum_research_2025"
                    }
                },
                "timeout": 15.0
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
                "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
                "from_agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "to_agent_id": "223e4567-e89b-12d3-a456-426614174000",
                "status": "replied",
                "reply": {
                    "answer": "The quantum research project is 65% complete.",
                    "details": {
                        "estimated_completion_date": "2025-06-30",
                        "current_phase": "Algorithm optimization"
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
                    "name": "research_priority_routing",
                    "condition": {
                        "topic": "research.*",
                        "priority": "high"
                    },
                    "action": {
                        "route_to": "senior_researcher_agent",
                        "priority_boost": 10
                    }
                }
            }
        }


class RoutingRuleResponse(BaseModel):
    """
    Model for routing rule response.
    """
    rule_name: str
    status: str  # "added", "updated", "removed"
    
    class Config:
        schema_extra = {
            "example": {
                "rule_name": "research_priority_routing",
                "status": "added"
            }
        }


class AgentStateHistoryItem(BaseEntityModel):
    """
    Model for agent state history items.
    """
    agent_id: UUID
    previous_status: Optional[AgentStatus] = None
    new_status: AgentStatus
    previous_state_detail: Optional[AgentStateDetail] = None
    new_state_detail: Optional[AgentStateDetail] = None
    reason: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "previous_status": "INACTIVE",
                "new_status": "INACTIVE",
                "previous_state_detail": "CREATED",
                "new_state_detail": "INITIALIZING",
                "reason": "Agent initialization started",
                "timestamp": "2025-03-20T10:30:00Z"
            }
        }


class ExecutionStateHistoryItem(BaseEntityModel):
    """
    Model for execution state history items.
    """
    execution_id: UUID
    previous_state: Optional[ExecutionState] = None
    new_state: ExecutionState
    reason: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "execution_id": "123e4567-e89b-12d3-a456-426614174000",
                "previous_state": "QUEUED",
                "new_state": "RUNNING",
                "reason": "Execution started",
                "timestamp": "2025-03-20T10:30:00Z"
            }
        }


# Using shared ErrorResponse from shared.models.src.api.responses


class HumanInteractionRequest(BaseModel):
    """
    Base model for human interaction requests.
    """
    execution_id: Optional[UUID] = None
    content: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "execution_id": "123e4567-e89b-12d3-a456-426614174000",
                "content": {
                    "message": "Please review this output",
                    "data": {"result": "Some result to review"}
                },
                "metadata": {
                    "priority": "high",
                    "source": "research_agent"
                }
            }
        }


class HumanInteractionResponseData(BaseModel):
    """
    Base data model for human interaction responses.
    """
    interaction_id: UUID = Field(default_factory=uuid4)
    agent_id: UUID
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "interaction_id": "123e4567-e89b-12d3-a456-426614174000",
                "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "pending",
                "timestamp": "2025-03-20T10:40:00Z"
            }
        }


# Create response model using shared utility
HumanInteractionResponse = create_data_response_model(HumanInteractionResponseData)


class HumanApprovalRequest(BaseModel):
    """
    Model for requesting human approval for an agent action.
    """
    execution_id: Optional[UUID] = None
    title: str
    description: str
    options: List[str]
    context: Dict[str, Any] = Field(default_factory=dict)
    deadline: Optional[datetime] = None
    priority: str = "normal"  # low, normal, high, critical
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "execution_id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Approve database schema changes",
                "description": "Please review and approve the proposed database schema changes",
                "options": ["Approve", "Reject", "Request modifications"],
                "context": {
                    "changes": [
                        {"table": "users", "action": "add_column", "column": "last_login_at"}
                    ]
                },
                "deadline": "2025-03-21T12:00:00Z",
                "priority": "high",
                "metadata": {
                    "source": "database_migration_agent"
                }
            }
        }


class HumanApprovalResponseData(HumanInteractionResponseData):
    """
    Data model for human approval response.
    """
    class Config:
        schema_extra = {
            "example": {
                "interaction_id": "123e4567-e89b-12d3-a456-426614174000",
                "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "pending",
                "timestamp": "2025-03-20T10:40:00Z"
            }
        }


# Create response model using shared utility
HumanApprovalResponse = create_data_response_model(HumanApprovalResponseData)


class HumanFeedbackRequest(BaseModel):
    """
    Model for submitting human feedback for an agent.
    """
    execution_id: Optional[UUID] = None
    feedback_type: str  # "quality", "correctness", "helpfulness", "other"
    content: str
    rating: Optional[float] = None  # 0.0 to 5.0
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "execution_id": "123e4567-e89b-12d3-a456-426614174000",
                "feedback_type": "quality",
                "content": "The code generated was well-structured and followed best practices",
                "rating": 4.5,
                "context": {
                    "task": "Generate a React component"
                },
                "metadata": {
                    "reviewer": "senior_developer"
                }
            }
        }


class HumanFeedbackResponseData(HumanInteractionResponseData):
    """
    Data model for human feedback response.
    """
    class Config:
        schema_extra = {
            "example": {
                "interaction_id": "123e4567-e89b-12d3-a456-426614174000",
                "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "timestamp": "2025-03-20T10:40:00Z"
            }
        }


# Create response model using shared utility
HumanFeedbackResponse = create_data_response_model(HumanFeedbackResponseData)


# Add aliases for backward compatibility with model registry
AgentList = AgentListResponse
AgentTemplateList = AgentTemplateListResponse


# Validation models for state transitions
class StateTransitionValidator:
    """
    Validator for agent state transitions.
    """
    # Define valid status transitions
    VALID_STATUS_TRANSITIONS = {
        AgentStatus.INACTIVE: {AgentStatus.ACTIVE, AgentStatus.ERROR, AgentStatus.MAINTENANCE},
        AgentStatus.ACTIVE: {AgentStatus.INACTIVE, AgentStatus.BUSY, AgentStatus.ERROR, AgentStatus.MAINTENANCE},
        AgentStatus.BUSY: {AgentStatus.ACTIVE, AgentStatus.INACTIVE, AgentStatus.ERROR, AgentStatus.MAINTENANCE},
        AgentStatus.ERROR: {AgentStatus.INACTIVE, AgentStatus.MAINTENANCE},
        AgentStatus.MAINTENANCE: {AgentStatus.INACTIVE, AgentStatus.ACTIVE},
    }
    
    # Define valid state detail transitions
    VALID_STATE_DETAIL_TRANSITIONS = {
        AgentStateDetail.CREATED: {AgentStateDetail.INITIALIZING},
        AgentStateDetail.INITIALIZING: {AgentStateDetail.READY, AgentStateDetail.ERROR},
        AgentStateDetail.READY: {AgentStateDetail.ACTIVE, AgentStateDetail.TERMINATED},
        AgentStateDetail.ACTIVE: {AgentStateDetail.PAUSED, AgentStateDetail.ERROR, AgentStateDetail.TERMINATED},
        AgentStateDetail.PAUSED: {AgentStateDetail.ACTIVE, AgentStateDetail.ERROR, AgentStateDetail.TERMINATED},
        AgentStateDetail.ERROR: {AgentStateDetail.INITIALIZING, AgentStateDetail.TERMINATED},
        AgentStateDetail.TERMINATED: set(),  # Terminal state, no transitions out
    }
    
    @classmethod
    def is_valid_status_transition(cls, current_status: AgentStatus, target_status: AgentStatus) -> bool:
        """
        Check if a status transition is valid.
        
        Args:
            current_status: Current agent status
            target_status: Target agent status
            
        Returns:
            bool: True if transition is valid, False otherwise
        """
        return target_status in cls.VALID_STATUS_TRANSITIONS.get(current_status, set())
    
    @classmethod
    def is_valid_state_detail_transition(cls, current_state: AgentStateDetail, target_state: AgentStateDetail) -> bool:
        """
        Check if a state detail transition is valid.
        
        Args:
            current_state: Current agent state detail
            target_state: Target agent state detail
            
        Returns:
            bool: True if transition is valid, False otherwise
        """
        return target_state in cls.VALID_STATE_DETAIL_TRANSITIONS.get(current_state, set())


class ExecutionStateTransitionValidator:
    """
    Validator for execution state transitions.
    """
    # Define valid state transitions
    VALID_TRANSITIONS = {
        ExecutionState.QUEUED: {ExecutionState.PREPARING, ExecutionState.CANCELLED},
        ExecutionState.PREPARING: {ExecutionState.RUNNING, ExecutionState.FAILED, ExecutionState.CANCELLED},
        ExecutionState.RUNNING: {ExecutionState.PAUSED, ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.CANCELLED},
        ExecutionState.PAUSED: {ExecutionState.RUNNING, ExecutionState.CANCELLED},
        ExecutionState.COMPLETED: set(),  # Terminal state
        ExecutionState.FAILED: {ExecutionState.QUEUED},  # Can retry failed executions
        ExecutionState.CANCELLED: set(),  # Terminal state
    }
    
    @classmethod
    def is_valid_transition(cls, current_state: ExecutionState, target_state: ExecutionState) -> bool:
        """
        Check if a state transition is valid.
        
        Args:
            current_state: Current execution state
            target_state: Target execution state
            
        Returns:
            bool: True if transition is valid, False otherwise
        """
        return target_state in cls.VALID_TRANSITIONS.get(current_state, set())
