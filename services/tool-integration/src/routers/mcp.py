"""
MCP router for the Tool Integration service.

This module defines the FastAPI routes for MCP (Model Context Protocol) operations,
allowing clients to interact with MCP servers and their tools.
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status

from ..dependencies import get_tool_service
from ..models.api import (
    MCPServerInfo,
    MCPToolInfo,
    MCPServerListResponse,
    MCPToolListResponse,
    ToolCreate,
    Tool,
    PaginatedResponse,
    PaginationParams
)
from ..services.tool_service import ToolService
from ..exceptions import MCPIntegrationError, MCPToolNotAvailableError, ToolRegistrationError

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/servers", response_model=MCPServerListResponse)
async def list_mcp_servers(
    service: ToolService = Depends(get_tool_service)
):
    """
    List all connected MCP servers.
    
    Args:
        service: Tool service
        
    Returns:
        MCPServerListResponse: List of connected MCP servers
        
    Raises:
        HTTPException: If listing fails
    """
    logger.info("Listing MCP servers")
    try:
        return await service.list_mcp_servers()
    except MCPIntegrationError as e:
        logger.error(f"MCP integration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MCP integration error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error listing MCP servers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing MCP servers: {str(e)}"
        )

@router.get("/servers/{server_name}", response_model=MCPServerInfo)
async def get_mcp_server_info(
    server_name: str = Path(..., description="MCP server name"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Get information about a specific MCP server.
    
    Args:
        server_name: MCP server name
        service: Tool service
        
    Returns:
        MCPServerInfo: MCP server information
        
    Raises:
        HTTPException: If server not found
    """
    logger.info(f"Getting MCP server info: {server_name}")
    try:
        return await service.get_mcp_server_info(server_name)
    except MCPIntegrationError as e:
        logger.error(f"MCP integration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting MCP server info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting MCP server info: {str(e)}"
        )

@router.get("/servers/{server_name}/tools", response_model=MCPToolListResponse)
async def list_mcp_server_tools(
    server_name: str = Path(..., description="MCP server name"),
    service: ToolService = Depends(get_tool_service)
):
    """
    List all tools provided by a specific MCP server.
    
    Args:
        server_name: MCP server name
        service: Tool service
        
    Returns:
        MCPToolListResponse: List of tools provided by the MCP server
        
    Raises:
        HTTPException: If server not found or listing fails
    """
    logger.info(f"Listing tools for MCP server: {server_name}")
    try:
        return await service.list_mcp_server_tools(server_name)
    except MCPIntegrationError as e:
        logger.error(f"MCP integration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error listing MCP server tools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing MCP server tools: {str(e)}"
        )

@router.get("/servers/{server_name}/tools/{tool_name}", response_model=MCPToolInfo)
async def get_mcp_tool_info(
    server_name: str = Path(..., description="MCP server name"),
    tool_name: str = Path(..., description="MCP tool name"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Get information about a specific MCP tool.
    
    Args:
        server_name: MCP server name
        tool_name: MCP tool name
        service: Tool service
        
    Returns:
        MCPToolInfo: MCP tool information
        
    Raises:
        HTTPException: If tool not found
    """
    logger.info(f"Getting MCP tool info: {server_name}/{tool_name}")
    try:
        return await service.get_mcp_tool_info(server_name, tool_name)
    except MCPToolNotAvailableError as e:
        logger.error(f"MCP tool not available: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP tool not found: {str(e)}"
        )
    except MCPIntegrationError as e:
        logger.error(f"MCP integration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MCP integration error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting MCP tool info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting MCP tool info: {str(e)}"
        )

@router.post("/servers/{server_name}/tools/{tool_name}/register", response_model=Tool, status_code=status.HTTP_201_CREATED)
async def register_mcp_tool(
    server_name: str = Path(..., description="MCP server name"),
    tool_name: str = Path(..., description="MCP tool name"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Register an MCP tool in the tool registry.
    
    Args:
        server_name: MCP server name
        tool_name: MCP tool name
        service: Tool service
        
    Returns:
        Tool: Registered tool
        
    Raises:
        HTTPException: If tool not found or registration fails
    """
    logger.info(f"Registering MCP tool: {server_name}/{tool_name}")
    try:
        return await service.register_mcp_tool(server_name, tool_name)
    except MCPToolNotAvailableError as e:
        logger.error(f"MCP tool not available: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP tool not found: {str(e)}"
        )
    except ToolRegistrationError as e:
        logger.error(f"Tool registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool registration failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error registering MCP tool: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering MCP tool: {str(e)}"
        )

@router.post("/servers/{server_name}/refresh", response_model=MCPServerInfo)
async def refresh_mcp_server_connection(
    server_name: str = Path(..., description="MCP server name"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Refresh connection to an MCP server.
    
    Args:
        server_name: MCP server name
        service: Tool service
        
    Returns:
        MCPServerInfo: Updated MCP server information
        
    Raises:
        HTTPException: If server not found or refresh fails
    """
    logger.info(f"Refreshing MCP server connection: {server_name}")
    try:
        return await service.refresh_mcp_server_connection(server_name)
    except MCPIntegrationError as e:
        logger.error(f"MCP integration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MCP integration error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error refreshing MCP server connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error refreshing MCP server connection: {str(e)}"
        )

@router.post("/servers/{server_name}/register-all", response_model=List[Tool])
async def register_all_mcp_server_tools(
    server_name: str = Path(..., description="MCP server name"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Register all tools from an MCP server.
    
    Args:
        server_name: MCP server name
        service: Tool service
        
    Returns:
        List[Tool]: List of registered tools
        
    Raises:
        HTTPException: If server not found or registration fails
    """
    logger.info(f"Registering all tools from MCP server: {server_name}")
    try:
        return await service.register_all_mcp_server_tools(server_name)
    except MCPIntegrationError as e:
        logger.error(f"MCP integration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MCP integration error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error registering all MCP server tools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering all MCP server tools: {str(e)}"
        )

@router.get("/tools", response_model=List[Tool])
async def list_registered_mcp_tools(
    server_name: Optional[str] = Query(None, description="Filter by MCP server name"),
    service: ToolService = Depends(get_tool_service)
):
    """
    List all registered MCP tools.
    
    Args:
        server_name: Optional MCP server name filter
        service: Tool service
        
    Returns:
        List[Tool]: List of registered MCP tools
        
    Raises:
        HTTPException: If listing fails
    """
    logger.info(f"Listing registered MCP tools")
    try:
        return await service.list_registered_mcp_tools(server_name)
    except Exception as e:
        logger.error(f"Error listing registered MCP tools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing registered MCP tools: {str(e)}"
        )
