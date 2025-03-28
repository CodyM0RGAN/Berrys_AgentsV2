from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, HttpUrl


class ToolSource(str, Enum):
    BUILT_IN = "BUILT_IN"
    DISCOVERED = "DISCOVERED"
    USER_DEFINED = "USER_DEFINED"
    MCP = "MCP"
    EXTERNAL_API = "EXTERNAL_API"
    CUSTOM = "CUSTOM"


class ToolStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    EVALUATING = "EVALUATING"
    APPROVED = "APPROVED"
    INTEGRATED = "INTEGRATED"
    DEPRECATED = "DEPRECATED"
    REJECTED = "REJECTED"


class IntegrationType(str, Enum):
    API = "API"
    LIBRARY = "LIBRARY"
    CLI = "CLI"
    MCP = "MCP"
    CUSTOM = "CUSTOM"


class ToolBase(BaseModel):
    """Base model for Tool with common attributes."""
    name: str
    description: Optional[str] = None
    capability: str
    source: ToolSource
    documentation_url: Optional[str] = None
    tool_schema: Optional[Dict[str, Any]] = None
    integration_type: Optional[IntegrationType] = None


class ToolCreate(ToolBase):
    """Model for creating a new Tool."""
    pass


class ToolUpdate(BaseModel):
    """Model for updating an existing Tool."""
    name: Optional[str] = None
    description: Optional[str] = None
    documentation_url: Optional[str] = None
    tool_schema: Optional[Dict[str, Any]] = None
    integration_type: Optional[IntegrationType] = None
    status: Optional[ToolStatus] = None


class ToolInDB(ToolBase):
    """Model for Tool as stored in the database."""
    id: UUID = Field(default_factory=uuid4)
    status: ToolStatus = ToolStatus.DISCOVERED
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Tool(ToolInDB):
    """Complete Tool model with all attributes."""
    pass


class ToolSummary(BaseModel):
    """Simplified Tool model for list views."""
    id: UUID
    name: str
    capability: str
    source: ToolSource
    status: ToolStatus

    class Config:
        from_attributes = True


class AgentTool(BaseModel):
    """Model for Tool as configured for a specific Agent."""
    tool_id: UUID
    agent_id: UUID
    configuration: Dict[str, Any] = Field(default_factory=dict)


class ToolRequirement(BaseModel):
    """Model for specifying tool requirements during discovery."""
    capability: str
    description: str
    priority: int = 3  # 1-5, 5 being highest


class ToolDiscoveryRequest(BaseModel):
    """Model for requesting tool discovery."""
    project_id: UUID
    requirements: List[ToolRequirement]
    context: Optional[Dict[str, Any]] = None


class ToolEvaluationResult(BaseModel):
    """Model for tool evaluation results."""
    tool_id: UUID
    score: float  # 0.0 to 1.0
    strengths: List[str]
    weaknesses: List[str]
    recommendation: str
    evaluation_details: Dict[str, Any]
