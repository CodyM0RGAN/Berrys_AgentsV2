from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    PROJECT = "PROJECT"
    AGENT = "AGENT"
    TASK = "TASK"
    TOOL = "TOOL"
    MODEL = "MODEL"
    USER = "USER"
    SYSTEM = "SYSTEM"


class ActionType(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    EXECUTE = "EXECUTE"
    ASSIGN = "ASSIGN"
    COMPLETE = "COMPLETE"
    FAIL = "FAIL"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"


class OptimizationStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IMPLEMENTED = "IMPLEMENTED"
    FAILED = "FAILED"


class OptimizationCategory(str, Enum):
    PROMPT_ENGINEERING = "PROMPT_ENGINEERING"
    MODEL_SELECTION = "MODEL_SELECTION"
    AGENT_CONFIGURATION = "AGENT_CONFIGURATION"
    TOOL_INTEGRATION = "TOOL_INTEGRATION"
    WORKFLOW_OPTIMIZATION = "WORKFLOW_OPTIMIZATION"
    RESOURCE_ALLOCATION = "RESOURCE_ALLOCATION"
    COST_REDUCTION = "COST_REDUCTION"
    PERFORMANCE_IMPROVEMENT = "PERFORMANCE_IMPROVEMENT"
    ERROR_PREVENTION = "ERROR_PREVENTION"
    SECURITY_ENHANCEMENT = "SECURITY_ENHANCEMENT"


class AuditLog(BaseModel):
    """Model for audit logs."""
    id: UUID = Field(default_factory=uuid4)
    entity_id: UUID
    entity_type: EntityType
    action: ActionType
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    actor_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "from_attributes": True,
        "protected_namespaces": ()
    }


class PerformanceMetric(BaseModel):
    """Model for performance metrics."""
    id: UUID = Field(default_factory=uuid4)
    entity_id: UUID
    entity_type: EntityType
    metric_name: str
    metric_value: float
    context: Optional[Dict[str, Any]] = None
    recorded_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "from_attributes": True,
        "protected_namespaces": ()
    }


class OptimizationSuggestion(BaseModel):
    """Model for optimization suggestions."""
    id: UUID = Field(default_factory=uuid4)
    category: OptimizationCategory
    description: str
    evidence: Dict[str, Any]
    status: OptimizationStatus = OptimizationStatus.PENDING
    impact_score: float  # 0.0 to 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "from_attributes": True,
        "protected_namespaces": ()
    }


class OptimizationImplementation(BaseModel):
    """Model for implemented optimizations."""
    suggestion_id: UUID
    implementation_details: Dict[str, Any]
    implemented_by: Optional[UUID] = None
    implemented_at: datetime = Field(default_factory=datetime.utcnow)
    result_metrics: Optional[Dict[str, Any]] = None
    success: bool = True


class AuditQuery(BaseModel):
    """Model for querying audit logs."""
    entity_id: Optional[UUID] = None
    entity_type: Optional[EntityType] = None
    action: Optional[ActionType] = None
    actor_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


class MetricQuery(BaseModel):
    """Model for querying performance metrics."""
    entity_id: Optional[UUID] = None
    entity_type: Optional[EntityType] = None
    metric_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


class OptimizationQuery(BaseModel):
    """Model for querying optimization suggestions."""
    category: Optional[OptimizationCategory] = None
    status: Optional[OptimizationStatus] = None
    min_impact_score: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


class AuditSummary(BaseModel):
    """Model for audit summary statistics."""
    total_actions: int
    actions_by_type: Dict[ActionType, int]
    actions_by_entity: Dict[EntityType, int]
    actions_by_day: Dict[str, int]  # ISO date string -> count
    top_actors: List[Dict[str, Any]]


class PerformanceSummary(BaseModel):
    """Model for performance summary statistics."""
    metrics_by_name: Dict[str, Dict[str, Any]]  # metric_name -> {avg, min, max, count}
    metrics_by_entity_type: Dict[EntityType, Dict[str, Any]]
    metrics_over_time: Dict[str, List[Dict[str, Any]]]  # metric_name -> [{date, value}]
    anomalies: List[Dict[str, Any]]
