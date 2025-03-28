"""
Evaluation router for the Tool Integration service.

This module defines the FastAPI routes for tool evaluation operations,
allowing clients to evaluate tools for security, performance, and compatibility.
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status

from ..dependencies import get_tool_service
from ..models.api import (
    EvaluationRequest,
    ComprehensiveEvaluationResult,
    ToolEvaluationResult,
    BatchEvaluationRequest,
    BatchEvaluationResponse,
    EvaluationCriteriaType,
    PaginatedResponse,
    PaginationParams
)
from ..services.tool_service import ToolService
from ..exceptions import ToolEvaluationError, ToolNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/tools/{tool_id}", response_model=ComprehensiveEvaluationResult)
async def evaluate_tool(
    evaluation_request: EvaluationRequest,
    tool_id: UUID = Path(..., description="Tool ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Evaluate a tool against specified criteria.
    
    Args:
        evaluation_request: Evaluation request with criteria
        tool_id: Tool ID
        service: Tool service
        
    Returns:
        ComprehensiveEvaluationResult: Evaluation results
        
    Raises:
        HTTPException: If evaluation fails
    """
    logger.info(f"Evaluating tool: {tool_id}")
    try:
        return await service.evaluate_tool(tool_id, evaluation_request.criteria, evaluation_request.context)
    except ToolNotFoundError:
        logger.error(f"Tool not found: {tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool not found: {tool_id}"
        )
    except ToolEvaluationError as e:
        logger.error(f"Tool evaluation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool evaluation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error evaluating tool: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating tool: {str(e)}"
        )

@router.get("/tools/{tool_id}", response_model=List[ToolEvaluationResult])
async def get_tool_evaluations(
    tool_id: UUID = Path(..., description="Tool ID"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of evaluations"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Get evaluation history for a tool.
    
    Args:
        tool_id: Tool ID
        limit: Maximum number of evaluations to return
        service: Tool service
        
    Returns:
        List[ToolEvaluationResult]: List of evaluation results
        
    Raises:
        HTTPException: If tool not found or retrieval fails
    """
    logger.info(f"Getting evaluations for tool: {tool_id}")
    try:
        return await service.get_tool_evaluations(tool_id, limit)
    except ToolNotFoundError:
        logger.error(f"Tool not found: {tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool not found: {tool_id}"
        )
    except Exception as e:
        logger.error(f"Error getting tool evaluations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting tool evaluations: {str(e)}"
        )

@router.post("/batch", response_model=BatchEvaluationResponse)
async def batch_evaluate_tools(
    batch_request: BatchEvaluationRequest,
    service: ToolService = Depends(get_tool_service)
):
    """
    Evaluate multiple tools in a single batch operation.
    
    Args:
        batch_request: Batch evaluation request
        service: Tool service
        
    Returns:
        BatchEvaluationResponse: Batch evaluation results
        
    Raises:
        HTTPException: If batch evaluation fails
    """
    logger.info(f"Batch evaluating {len(batch_request.evaluations)} tools")
    try:
        return await service.batch_evaluate_tools(batch_request.evaluations)
    except Exception as e:
        logger.error(f"Error in batch tool evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in batch tool evaluation: {str(e)}"
        )

@router.get("/history", response_model=PaginatedResponse)
async def list_evaluations(
    tool_id: Optional[UUID] = Query(None, description="Filter by tool ID"),
    evaluation_type: Optional[EvaluationCriteriaType] = Query(None, description="Filter by evaluation type"),
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum score filter"),
    pagination: PaginationParams = Depends(),
    service: ToolService = Depends(get_tool_service)
):
    """
    List evaluations with filtering and pagination.
    
    Args:
        tool_id: Optional tool ID filter
        evaluation_type: Optional evaluation type filter
        min_score: Optional minimum score filter
        pagination: Pagination parameters
        service: Tool service
        
    Returns:
        PaginatedResponse: Paginated list of evaluations
        
    Raises:
        HTTPException: If listing evaluations fails
    """
    logger.info(f"Listing evaluations (tool_id={tool_id}, type={evaluation_type})")
    try:
        return await service.list_evaluations(
            tool_id=tool_id,
            evaluation_type=evaluation_type,
            min_score=min_score,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except Exception as e:
        logger.error(f"Error listing evaluations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing evaluations: {str(e)}"
        )

@router.get("/evaluations/{evaluation_id}", response_model=ComprehensiveEvaluationResult)
async def get_evaluation(
    evaluation_id: UUID = Path(..., description="Evaluation ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Get a specific evaluation by ID.
    
    Args:
        evaluation_id: Evaluation ID
        service: Tool service
        
    Returns:
        ComprehensiveEvaluationResult: Evaluation result
        
    Raises:
        HTTPException: If evaluation not found
    """
    logger.info(f"Getting evaluation: {evaluation_id}")
    try:
        return await service.get_evaluation(evaluation_id)
    except ToolEvaluationError as e:
        logger.error(f"Tool evaluation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting evaluation: {str(e)}"
        )

@router.post("/tools/{tool_id}/security", response_model=ComprehensiveEvaluationResult)
async def evaluate_tool_security(
    tool_id: UUID = Path(..., description="Tool ID"),
    service: ToolService = Depends(get_tool_service)
):
    """
    Evaluate a tool's security specifically.
    
    Args:
        tool_id: Tool ID
        service: Tool service
        
    Returns:
        ComprehensiveEvaluationResult: Security evaluation results
        
    Raises:
        HTTPException: If evaluation fails
    """
    logger.info(f"Evaluating security for tool: {tool_id}")
    try:
        criteria = {EvaluationCriteriaType.SECURITY: True}
        return await service.evaluate_tool(tool_id, criteria)
    except ToolNotFoundError:
        logger.error(f"Tool not found: {tool_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool not found: {tool_id}"
        )
    except ToolEvaluationError as e:
        logger.error(f"Tool security evaluation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool security evaluation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error evaluating tool security: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating tool security: {str(e)}"
        )
