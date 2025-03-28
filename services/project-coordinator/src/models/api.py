"""
API models for the Project Coordinator service.

These models are used for API request/response validation and serialization.
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from shared.models.src.project import ProjectStatus


class ResourceType(str, Enum):
    """Types of resources that can be allocated to projects."""
    AGENT = "agent"
    MODEL = "model"
    TOOL = "tool"
    USER = "user"
    COMPUTE = "compute"
    STORAGE = "storage"


class OptimizationTarget(str, Enum):
    """Optimization targets for resource allocation."""
    TIME = "time"
    COST = "cost"
    QUALITY = "quality"
    BALANCED = "balanced"


class ArtifactType(str, Enum):
    """Types of artifacts that can be stored for projects."""
    DOCUMENT = "document"
    PLAN = "plan"
    CODE = "code"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DATA = "data"
    OTHER = "other"


class ProjectCreateRequest(BaseModel):
    """Request model for creating a new project."""
    name: str
    description: Optional[str] = None
    owner_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ProjectUpdateRequest(BaseModel):
    """Request model for updating a project."""
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    """Response model for project details."""
    id: UUID
    name: str
    description: Optional[str] = None
    status: ProjectStatus
    owner_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    project_metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectListResponse(BaseModel):
    """Response model for listing projects."""
    projects: List[ProjectResponse]
    total: int
    page: int
    page_size: int


class ProjectStateTransitionRequest(BaseModel):
    """Request model for transitioning a project's state."""
    target_state: ProjectStatus
    reason: Optional[str] = None


class ProjectStateHistoryResponse(BaseModel):
    """Response model for project state history."""
    id: UUID
    project_id: UUID
    state: ProjectStatus
    transitioned_at: datetime
    reason: Optional[str] = None
    transitioned_by: Optional[UUID] = None


class ProjectStateHistoryListResponse(BaseModel):
    """Response model for listing project state history."""
    states: List[ProjectStateHistoryResponse]
    total: int


class ProjectProgressUpdateRequest(BaseModel):
    """Request model for updating project progress."""
    percentage: float = Field(ge=0.0, le=100.0)
    metrics: Optional[Dict[str, Any]] = None
    milestone: Optional[str] = None


class ProjectProgressResponse(BaseModel):
    """Response model for project progress."""
    id: UUID
    project_id: UUID
    percentage: float
    recorded_at: datetime
    metrics: Dict[str, Any] = Field(default_factory=dict)
    milestone: Optional[str] = None


class ProjectProgressHistoryResponse(BaseModel):
    """Response model for project progress history."""
    progress_points: List[ProjectProgressResponse]
    average_progress_rate: float  # percentage per day


class ResourceAllocationRequest(BaseModel):
    """Request model for allocating resources to a project."""
    resource_type: ResourceType
    resource_id: str
    allocation: float = Field(ge=0.0, le=1.0)  # 0.0 to 1.0 (0% to 100%)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class ResourceResponse(BaseModel):
    """Response model for resource allocation details."""
    id: UUID
    project_id: UUID
    resource_type: ResourceType
    resource_id: str
    allocation: float
    allocated_at: datetime
    released_at: Optional[datetime] = None
    resource_metadata: Dict[str, Any] = Field(default_factory=dict)


class ResourceListResponse(BaseModel):
    """Response model for listing project resources."""
    resources: List[ResourceResponse]
    total: int


class ResourceOptimizationRequest(BaseModel):
    """Request model for optimizing resource allocation."""
    target: OptimizationTarget
    constraints: Optional[Dict[str, Any]] = None


class ResourceOptimizationResponse(BaseModel):
    """Response model for resource optimization results."""
    optimized_resources: List[ResourceResponse]
    optimization_score: float
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ArtifactCreateRequest(BaseModel):
    """Request model for creating a project artifact."""
    name: str
    type: ArtifactType
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    # Content handling is done separately via file upload


class ArtifactResponse(BaseModel):
    """Response model for artifact details."""
    id: UUID
    project_id: UUID
    name: str
    type: ArtifactType
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    size_bytes: int
    artifact_metadata: Dict[str, Any] = Field(default_factory=dict)


class ArtifactListResponse(BaseModel):
    """Response model for listing project artifacts."""
    artifacts: List[ArtifactResponse]
    total: int
    total_size_bytes: int


