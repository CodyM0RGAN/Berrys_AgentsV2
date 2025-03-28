from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class AgentType(str, Enum):
    RESEARCHER = "RESEARCHER"
    PLANNER = "PLANNER"
    DEVELOPER = "DEVELOPER"
    REVIEWER = "REVIEWER"
    MANAGER = "MANAGER"
    SPECIALIST = "SPECIALIST"
    TOOL_CURATOR = "TOOL_CURATOR"
    DEPLOYMENT = "DEPLOYMENT"
    AUDITOR = "AUDITOR"
    CUSTOM = "CUSTOM"


class AgentStatus(str, Enum):
    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    TERMINATED = "TERMINATED"


class AgentBase(BaseModel):
    """Base model for Agent with common attributes."""
    name: str
    type: AgentType
    configuration: Dict[str, Any] = Field(default_factory=dict)
    prompt_template: Optional[str] = None


class AgentCreate(AgentBase):
    """Model for creating a new Agent."""
    project_id: UUID


class AgentUpdate(BaseModel):
    """Model for updating an existing Agent."""
    name: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    prompt_template: Optional[str] = None
    status: Optional[AgentStatus] = None


class AgentInDB(AgentBase):
    """Model for Agent as stored in the database."""
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    status: AgentStatus = AgentStatus.CREATED
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "protected_namespaces": ()
    }


class Agent(AgentInDB):
    """Complete Agent model with all attributes."""
    pass


class AgentSummary(BaseModel):
    """Simplified Agent model for list views."""
    id: UUID
    name: str
    type: AgentType
    status: AgentStatus
    project_id: UUID

    model_config = {
        "from_attributes": True,
        "protected_namespaces": ()
    }


class AgentWithTools(Agent):
    """Agent model with associated tools."""
    tools: List[Dict[str, Any]] = Field(default_factory=list)


class AgentWithPerformance(Agent):
    """Agent model with performance metrics."""
    task_count: int = 0
    completed_task_count: int = 0
    success_rate: float = 0.0
    average_completion_time: Optional[float] = None
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)


class AgentRequirement(BaseModel):
    """Model for specifying agent requirements during generation."""
    name: str
    description: str
    capabilities: List[str]
    priority: int = 3  # 1-5, 5 being highest


class AgentGenerationRequest(BaseModel):
    """Model for requesting agent generation."""
    project_id: UUID
    project_description: str
    requirements: Optional[List[AgentRequirement]] = None
