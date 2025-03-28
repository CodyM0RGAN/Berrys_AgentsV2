"""
API routes for Tool Curator functionality.

This module defines the API endpoints for the Tool Curator component,
providing routes for tool recommendation, evaluation, versioning, and curation.
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from pydantic import BaseModel, Field

from shared.models.src.tool import (
    ToolRequirement,
    ToolStatus,
)

from ..dependencies import get_tool_service
from ..services.tool_service import ToolService
from ..services.tool_curator.models import (
    ToolVersionStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/curator",
    tags=["tool-curator"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)


# Request/Response models

class ToolRecommendationRequest(BaseModel):
    """Request model for tool recommendations."""
    requirements: List[ToolRequirement] = Field(..., description="List of tool requirements")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional recommendation context")
    min_score: float = Field(0.5, description="Minimum score for a tool to be recommended")
    max_recommendations: int = Field(5, description="Maximum number of recommendations per requirement")


class ToolCurationRequest(BaseModel):
    """Request model for tool curation."""
    agent_id: UUID = Field(..., description="ID of the agent")
    requirements: List[ToolRequirement] = Field(..., description="List of tool requirements")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional curation context")


class ToolVersionRequest(BaseModel):
    """Request model for tracking tool versions."""
    version_number: str = Field(..., description="Version number (semantic versioning)")
    release_notes: Optional[str] = Field(None, description="Optional release notes")
    changes: Optional[List[str]] = Field(None, description="Optional list of changes")
    compatibility: Optional[Dict[str, Any]] = Field(None, description="Optional compatibility information")
    created_by: Optional[str] = Field(None, description="Optional creator identifier")


class ToolCompatibilityRequest(BaseModel):
    """Request model for checking tool compatibility."""
    version1: str = Field(..., description="First version string")
    version2: str = Field(..., description="Second version string")


class ToolCapabilityEvaluationRequest(BaseModel):
    """Request model for evaluating tool capabilities."""
    requirements: List[str] = Field(..., description="List of requirements to evaluate against")


class ToolCurationOperationRequest(BaseModel):
    """Request model for performing curation operations."""
    operation: str = Field(..., description="Curation operation to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Optional operation parameters")
    performed_by: Optional[str] = Field(None, description="Optional identifier of who performed the operation")


# API Routes

@router.post("/recommendations", response_model=Dict[str, List[Dict[str, Any]]])
async def recommend_tools(
    request: ToolRecommendationRequest,
    tool_service: ToolService = Depends(get_tool_service),
):
    """
    Recommend tools for the given requirements.
    
    Returns a dictionary mapping requirement IDs to lists of tool recommendations.
    """
    try:
        recommendations = await tool_service.recommend_tools_for_requirements(
            request.requirements,
            request.context,
            request.min_score,
            request.max_recommendations,
        )
        return recommendations
    except Exception as e:
        logger.error(f"Error recommending tools: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error recommending tools: {str(e)}")


@router.post("/curate", response_model=List[Dict[str, Any]])
async def curate_tools_for_agent(
    request: ToolCurationRequest,
    tool_service: ToolService = Depends(get_tool_service),
):
    """
    Curate a set of tools for an agent based on requirements.
    
    This is a high-level endpoint that combines discovery, evaluation, and recommendation
    to provide a comprehensive tool curation solution.
    """
    try:
        recommendations = await tool_service.curate_tools_for_agent(
            request.agent_id,
            request.requirements,
            request.context,
        )
        return recommendations
    except Exception as e:
        logger.error(f"Error curating tools for agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error curating tools for agent: {str(e)}")


@router.post("/tools/{tool_id}/versions", response_model=Dict[str, Any])
async def track_tool_version(
    tool_id: UUID = Path(..., description="ID of the tool"),
    request: ToolVersionRequest = Body(...),
    tool_service: ToolService = Depends(get_tool_service),
):
    """
    Track a new version of a tool.
    """
    try:
        version = await tool_service.track_tool_version(
            tool_id,
            request.version_number,
            request.release_notes,
            request.changes,
            request.compatibility,
            request.created_by,
        )
        return version
    except ValueError as e:
        logger.error(f"Invalid version data: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid version data: {str(e)}")
    except Exception as e:
        logger.error(f"Error tracking tool version: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error tracking tool version: {str(e)}")


@router.post("/tools/{tool_id}/compatibility", response_model=Dict[str, Any])
async def check_tool_compatibility(
    tool_id: UUID = Path(..., description="ID of the tool"),
    request: ToolCompatibilityRequest = Body(...),
    tool_service: ToolService = Depends(get_tool_service),
):
    """
    Check compatibility between two versions of a tool.
    """
    try:
        compatibility_info = await tool_service.check_tool_compatibility(
            tool_id,
            request.version1,
            request.version2,
        )
        return compatibility_info
    except ValueError as e:
        logger.error(f"Invalid version data: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid version data: {str(e)}")
    except Exception as e:
        logger.error(f"Error checking tool compatibility: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking tool compatibility: {str(e)}")


@router.get("/tools/{tool_id}/usage", response_model=Dict[str, Any])
async def get_tool_usage_statistics(
    tool_id: UUID = Path(..., description="ID of the tool"),
    tool_service: ToolService = Depends(get_tool_service),
):
    """
    Get usage statistics for a tool.
    """
    try:
        statistics = await tool_service.get_tool_usage_statistics(tool_id)
        return statistics
    except ValueError as e:
        logger.error(f"Tool not found: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Tool not found: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting tool usage statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting tool usage statistics: {str(e)}")


@router.post("/tools/{tool_id}/capabilities", response_model=List[Dict[str, Any]])
async def evaluate_tool_capabilities(
    tool_id: UUID = Path(..., description="ID of the tool"),
    request: ToolCapabilityEvaluationRequest = Body(...),
    tool_service: ToolService = Depends(get_tool_service),
):
    """
    Evaluate a tool's capabilities against requirements.
    """
    try:
        capability_matches = await tool_service.evaluate_tool_capabilities(
            tool_id,
            request.requirements,
        )
        return capability_matches
    except ValueError as e:
        logger.error(f"Tool not found: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Tool not found: {str(e)}")
    except Exception as e:
        logger.error(f"Error evaluating tool capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error evaluating tool capabilities: {str(e)}")


@router.post("/tools/{tool_id}/operations", response_model=Dict[str, Any])
async def perform_curation_operation(
    tool_id: UUID = Path(..., description="ID of the tool"),
    request: ToolCurationOperationRequest = Body(...),
    tool_service: ToolService = Depends(get_tool_service),
):
    """
    Perform a curation operation on a tool.
    
    Available operations:
    - approve: Approve the tool
    - deprecate: Deprecate the tool
    - update_version: Update the tool version
    - evaluate: Evaluate the tool against requirements
    """
    try:
        result = await tool_service.perform_curation_operation(
            tool_id,
            request.operation,
            request.parameters,
            request.performed_by,
        )
        return result
    except ValueError as e:
        logger.error(f"Invalid operation: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid operation: {str(e)}")
    except Exception as e:
        logger.error(f"Error performing curation operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error performing curation operation: {str(e)}")
