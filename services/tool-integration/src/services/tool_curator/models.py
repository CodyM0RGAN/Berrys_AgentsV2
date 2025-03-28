"""
Internal models for the Tool Curator component.

These models define the data structures used internally by the Tool Curator
for tool discovery, evaluation, and recommendation.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class ToolMatchScore(BaseModel):
    """Score for a tool match against requirements."""
    tool_id: UUID = Field(..., description="ID of the tool")
    requirement_id: UUID = Field(..., description="ID of the requirement")
    score: float = Field(..., ge=0.0, le=1.0, description="Match score (0-1)")
    match_details: Dict[str, Any] = Field(default_factory=dict, description="Details about the match")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the match")


class ToolRecommendation(BaseModel):
    """Recommendation for a tool based on requirements."""
    tool_id: UUID = Field(..., description="ID of the tool")
    requirement_id: UUID = Field(..., description="ID of the requirement")
    score: float = Field(..., ge=0.0, le=1.0, description="Recommendation score (0-1)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the recommendation (0-1)")
    reasoning: str = Field(..., description="Reasoning for the recommendation")
    alternatives: List[UUID] = Field(default_factory=list, description="Alternative tool IDs")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the recommendation")


class ToolVersionStatus(str, Enum):
    """Status of a tool version."""
    CURRENT = "CURRENT"
    DEPRECATED = "DEPRECATED"
    BETA = "BETA"
    ALPHA = "ALPHA"
    ARCHIVED = "ARCHIVED"


class ToolVersion(BaseModel):
    """Version information for a tool."""
    tool_id: UUID = Field(..., description="ID of the tool")
    version_number: str = Field(..., description="Version number (semantic versioning)")
    status: ToolVersionStatus = Field(ToolVersionStatus.CURRENT, description="Status of this version")
    release_notes: Optional[str] = Field(None, description="Release notes for this version")
    changes: List[str] = Field(default_factory=list, description="List of changes in this version")
    compatibility: Dict[str, Any] = Field(default_factory=dict, description="Compatibility information")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    created_by: Optional[str] = Field(None, description="Creator identifier")


class ToolCapabilityMatch(BaseModel):
    """Match between a tool capability and a requirement."""
    tool_id: UUID = Field(..., description="ID of the tool")
    capability: str = Field(..., description="Tool capability")
    requirement: str = Field(..., description="Requirement to match")
    score: float = Field(..., ge=0.0, le=1.0, description="Match score (0-1)")
    match_type: str = Field(..., description="Type of match (exact, semantic, partial)")
    details: Dict[str, Any] = Field(default_factory=dict, description="Match details")


class ToolCompatibilityResult(BaseModel):
    """Result of a tool compatibility check."""
    tool_id: UUID = Field(..., description="ID of the tool")
    compatible: bool = Field(..., description="Whether the tool is compatible")
    compatibility_score: float = Field(..., ge=0.0, le=1.0, description="Compatibility score (0-1)")
    incompatibilities: List[str] = Field(default_factory=list, description="List of incompatibilities")
    requirements: Dict[str, Any] = Field(default_factory=dict, description="Requirements for compatibility")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for compatibility")


class ToolCurationResult(BaseModel):
    """Result of a tool curation operation."""
    tool_id: UUID = Field(..., description="ID of the tool")
    operation: str = Field(..., description="Curation operation performed")
    success: bool = Field(..., description="Whether the operation was successful")
    details: Dict[str, Any] = Field(default_factory=dict, description="Operation details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the operation")
    performed_by: Optional[str] = Field(None, description="Identifier of who performed the operation")


class ToolUsageStatistics(BaseModel):
    """Usage statistics for a tool."""
    tool_id: UUID = Field(..., description="ID of the tool")
    total_executions: int = Field(0, description="Total number of executions")
    successful_executions: int = Field(0, description="Number of successful executions")
    failed_executions: int = Field(0, description="Number of failed executions")
    average_execution_time_ms: Optional[float] = Field(None, description="Average execution time in milliseconds")
    last_execution_time: Optional[datetime] = Field(None, description="Timestamp of the last execution")
    usage_by_agent: Dict[str, int] = Field(default_factory=dict, description="Usage count by agent ID")
    usage_trend: List[Dict[str, Any]] = Field(default_factory=list, description="Usage trend over time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
