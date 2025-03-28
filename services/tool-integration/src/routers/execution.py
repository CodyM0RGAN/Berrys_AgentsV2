"""
Execution router for the Tool Integration service.

This module defines the FastAPI routes for tool execution operations,
allowing clients to execute tools and check execution status.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status

from ..dependencies import get_tool_service
from ..models.api import (
    ToolExecutionRequest,
    ToolExecutionResponse,
    ToolExecutionStatusRequest,
    ExecutionMode,
    PaginatedResponse,
    PaginationParams
)
from ..services.tool_service import ToolService
from ..exceptions import (
    ToolNotFoundError,
    ToolExecutionError,
    ToolExecutionTimeoutError,
    SecurityViolationError,
    ToolValidationError
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    execution_request: ToolExecutionRequest,
    service: ToolService = Depends(get_tool_service)
):
    """
    Execute a tool with the provided parameters.
    
    Args:
        execution_request: Tool execution request with parameters
        service: Tool service
        
    Returns:
        ToolExecutionResponse: Execution response with results or status
        
    Raises:
        HTTPException: If execution fails
    """
    logger.info(f"Executing tool {execution_request.tool_id} for agent {execution_request.agent_id}")
    try:
        return await service.execute_tool(execution_request)
    except ToolNotFoundError:
        logger.error(f"Tool or integration not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool or integration not found for tool_id={execution_request.tool_id}, agent_id={execution_request.agent_id}"
        )
    except ToolValidationError as e:
        logger.error(f"Parameter validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameters: {str(e)}"
        )
    except SecurityViolationError as e:
        logger.error(f"Security violation during execution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Execution denied due to security concerns: {str(e)}"
        )
    except ToolExecutionTimeoutError as e:
        logger.error(f"Execution timed out: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Execution timed out: {str(e)}"
        )
    except ToolExecutionError as e:
        logger.error(f"Execution error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during execution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during execution: {str(e)}"
        )

@router.get("/status/{execution_id}", response_model=ToolExecutionResponse)
async def get_execution_status(
    execution_id: UUID = Path(..., description="Execution ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Get status of a tool execution.
    
    Args:
        execution_id: Execution ID
        service: Tool service
        
    Returns:
        ToolExecutionResponse: Execution response with current status and results if available
        
    Raises:
        HTTPException: If execution not found
    """
    logger.info(f"Getting execution status: {execution_id}")
    try:
        return await service.get_execution_status(execution_id)
    except ToolExecutionError as e:
        logger.error(f"Execution not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting execution status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting execution status: {str(e)}"
        )

@router.post("/cancel/{execution_id}", response_model=ToolExecutionResponse)
async def cancel_execution(
    execution_id: UUID = Path(..., description="Execution ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Cancel a running tool execution.
    
    Args:
        execution_id: Execution ID
        service: Tool service
        
    Returns:
        ToolExecutionResponse: Execution response with updated status
        
    Raises:
        HTTPException: If cancellation fails
    """
    logger.info(f"Cancelling execution: {execution_id}")
    try:
        return await service.cancel_execution(execution_id)
    except ToolExecutionError as e:
        logger.error(f"Execution not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error cancelling execution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling execution: {str(e)}"
        )

@router.get("/history", response_model=PaginatedResponse)
async def list_executions(
    tool_id: Optional[UUID] = Query(None, description="Filter by tool ID"),
    agent_id: Optional[UUID] = Query(None, description="Filter by agent ID"),
    status: Optional[str] = Query(None, description="Filter by execution status"),
    mode: Optional[ExecutionMode] = Query(None, description="Filter by execution mode"),
    success: Optional[bool] = Query(None, description="Filter by execution success"),
    pagination: PaginationParams = Depends(),
    service: ToolService = Depends(get_tool_service)
):
    """
    List tool executions with filtering and pagination.
    
    Args:
        tool_id: Optional tool ID filter
        agent_id: Optional agent ID filter
        status: Optional execution status filter
        mode: Optional execution mode filter
        success: Optional execution success filter
        pagination: Pagination parameters
        service: Tool service
        
    Returns:
        PaginatedResponse: Paginated list of executions
        
    Raises:
        HTTPException: If listing fails
    """
    logger.info(f"Listing executions (tool_id={tool_id}, agent_id={agent_id}, status={status})")
    try:
        return await service.list_executions(
            tool_id=tool_id,
            agent_id=agent_id,
            status=status,
            mode=mode,
            success=success,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except Exception as e:
        logger.error(f"Error listing executions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing executions: {str(e)}"
        )

@router.get("/logs/{execution_id}", response_model=List[Dict[str, Any]])
async def get_execution_logs(
    execution_id: UUID = Path(..., description="Execution ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of log entries"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Get logs for a specific execution.
    
    Args:
        execution_id: Execution ID
        limit: Maximum number of log entries to return
        service: Tool service
        
    Returns:
        List[Dict[str, Any]]: List of log entries
        
    Raises:
        HTTPException: If execution not found or logs retrieval fails
    """
    logger.info(f"Getting logs for execution: {execution_id}")
    try:
        return await service.get_execution_logs(execution_id, limit)
    except ToolExecutionError as e:
        logger.error(f"Execution not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting execution logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting execution logs: {str(e)}"
        )

@router.get("/tools/{tool_id}/executions", response_model=PaginatedResponse)
async def get_tool_executions(
    tool_id: UUID = Path(..., description="Tool ID"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of executions"),
    pagination: PaginationParams = Depends(),
    service: ToolService = Depends(get_tool_service)
):
    """
    Get execution history for a specific tool.
    
    Args:
        tool_id: Tool ID
        limit: Maximum number of executions to return
        pagination: Pagination parameters
        service: Tool service
        
    Returns:
        PaginatedResponse: Paginated list of executions for the tool
        
    Raises:
        HTTPException: If tool not found or retrieval fails
    """
    logger.info(f"Getting executions for tool: {tool_id}")
    try:
        return await service.list_executions(
            tool_id=tool_id,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except ToolNotFoundError:
        logger.error(f"Tool not found: {tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool not found: {tool_id}"
        )
    except Exception as e:
        logger.error(f"Error getting tool executions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting tool executions: {str(e)}"
        )

@router.get("/agents/{agent_id}/executions", response_model=PaginatedResponse)
async def get_agent_executions(
    agent_id: UUID = Path(..., description="Agent ID"),
    pagination: PaginationParams = Depends(),
    service: ToolService = Depends(get_tool_service)
):
    """
    Get execution history for a specific agent.
    
    Args:
        agent_id: Agent ID
        pagination: Pagination parameters
        service: Tool service
        
    Returns:
        PaginatedResponse: Paginated list of executions for the agent
        
    Raises:
        HTTPException: If retrieval fails
    """
    logger.info(f"Getting executions for agent: {agent_id}")
    try:
        return await service.list_executions(
            agent_id=agent_id,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except Exception as e:
        logger.error(f"Error getting agent executions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting agent executions: {str(e)}"
        )
