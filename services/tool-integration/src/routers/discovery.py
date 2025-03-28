"""
Discovery router for the Tool Integration service.

This module defines the FastAPI routes for tool discovery operations,
allowing clients to discover, register, and evaluate external tools.
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status

from ..dependencies import get_tool_service
from ..models.api import (
    ToolDiscoveryRequest,
    DiscoveryResponse,
    DiscoveryFilterParams,
    ToolSummary,
    PaginatedResponse,
    PaginationParams
)
from ..services.tool_service import ToolService
from ..exceptions import ToolDiscoveryError, ToolRegistrationError

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=DiscoveryResponse)
async def discover_tools(
    discovery_request: ToolDiscoveryRequest,
    service: ToolService = Depends(get_tool_service)
):
    """
    Submit a tool discovery request.
    
    Args:
        discovery_request: Discovery request parameters
        service: Tool service
        
    Returns:
        DiscoveryResponse: Discovery response with discovered tools
        
    Raises:
        HTTPException: If discovery fails
    """
    logger.info(f"Discovering tools for project: {discovery_request.project_id}")
    try:
        return await service.discover_tools(discovery_request)
    except ToolDiscoveryError as e:
        logger.error(f"Tool discovery error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool discovery failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error discovering tools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error discovering tools: {str(e)}"
        )

@router.get("/requests/{discovery_id}", response_model=DiscoveryResponse)
async def get_discovery_results(
    discovery_id: UUID = Path(..., description="Discovery request ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Get results of a previous discovery request.
    
    Args:
        discovery_id: Discovery request ID
        service: Tool service
        
    Returns:
        DiscoveryResponse: Discovery results
        
    Raises:
        HTTPException: If discovery request not found
    """
    logger.info(f"Getting discovery results: {discovery_id}")
    try:
        return await service.get_discovery_results(discovery_id)
    except ToolDiscoveryError as e:
        logger.error(f"Tool discovery error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discovery request not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting discovery results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting discovery results: {str(e)}"
        )

@router.get("/requests", response_model=PaginatedResponse)
async def list_discovery_requests(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    pagination: PaginationParams = Depends(),
    service: ToolService = Depends(get_tool_service)
):
    """
    List discovery requests with filtering and pagination.
    
    Args:
        project_id: Optional project ID filter
        status: Optional status filter
        pagination: Pagination parameters
        service: Tool service
        
    Returns:
        PaginatedResponse: Paginated list of discovery requests
        
    Raises:
        HTTPException: If listing discovery requests fails
    """
    logger.info(f"Listing discovery requests (project_id={project_id}, status={status})")
    try:
        return await service.list_discovery_requests(
            project_id=project_id,
            status=status,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except Exception as e:
        logger.error(f"Error listing discovery requests: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing discovery requests: {str(e)}"
        )

@router.post("/register/{discovery_id}", response_model=List[ToolSummary])
async def register_discovered_tools(
    discovery_id: UUID = Path(..., description="Discovery request ID"),
    tool_indices: List[int] = Query(None, description="Indices of tools to register"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Register tools from a discovery request.
    
    Args:
        discovery_id: Discovery request ID
        tool_indices: Indices of tools to register (all if not specified)
        service: Tool service
        
    Returns:
        List[ToolSummary]: Registered tools
        
    Raises:
        HTTPException: If registration fails
    """
    logger.info(f"Registering discovered tools: {discovery_id}")
    try:
        return await service.register_discovered_tools(discovery_id, tool_indices)
    except ToolDiscoveryError as e:
        logger.error(f"Tool discovery error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discovery request not found: {str(e)}"
        )
    except ToolRegistrationError as e:
        logger.error(f"Tool registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool registration failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error registering discovered tools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering discovered tools: {str(e)}"
        )

@router.post("/sources/{source}", response_model=DiscoveryResponse)
async def discover_from_source(
    source: str = Path(..., description="Tool source to discover from"),
    filter_params: DiscoveryFilterParams = Depends(),
    service: ToolService = Depends(get_tool_service)
):
    """
    Discover tools from a specific source.
    
    Args:
        source: Tool source (e.g., "MCP", "EXTERNAL_API")
        filter_params: Discovery filter parameters
        service: Tool service
        
    Returns:
        DiscoveryResponse: Discovery response with discovered tools
        
    Raises:
        HTTPException: If discovery fails
    """
    logger.info(f"Discovering tools from source: {source}")
    try:
        return await service.discover_from_source(
            source,
            capability=filter_params.capability,
            integration_type=filter_params.integration_type,
            min_score=filter_params.min_score
        )
    except ToolDiscoveryError as e:
        logger.error(f"Tool discovery error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool discovery failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error discovering tools from source: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error discovering tools from source: {str(e)}"
        )

@router.delete("/requests/{discovery_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_discovery_request(
    discovery_id: UUID = Path(..., description="Discovery request ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Delete a discovery request.
    
    Args:
        discovery_id: Discovery request ID
        service: Tool service
        
    Raises:
        HTTPException: If discovery request not found or deletion fails
    """
    logger.info(f"Deleting discovery request: {discovery_id}")
    try:
        await service.delete_discovery_request(discovery_id)
    except ToolDiscoveryError as e:
        logger.error(f"Tool discovery error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discovery request not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error deleting discovery request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting discovery request: {str(e)}"
        )
