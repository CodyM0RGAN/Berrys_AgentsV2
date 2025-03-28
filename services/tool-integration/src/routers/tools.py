"""
Tools router for the Tool Integration service.

This module defines the FastAPI routes for tool management,
including creating, reading, updating, and deleting tools.
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status

from ..dependencies import get_tool_service
from ..models.api import (
    ToolCreate,
    ToolUpdate,
    Tool,
    ToolSummary,
    PaginatedResponse,
    PaginationParams,
    BatchRegistrationRequest,
    BatchRegistrationResponse
)
from ..services.tool_service import ToolService
from ..exceptions import ToolNotFoundError, ToolValidationError, ToolRegistrationError

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=Tool, status_code=status.HTTP_201_CREATED)
async def create_tool(
    tool_data: ToolCreate,
    service: ToolService = Depends(get_tool_service)
):
    """
    Register a new tool.
    
    Args:
        tool_data: Tool data
        service: Tool service
        
    Returns:
        Tool: Registered tool
        
    Raises:
        HTTPException: If tool registration fails
        ToolValidationError: If tool data is invalid
    """
    logger.info(f"Registering tool: {tool_data.name}")
    try:
        return await service.register_tool(tool_data)
    except ToolValidationError as e:
        logger.error(f"Tool validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tool data: {str(e)}"
        )
    except ToolRegistrationError as e:
        logger.error(f"Tool registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool registration failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error registering tool: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering tool: {str(e)}"
        )

@router.get("/{tool_id}", response_model=Tool)
async def get_tool(
    tool_id: UUID = Path(..., description="Tool ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Get a tool by ID.
    
    Args:
        tool_id: Tool ID
        service: Tool service
        
    Returns:
        Tool: Tool data
        
    Raises:
        HTTPException: If tool not found
    """
    logger.info(f"Getting tool: {tool_id}")
    try:
        return await service.get_tool(tool_id)
    except ToolNotFoundError:
        logger.error(f"Tool not found: {tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool not found: {tool_id}"
        )
    except Exception as e:
        logger.error(f"Error getting tool: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting tool: {str(e)}"
        )

@router.get("/", response_model=PaginatedResponse)
async def list_tools(
    capability: Optional[str] = Query(None, description="Filter by capability"),
    source: Optional[str] = Query(None, description="Filter by source"),
    status: Optional[str] = Query(None, description="Filter by status"),
    integration_type: Optional[str] = Query(None, description="Filter by integration type"),
    pagination: PaginationParams = Depends(),
    service: ToolService = Depends(get_tool_service)
):
    """
    List tools with filtering and pagination.
    
    Args:
        capability: Optional capability filter
        source: Optional source filter
        status: Optional status filter
        integration_type: Optional integration type filter
        pagination: Pagination parameters
        service: Tool service
        
    Returns:
        PaginatedResponse: Paginated list of tools
        
    Raises:
        HTTPException: If listing tools fails
    """
    logger.info(f"Listing tools (capability={capability}, source={source}, status={status})")
    try:
        return await service.list_tools(
            capability=capability,
            source=source,
            status=status,
            integration_type=integration_type,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing tools: {str(e)}"
        )

@router.put("/{tool_id}", response_model=Tool)
async def update_tool(
    tool_data: ToolUpdate,
    tool_id: UUID = Path(..., description="Tool ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Update a tool.
    
    Args:
        tool_data: Tool data to update
        tool_id: Tool ID
        service: Tool service
        
    Returns:
        Tool: Updated tool
        
    Raises:
        HTTPException: If tool not found or update fails
    """
    logger.info(f"Updating tool: {tool_id}")
    try:
        return await service.update_tool(tool_id, tool_data)
    except ToolNotFoundError:
        logger.error(f"Tool not found: {tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool not found: {tool_id}"
        )
    except ToolValidationError as e:
        logger.error(f"Tool validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tool data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error updating tool: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating tool: {str(e)}"
        )

@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: UUID = Path(..., description="Tool ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Delete a tool.
    
    Args:
        tool_id: Tool ID
        service: Tool service
        
    Raises:
        HTTPException: If tool not found or deletion fails
    """
    logger.info(f"Deleting tool: {tool_id}")
    try:
        await service.delete_tool(tool_id)
    except ToolNotFoundError:
        logger.error(f"Tool not found: {tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool not found: {tool_id}"
        )
    except Exception as e:
        logger.error(f"Error deleting tool: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting tool: {str(e)}"
        )

@router.post("/batch", response_model=BatchRegistrationResponse)
async def batch_register_tools(
    batch_request: BatchRegistrationRequest,
    service: ToolService = Depends(get_tool_service)
):
    """
    Register multiple tools in a single batch operation.
    
    Args:
        batch_request: Batch registration request
        service: Tool service
        
    Returns:
        BatchRegistrationResponse: Registration results
        
    Raises:
        HTTPException: If batch registration fails
    """
    logger.info(f"Batch registering {len(batch_request.tools)} tools")
    try:
        return await service.batch_register_tools(batch_request.tools)
    except Exception as e:
        logger.error(f"Error in batch tool registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in batch tool registration: {str(e)}"
        )

@router.get("/search/{capability}", response_model=List[ToolSummary])
async def search_tools_by_capability(
    capability: str = Path(..., description="Capability to search for"),
    min_score: float = Query(0.5, ge=0.0, le=1.0, description="Minimum match score"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Search for tools matching a specific capability.
    
    Args:
        capability: Capability to search for
        min_score: Minimum match score
        limit: Maximum number of results
        service: Tool service
        
    Returns:
        List[ToolSummary]: Matching tools
        
    Raises:
        HTTPException: If search fails
    """
    logger.info(f"Searching for tools with capability: {capability}")
    try:
        return await service.search_tools_by_capability(capability, min_score, limit)
    except Exception as e:
        logger.error(f"Error searching tools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching tools: {str(e)}"
        )

@router.post("/{tool_id}/approve", response_model=Tool)
async def approve_tool(
    tool_id: UUID = Path(..., description="Tool ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Approve a tool for use.
    
    Args:
        tool_id: Tool ID
        service: Tool service
        
    Returns:
        Tool: Approved tool
        
    Raises:
        HTTPException: If tool not found or approval fails
    """
    logger.info(f"Approving tool: {tool_id}")
    try:
        return await service.approve_tool(tool_id)
    except ToolNotFoundError:
        logger.error(f"Tool not found: {tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool not found: {tool_id}"
        )
    except Exception as e:
        logger.error(f"Error approving tool: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error approving tool: {str(e)}"
        )

@router.post("/{tool_id}/deprecate", response_model=Tool)
async def deprecate_tool(
    tool_id: UUID = Path(..., description="Tool ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Deprecate a tool.
    
    Args:
        tool_id: Tool ID
        service: Tool service
        
    Returns:
        Tool: Deprecated tool
        
    Raises:
        HTTPException: If tool not found or deprecation fails
    """
    logger.info(f"Deprecating tool: {tool_id}")
    try:
        return await service.deprecate_tool(tool_id)
    except ToolNotFoundError:
        logger.error(f"Tool not found: {tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool not found: {tool_id}"
        )
    except Exception as e:
        logger.error(f"Error deprecating tool: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deprecating tool: {str(e)}"
        )
