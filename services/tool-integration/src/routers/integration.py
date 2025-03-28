"""
Integration router for the Tool Integration service.

This module defines the FastAPI routes for tool integration operations,
allowing clients to integrate tools with agents and manage their configurations.
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status

from ..dependencies import get_tool_service
from ..models.api import (
    ToolIntegrationRequest,
    ToolIntegrationResponse,
    ToolIntegrationUpdateRequest,
    PaginatedResponse,
    PaginationParams
)
from ..services.tool_service import ToolService
from ..exceptions import ToolNotFoundError, ToolValidationError, SecurityViolationError

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/agents/{agent_id}/tools", response_model=ToolIntegrationResponse, status_code=status.HTTP_201_CREATED)
async def integrate_tool_with_agent(
    integration_request: ToolIntegrationRequest,
    agent_id: UUID = Path(..., description="Agent ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Integrate a tool with an agent.
    
    Args:
        integration_request: Integration request data
        agent_id: Agent ID
        service: Tool service
        
    Returns:
        ToolIntegrationResponse: Integration details
        
    Raises:
        HTTPException: If integration fails
    """
    logger.info(f"Integrating tool {integration_request.tool_id} with agent {agent_id}")
    try:
        integration_request.agent_id = agent_id  # Ensure agent_id in request matches path
        return await service.integrate_tool(integration_request)
    except ToolNotFoundError:
        logger.error(f"Tool not found: {integration_request.tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool not found: {integration_request.tool_id}"
        )
    except SecurityViolationError as e:
        logger.error(f"Security violation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Integration denied due to security concerns: {str(e)}"
        )
    except ToolValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid integration configuration: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error integrating tool: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error integrating tool: {str(e)}"
        )

