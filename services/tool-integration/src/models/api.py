from enum import Enum
from pydantic import Field, validator
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from datetime import datetime

from shared.models.src.enums import ToolStatus, ToolCategory, ExecutionStatus
from shared.models.src.api.responses import StandardResponse, PaginatedResponse
from shared.models.src.base import APIModel

class PaginationParams(APIModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Items per page")

class ToolBase(APIModel):
    name: str = Field(..., description="Name of the tool")
    description: Optional[str] = Field(None, description="Description of the tool")
    status: ToolStatus = Field(ToolStatus.ACTIVE, description="Status of the tool")
    category_id: UUID = Field(..., description="ID of the tool category")
    version_number: str = Field(..., description="Version number of the tool")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Tool configuration")
    is_enabled: bool = Field(True, description="Whether the tool is enabled")

class ToolCreate(ToolBase):
    pass

class ToolUpdate(APIModel):
    name: Optional[str] = Field(None, description="Name of the tool")
    description: Optional[str] = Field(None, description="Description of the tool")
    status: Optional[ToolStatus] = Field(None, description="Status of the tool")
    category_id: Optional[UUID] = Field(None, description="ID of the tool category")
    version_number: Optional[str] = Field(None, description="Version number of the tool")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Tool configuration")
    is_enabled: Optional[bool] = Field(None, description="Whether the tool is enabled")

class ToolResponse(ToolBase):
    id: UUID = Field(..., description="ID of the tool")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    version: int = Field(..., description="Version number for optimistic locking")

# Alias for backward compatibility
Tool = ToolResponse

class ToolSummary(APIModel):
    """Summary information about a tool."""
    id: Optional[UUID] = Field(None, description="ID of the tool (may be None for discovered tools)")
    name: str = Field(..., description="Name of the tool")
    capability: str = Field(..., description="Primary capability of the tool")
    source: str = Field(..., description="Source of the tool")
    integration_type: Optional[str] = Field(None, description="Type of integration")
    status: ToolStatus = Field(..., description="Status of the tool")
    security_score: Optional[float] = Field(None, description="Security evaluation score (0-1)")
    overall_score: Optional[float] = Field(None, description="Overall evaluation score (0-1)")

class ToolCategoryBase(APIModel):
    name: str = Field(..., description="Name of the category")
    description: Optional[str] = Field(None, description="Description of the category")
    type: ToolCategory = Field(ToolCategory.UTILITY, description="Type of the category")

class ToolCategoryCreate(ToolCategoryBase):
    pass

class ToolCategoryUpdate(APIModel):
    name: Optional[str] = Field(None, description="Name of the category")
    description: Optional[str] = Field(None, description="Description of the category")
    type: Optional[ToolCategory] = Field(None, description="Type of the category")

class ToolCategoryResponse(ToolCategoryBase):
    id: UUID = Field(..., description="ID of the category")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    version: int = Field(..., description="Version number for optimistic locking")

class ToolExecutionBase(APIModel):
    tool_id: UUID = Field(..., description="ID of the tool")
    agent_id: UUID = Field(..., description="ID of the agent")
    project_id: UUID = Field(..., description="ID of the project")
    status: ExecutionStatus = Field(ExecutionStatus.PENDING, description="Status of the execution")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Execution parameters")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    error_message: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time: Optional[int] = Field(None, description="Execution time in milliseconds")

class ToolExecutionCreate(ToolExecutionBase):
    pass

class ToolExecutionUpdate(APIModel):
    status: Optional[ExecutionStatus] = Field(None, description="Status of the execution")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    error_message: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time: Optional[int] = Field(None, description="Execution time in milliseconds")

class ToolExecutionResponse(ToolExecutionBase):
    id: UUID = Field(..., description="ID of the execution")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    version: int = Field(..., description="Version number for optimistic locking")

# Enums
class EvaluationCriteriaType(str, Enum):
    """Type of evaluation criteria."""
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    COMPATIBILITY = "COMPATIBILITY"
    USABILITY = "USABILITY"
    RELIABILITY = "RELIABILITY"

class ExecutionMode(str, Enum):
    """Mode of tool execution."""
    SYNCHRONOUS = "SYNCHRONOUS"
    ASYNCHRONOUS = "ASYNCHRONOUS"

# Evaluation models
class SecurityEvaluationResult(APIModel):
    """Security evaluation result."""
    score: float = Field(..., description="Security score (0-1)")
    vulnerabilities: List[Dict[str, Any]] = Field(default_factory=list, description="Detected vulnerabilities")
    risk_level: str = Field(..., description="Risk level assessment")
    recommendations: List[str] = Field(default_factory=list, description="Security recommendations")

class PerformanceEvaluationResult(APIModel):
    """Performance evaluation result."""
    score: float = Field(..., description="Performance score (0-1)")
    latency_ms: int = Field(..., description="Average latency in milliseconds")
    throughput: Optional[float] = Field(None, description="Throughput measurement")
    resource_usage: Dict[str, Any] = Field(default_factory=dict, description="Resource usage metrics")
    recommendations: List[str] = Field(default_factory=list, description="Performance recommendations")

class CompatibilityEvaluationResult(APIModel):
    """Compatibility evaluation result."""
    score: float = Field(..., description="Compatibility score (0-1)")
    compatible_platforms: List[str] = Field(default_factory=list, description="Compatible platforms")
    incompatible_platforms: List[str] = Field(default_factory=list, description="Incompatible platforms")
    dependencies: List[Dict[str, Any]] = Field(default_factory=list, description="Required dependencies")
    recommendations: List[str] = Field(default_factory=list, description="Compatibility recommendations")

class ToolEvaluationResult(APIModel):
    """Result of a tool evaluation."""
    id: UUID = Field(..., description="ID of the evaluation")
    tool_id: UUID = Field(..., description="ID of the evaluated tool")
    evaluation_type: EvaluationCriteriaType = Field(..., description="Type of evaluation")
    score: float = Field(..., description="Evaluation score (0-1)")
    details: Dict[str, Any] = Field(default_factory=dict, description="Evaluation details")
    timestamp: datetime = Field(..., description="Timestamp of the evaluation")
    evaluator: Optional[str] = Field(None, description="Evaluator identifier")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations based on evaluation")

class ComprehensiveEvaluationResult(APIModel):
    """Comprehensive evaluation result including all criteria."""
    tool_id: UUID = Field(..., description="ID of the evaluated tool")
    evaluation_id: UUID = Field(..., description="ID of the evaluation")
    evaluation_timestamp: datetime = Field(..., description="Timestamp of the evaluation")
    overall_score: float = Field(..., description="Overall evaluation score (0-1)")
    security: Optional[SecurityEvaluationResult] = Field(None, description="Security evaluation result")
    performance: Optional[PerformanceEvaluationResult] = Field(None, description="Performance evaluation result")
    compatibility: Optional[CompatibilityEvaluationResult] = Field(None, description="Compatibility evaluation result")
    usability_score: Optional[float] = Field(None, description="Usability score (0-1)")
    reliability_score: Optional[float] = Field(None, description="Reliability score (0-1)")
    recommendation: str = Field(..., description="Overall recommendation")
    context: Optional[Dict[str, Any]] = Field(None, description="Evaluation context")

class EvaluationRequest(APIModel):
    """Request to evaluate a tool."""
    tool_id: UUID = Field(..., description="ID of the tool to evaluate")
    criteria: Dict[EvaluationCriteriaType, bool] = Field(..., description="Evaluation criteria to apply")
    context: Optional[Dict[str, Any]] = Field(None, description="Evaluation context")

class BatchEvaluationRequest(APIModel):
    """Request for batch tool evaluation."""
    evaluations: List[EvaluationRequest] = Field(..., description="Evaluation requests")

# Tool execution models
class ToolExecutionRequest(APIModel):
    """Request to execute a tool."""
    tool_id: UUID = Field(..., description="ID of the tool to execute")
    agent_id: UUID = Field(..., description="ID of the agent requesting execution")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Execution parameters")
    execution_context: Optional[Dict[str, Any]] = Field(None, description="Execution context")
    mode: ExecutionMode = Field(ExecutionMode.SYNCHRONOUS, description="Execution mode")
    timeout_seconds: Optional[int] = Field(None, description="Execution timeout in seconds")
    callback_id: Optional[str] = Field(None, description="Callback ID for asynchronous execution")

class ToolExecutionStatusRequest(APIModel):
    """Request to check the status of a tool execution."""
    execution_id: UUID = Field(..., description="ID of the execution to check")
    include_logs: bool = Field(False, description="Whether to include execution logs in the response")
    log_limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum number of log entries to include")

# Tool integration models
class ToolIntegrationRequest(APIModel):
    """Request to integrate a tool with an agent."""
    tool_id: UUID = Field(..., description="ID of the tool to integrate")
    agent_id: UUID = Field(..., description="ID of the agent")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Integration configuration")
    permissions: List[str] = Field(default_factory=list, description="Requested permissions")

class ToolIntegrationResponse(APIModel):
    """Response for tool integration."""
    id: UUID = Field(..., description="ID of the integration")
    tool_id: UUID = Field(..., description="ID of the tool")
    agent_id: UUID = Field(..., description="ID of the agent")
    configuration: Dict[str, Any] = Field(..., description="Integration configuration")
    permissions: List[str] = Field(..., description="Granted permissions")
    integrated_at: datetime = Field(..., description="Integration timestamp")
    status: str = Field(..., description="Integration status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class ToolIntegrationUpdateRequest(APIModel):
    """Request to update a tool integration."""
    configuration: Optional[Dict[str, Any]] = Field(None, description="Updated configuration")
    permissions: Optional[List[str]] = Field(None, description="Updated permissions")
    status: Optional[str] = Field(None, description="Updated status")

# MCP models
class MCPToolInfo(APIModel):
    """Information about an MCP tool."""
    name: str = Field(..., description="Name of the tool")
    description: Optional[str] = Field(None, description="Description of the tool")
    server_name: str = Field(..., description="Name of the MCP server")
    input_schema: Dict[str, Any] = Field(..., description="Input schema for the tool")
    capabilities: List[str] = Field(default_factory=list, description="Tool capabilities")

class MCPServerInfo(APIModel):
    """Information about an MCP server."""
    name: str = Field(..., description="Name of the server")
    version: str = Field(..., description="Server version")
    description: Optional[str] = Field(None, description="Server description")
    status: str = Field(..., description="Server status")
    tool_count: int = Field(..., description="Number of tools provided by the server")

class MCPToolListResponse(PaginatedResponse):
    """Response for listing MCP tools."""
    items: List[MCPToolInfo]

class MCPServerListResponse(PaginatedResponse):
    """Response for listing MCP servers."""
    items: List[MCPServerInfo]

# Discovery models
class DiscoveryFilterParams(APIModel):
    """Filter parameters for tool discovery."""
    capability: Optional[str] = Field(None, description="Filter by capability")
    integration_type: Optional[str] = Field(None, description="Filter by integration type")
    min_score: float = Field(0.5, ge=0.0, le=1.0, description="Minimum match score")

class ToolDiscoveryRequest(APIModel):
    """Request to discover tools."""
    project_id: UUID = Field(..., description="ID of the project")
    agent_id: Optional[UUID] = Field(None, description="ID of the agent")
    capability_requirements: List[str] = Field(default_factory=list, description="Required capabilities")
    integration_preferences: Optional[List[str]] = Field(None, description="Preferred integration types")
    discovery_context: Optional[Dict[str, Any]] = Field(None, description="Discovery context")
    sources: Optional[List[str]] = Field(None, description="Sources to discover from")
    min_score: float = Field(0.5, ge=0.0, le=1.0, description="Minimum match score")

class DiscoveryResponse(APIModel):
    """Response for tool discovery."""
    request_id: UUID = Field(..., description="ID of the discovery request")
    discovered_tools: List[ToolSummary] = Field(..., description="Discovered tools")
    discovery_timestamp: datetime = Field(..., description="Timestamp of the discovery")
    context: Optional[Dict[str, Any]] = Field(None, description="Discovery context")

# Batch operation requests and responses
class BatchRegistrationRequest(APIModel):
    """Request for batch tool registration."""
    tools: List[ToolCreate] = Field(..., description="Tools to register")

class BatchRegistrationResponse(APIModel):
    """Response for batch tool registration."""
    successful: List[ToolResponse] = Field(..., description="Successfully registered tools")
    failed: List[Dict[str, Any]] = Field(..., description="Failed registrations with errors")

class BatchEvaluationResponse(APIModel):
    """Response for batch tool evaluation."""
    successful: List[Any] = Field(..., description="Successfully evaluated tools")
    failed: List[Dict[str, Any]] = Field(..., description="Failed evaluations with errors")

# Response wrappers
class ToolListResponse(PaginatedResponse):
    items: List[ToolResponse]

class ToolCategoryListResponse(PaginatedResponse):
    items: List[ToolCategoryResponse]

class ToolExecutionListResponse(PaginatedResponse):
    items: List[ToolExecutionResponse]

class ToolStandardResponse(StandardResponse):
    data: Optional[ToolResponse] = None

class ToolCategoryStandardResponse(StandardResponse):
    data: Optional[ToolCategoryResponse] = None

class ToolExecutionStandardResponse(StandardResponse):
    data: Optional[ToolExecutionResponse] = None
