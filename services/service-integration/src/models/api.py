"""
API models for the Service Integration service.

These models are used for API request/response validation and serialization.
"""
from enum import Enum
from pydantic import Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid
from shared.models.src.base import BaseModel, BaseEntityModel, BaseTimestampModel
from shared.models.src.api.responses import create_data_response_model, create_list_response_model
from shared.models.src.enums import (
    ServiceStatus, ServiceType, WorkflowStatus, WorkflowType
)


class ServiceEndpoint(BaseModel):
    """Definition of a service endpoint."""
    path: str
    method: str
    description: str
    required_permissions: List[str] = []


class ServiceRegistrationRequest(BaseModel):
    """Request model for service registration."""
    service_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: ServiceType
    version: str
    base_url: str
    health_check_url: str
    endpoints: List[ServiceEndpoint] = []
    metadata: Dict[str, Any] = {}
    
    # Validator to handle case-insensitive string values for type
    @validator('type', pre=True)
    def validate_type(cls, v):
        if isinstance(v, str):
            try:
                return ServiceType[v.upper()]
            except KeyError:
                # Check if it matches any enum value
                for enum_item in ServiceType:
                    if v.upper() == enum_item.value:
                        return enum_item
                raise ValueError(f"Invalid service type: {v}")
        return v


class ServiceInfo(ServiceRegistrationRequest):
    """Information about a registered service."""
    status: ServiceStatus = ServiceStatus.ONLINE
    last_heartbeat: datetime = Field(default_factory=datetime.now)
    registered_at: datetime = Field(default_factory=datetime.now)
    
    # Validator to handle case-insensitive string values for status
    @validator('status', pre=True)
    def validate_status(cls, v):
        if isinstance(v, str):
            try:
                return ServiceStatus[v.upper()]
            except KeyError:
                # Check if it matches any enum value
                for enum_item in ServiceStatus:
                    if v.upper() == enum_item.value:
                        return enum_item
                raise ValueError(f"Invalid service status: {v}")
        return v


class ServiceHeartbeatRequest(BaseModel):
    """Request model for service heartbeat."""
    service_id: str
    status: Optional[ServiceStatus] = None
    
    # Validator to handle case-insensitive string values for status
    @validator('status', pre=True)
    def validate_status(cls, v):
        if isinstance(v, str):
            try:
                return ServiceStatus[v.upper()]
            except KeyError:
                # Check if it matches any enum value
                for enum_item in ServiceStatus:
                    if v.upper() == enum_item.value:
                        return enum_item
                raise ValueError(f"Invalid service status: {v}")
        return v


class ServiceDiscoveryRequest(BaseModel):
    """Request model for service discovery."""
    service_type: Optional[ServiceType] = None
    include_offline: bool = False
    
    # Validator to handle case-insensitive string values for service_type
    @validator('service_type', pre=True)
    def validate_service_type(cls, v):
        if isinstance(v, str):
            try:
                return ServiceType[v.upper()]
            except KeyError:
                # Check if it matches any enum value
                for enum_item in ServiceType:
                    if v.upper() == enum_item.value:
                        return enum_item
                raise ValueError(f"Invalid service type: {v}")
        return v


# Create response models using shared utilities
ServiceInfoResponse = create_data_response_model(ServiceInfo)
ServiceDiscoveryResponse = create_list_response_model(ServiceInfo)


class ServiceHealthCheckResponse(BaseEntityModel):
    """Response model for service health check."""
    service_id: str
    status: ServiceStatus
    last_heartbeat: datetime
    response_time_ms: float
    
    # Validator to handle case-insensitive string values for status
    @validator('status', pre=True)
    def validate_status(cls, v):
        if isinstance(v, str):
            try:
                return ServiceStatus[v.upper()]
            except KeyError:
                # Check if it matches any enum value
                for enum_item in ServiceStatus:
                    if v.upper() == enum_item.value:
                        return enum_item
                raise ValueError(f"Invalid service status: {v}")
        return v


class WorkflowRequest(BaseModel):
    """Request model for workflow execution."""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_type: WorkflowType
    data: Dict[str, Any]
    options: Dict[str, Any] = {}
    
    # Validator to handle case-insensitive string values for workflow_type
    @validator('workflow_type', pre=True)
    def validate_workflow_type(cls, v):
        if isinstance(v, str):
            try:
                return WorkflowType[v.upper()]
            except KeyError:
                # Check if it matches any enum value
                for enum_item in WorkflowType:
                    if v.upper() == enum_item.value:
                        return enum_item
                raise ValueError(f"Invalid workflow type: {v}")
        return v


class WorkflowResponseData(BaseEntityModel):
    """Data model for workflow execution response."""
    workflow_id: str
    status: WorkflowStatus
    execution_time: float
    result: Optional[Dict[str, Any]] = None
    errors: List[str] = []
    
    # Validator to handle case-insensitive string values for status
    @validator('status', pre=True)
    def validate_status(cls, v):
        if isinstance(v, str):
            try:
                return WorkflowStatus[v.upper()]
            except KeyError:
                # Check if it matches any enum value
                for enum_item in WorkflowStatus:
                    if v.upper() == enum_item.value:
                        return enum_item
                raise ValueError(f"Invalid workflow status: {v}")
        return v

# Create response model using shared utilities
WorkflowResponse = create_data_response_model(WorkflowResponseData)


# Define CircuitBreakerState enum since it's not in shared enums
class CircuitBreakerState(str, Enum):
    """States of a circuit breaker."""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerStatus(BaseEntityModel):
    """Status of a circuit breaker."""
    service_id: str
    state: CircuitBreakerState
    failure_count: int
    last_failure_time: Optional[datetime] = None
    half_open_call_count: int
    
    # Validator to handle case-insensitive string values for state
    @validator('state', pre=True)
    def validate_state(cls, v):
        if isinstance(v, str):
            try:
                return CircuitBreakerState[v.upper()]
            except KeyError:
                # Check if it matches any enum value
                for enum_item in CircuitBreakerState:
                    if v.upper() == enum_item.value:
                        return enum_item
                raise ValueError(f"Invalid circuit breaker state: {v}")
        return v


class SystemHealthResponse(BaseModel):
    """Response model for system health check."""
    status: str
    service_statuses: Dict[str, ServiceStatus]
    circuit_breaker_statuses: Dict[str, CircuitBreakerStatus]
    execution_time_ms: float


class AgentExecutionStep(BaseEntityModel):
    """A step in an agent execution plan."""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    depends_on: List[str] = []
    parameters: Dict[str, Any] = {}
    requires_human_approval: bool = False


class AgentExecutionPlan(BaseEntityModel, BaseTimestampModel):
    """Execution plan for an agent task."""
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    agent_id: str
    steps: List[AgentExecutionStep]
    created_at: datetime = Field(default_factory=datetime.now)


class ToolExecution(BaseEntityModel):
    """Tool execution information."""
    tool_id: str
    name: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    status: str = "PENDING"


class AgentTask(BaseEntityModel, BaseTimestampModel):
    """Agent task information."""
    task_id: str
    agent_id: str
    description: str
    parameters: Dict[str, Any] = {}
    status: str
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]] = None