@router.get("/agents/{agent_id}/tools", response_model=PaginatedResponse)
async def list_agent_tools(
    agent_id: UUID = Path(..., description="Agent ID"),
    status: Optional[str] = Query(None, description="Filter by integration status"),
    pagination: PaginationParams = Depends(),
    service: ToolService = Depends(get_tool_service)
):
    """
    List tools integrated with an agent.
    
    Args:
        agent_id: Agent ID
        status: Optional integration status filter
        pagination: Pagination parameters
        service: Tool service
        
    Returns:
        PaginatedResponse: Paginated list of integrated tools
        
    Raises:
        HTTPException: If listing fails
    """
    logger.info(f"Listing tools for agent: {agent_id}")
    try:
        return await service.list_agent_tools(
            agent_id=agent_id,
            status=status,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except Exception as e:
        logger.error(f"Error listing agent tools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing agent tools: {str(e)}"
        )

@router.get("/agents/{agent_id}/tools/{tool_id}", response_model=ToolIntegrationResponse)
async def get_agent_tool_integration(
    agent_id: UUID = Path(..., description="Agent ID"),
    tool_id: UUID = Path(..., description="Tool ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Get details of a specific tool integration for an agent.
    
    Args:
        agent_id: Agent ID
        tool_id: Tool ID
        service: Tool service
        
    Returns:
        ToolIntegrationResponse: Integration details
        
    Raises:
        HTTPException: If integration not found
    """
    logger.info(f"Getting integration details for tool {tool_id} with agent {agent_id}")
    try:
        return await service.get_integration(agent_id=agent_id, tool_id=tool_id)
    except ToolNotFoundError:
        logger.error(f"Integration not found for agent {agent_id} and tool {tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration not found for agent {agent_id} and tool {tool_id}"
        )
    except Exception as e:
        logger.error(f"Error getting integration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting integration: {str(e)}"
        )

@router.put("/agents/{agent_id}/tools/{tool_id}", response_model=ToolIntegrationResponse)
async def update_agent_tool_integration(
    update_request: ToolIntegrationUpdateRequest,
    agent_id: UUID = Path(..., description="Agent ID"),
    tool_id: UUID = Path(..., description="Tool ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Update a tool integration configuration.
    
    Args:
        update_request: Update request data
        agent_id: Agent ID
        tool_id: Tool ID
        service: Tool service
        
    Returns:
        ToolIntegrationResponse: Updated integration details
        
    Raises:
        HTTPException: If update fails
    """
    logger.info(f"Updating integration for tool {tool_id} with agent {agent_id}")
    try:
        return await service.update_integration(
            agent_id=agent_id,
            tool_id=tool_id,
            update_data=update_request
        )
    except ToolNotFoundError:
        logger.error(f"Integration not found for agent {agent_id} and tool {tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration not found for agent {agent_id} and tool {tool_id}"
        )
    except ToolValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid integration configuration: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error updating integration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating integration: {str(e)}"
        )

@router.delete("/agents/{agent_id}/tools/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_agent_tool_integration(
    agent_id: UUID = Path(..., description="Agent ID"),
    tool_id: UUID = Path(..., description="Tool ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Remove a tool integration from an agent.
    
    Args:
        agent_id: Agent ID
        tool_id: Tool ID
        service: Tool service
        
    Raises:
        HTTPException: If removal fails
    """
    logger.info(f"Removing integration for tool {tool_id} from agent {agent_id}")
    try:
        await service.remove_integration(agent_id=agent_id, tool_id=tool_id)
    except ToolNotFoundError:
        logger.error(f"Integration not found for agent {agent_id} and tool {tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration not found for agent {agent_id} and tool {tool_id}"
        )
    except Exception as e:
        logger.error(f"Error removing integration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing integration: {str(e)}"
        )

@router.post("/agents/{agent_id}/tools/{tool_id}/disable", response_model=ToolIntegrationResponse)
async def disable_agent_tool_integration(
    agent_id: UUID = Path(..., description="Agent ID"),
    tool_id: UUID = Path(..., description="Tool ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Disable a tool integration for an agent.
    
    Args:
        agent_id: Agent ID
        tool_id: Tool ID
        service: Tool service
        
    Returns:
        ToolIntegrationResponse: Updated integration details
        
    Raises:
        HTTPException: If disabling fails
    """
    logger.info(f"Disabling integration for tool {tool_id} with agent {agent_id}")
    try:
        update_data = ToolIntegrationUpdateRequest(status="DISABLED")
        return await service.update_integration(
            agent_id=agent_id,
            tool_id=tool_id,
            update_data=update_data
        )
    except ToolNotFoundError:
        logger.error(f"Integration not found for agent {agent_id} and tool {tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration not found for agent {agent_id} and tool {tool_id}"
        )
    except Exception as e:
        logger.error(f"Error disabling integration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error disabling integration: {str(e)}"
        )

@router.post("/agents/{agent_id}/tools/{tool_id}/enable", response_model=ToolIntegrationResponse)
async def enable_agent_tool_integration(
    agent_id: UUID = Path(..., description="Agent ID"),
    tool_id: UUID = Path(..., description="Tool ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Enable a tool integration for an agent.
    
    Args:
        agent_id: Agent ID
        tool_id: Tool ID
        service: Tool service
        
    Returns:
        ToolIntegrationResponse: Updated integration details
        
    Raises:
        HTTPException: If enabling fails
    """
    logger.info(f"Enabling integration for tool {tool_id} with agent {agent_id}")
    try:
        update_data = ToolIntegrationUpdateRequest(status="ACTIVE")
        return await service.update_integration(
            agent_id=agent_id,
            tool_id=tool_id,
            update_data=update_data
        )
    except ToolNotFoundError:
        logger.error(f"Integration not found for agent {agent_id} and tool {tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration not found for agent {agent_id} and tool {tool_id}"
        )
    except Exception as e:
        logger.error(f"Error enabling integration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enabling integration: {str(e)}"
        )

@router.get("/integrations", response_model=PaginatedResponse)
async def list_all_integrations(
    tool_id: Optional[UUID] = Query(None, description="Filter by tool ID"),
    agent_id: Optional[UUID] = Query(None, description="Filter by agent ID"),
    status: Optional[str] = Query(None, description="Filter by integration status"),
    pagination: PaginationParams = Depends(),
    service: ToolService = Depends(get_tool_service)
):
    """
    List all tool integrations with filtering and pagination.
    
    Args:
        tool_id: Optional tool ID filter
        agent_id: Optional agent ID filter
        status: Optional integration status filter
        pagination: Pagination parameters
        service: Tool service
        
    Returns:
        PaginatedResponse: Paginated list of tool integrations
        
    Raises:
        HTTPException: If listing fails
    """
    logger.info(f"Listing all integrations (tool_id={tool_id}, agent_id={agent_id}, status={status})")
    try:
        return await service.list_all_integrations(
            tool_id=tool_id,
            agent_id=agent_id,
            status=status,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except Exception as e:
        logger.error(f"Error listing integrations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing integrations: {str(e)}"
        )