class AnalyticsType(str, Enum):
    """Types of analytics that can be generated for projects."""
    PROGRESS = "progress"
    RESOURCES = "resources"
    PERFORMANCE = "performance"
    TIMELINE = "timeline"
    COST = "cost"
    QUALITY = "quality"


class AnalyticsRequest(BaseModel):
    """Request model for generating project analytics."""
    analytics_type: AnalyticsType
    parameters: Optional[Dict[str, Any]] = None
    time_range: Optional[Dict[str, datetime]] = None


class AnalyticsResponse(BaseModel):
    """Response model for project analytics."""
    analytics_type: AnalyticsType
    generated_at: datetime
    data: Dict[str, Any]
    visualizations: Optional[List[Dict[str, Any]]] = None


class ProjectPlanningMetadata(BaseModel):
    """Metadata for strategic and tactical plans."""
    strategic_plan: Optional[Dict[str, Any]] = None
    tactical_plan: Optional[Dict[str, Any]] = None
    agents: Optional[List[Dict[str, Any]]] = None
    task_assignments: Optional[List[Dict[str, Any]]] = None


class ProjectWithAllDetails(ProjectResponse):
    """Project response with all associated details."""
    state_history: List[ProjectStateHistoryResponse] = []
    current_progress: Optional[ProjectProgressResponse] = None
    resources: List[ResourceResponse] = []
    artifacts: List[ArtifactResponse] = []
    planning: Optional[ProjectPlanningMetadata] = None


# Agent Instructions Models

class AgentRole(str, Enum):
    """Enum for agent roles."""
    COORDINATOR = "coordinator"
    ASSISTANT = "assistant"
    RESEARCHER = "researcher"
    DEVELOPER = "developer"
    TESTER = "tester"
    REVIEWER = "reviewer"
    CUSTOM = "custom"


class AgentCapabilityRequest(BaseModel):
    """Request model for agent capability."""
    capability_name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None


class AgentKnowledgeDomainRequest(BaseModel):
    """Request model for agent knowledge domain."""
    domain_name: str
    priority_level: int = 1
    description: str


class AgentInstructionsRequest(BaseModel):
    """Request model for creating agent instructions."""
    agent_name: str
    purpose: str
    capabilities: Dict[str, Any]
    tone_guidelines: str
    knowledge_domains: Dict[str, Any]
    response_templates: Optional[Dict[str, Any]] = None


class AgentCapabilityResponse(BaseModel):
    """Response model for agent capability."""
    id: UUID
    capability_name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class AgentKnowledgeDomainResponse(BaseModel):
    """Response model for agent knowledge domain."""
    id: UUID
    domain_name: str
    priority_level: int
    description: str


class AgentInstructionsResponse(BaseModel):
    """Response model for agent instructions."""
    id: UUID
    agent_name: str
    purpose: str
    capabilities: Dict[str, Any]
    tone_guidelines: str
    knowledge_domains: Dict[str, Any]
    response_templates: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    capabilities_list: List[AgentCapabilityResponse] = []
    knowledge_domains_list: List[AgentKnowledgeDomainResponse] = []


# Chat Models

class ChatMessageRequest(BaseModel):
    """Request model for chat message."""
    role: str
    content: str
    timestamp: str


class ChatRequest(BaseModel):
    """Request model for chat."""
    message: str
    session_id: str
    user_id: Optional[str] = None
    history: Optional[List[ChatMessageRequest]] = None


class ChatActionData(BaseModel):
    """Model for chat action data."""
    type: str
    data: Dict[str, Any]


class ChatResponse(BaseModel):
    """Response model for chat."""
    response: str
    actions: Optional[List[ChatActionData]] = None


class ChatMessageResponse(BaseModel):
    """Response model for chat message."""
    id: UUID
    role: str
    content: str
    timestamp: datetime
    message_metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatSessionResponse(BaseModel):
    """Response model for chat session."""
    id: str
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    session_metadata: Dict[str, Any] = Field(default_factory=dict)
    messages: List[ChatMessageResponse] = []


class AgentList(BaseModel):
    """
    Paginated list of agents.
    
    This class is added for compatibility with the model registry.
    """
    items: List[Any] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
