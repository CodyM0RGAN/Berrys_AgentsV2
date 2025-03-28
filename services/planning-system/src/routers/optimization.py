"""
Optimization router for the Planning System service.

This module defines the FastAPI routes for resource optimization,
including optimizing resource allocation and scheduling.
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status

from ..dependencies import get_planning_service
from ..models.api import (
    OptimizationRequest,
    OptimizationResult,
    PaginatedResponse,
    PaginationParams
)
from ..services.planning_service import PlanningService
from ..exceptions import (
    PlanNotFoundError,
    ResourceAllocationError,
    OptimizationTimeoutError,
    InfeasibleAllocationError
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/resources", response_model=OptimizationResult)
async def optimize_resources(
    optimization_request: OptimizationRequest,
    service: PlanningService = Depends(get_planning_service)
):
    """
    Optimize resource allocation for a plan.
    
    Args:
        optimization_request: Optimization request data
        service: Planning service
        
    Returns:
        OptimizationResult: Optimization result
        
    Raises:
        HTTPException: If optimization fails
    """
    logger.info(f"Optimizing resources for plan: {optimization_request.plan_id}")
    try:
        return await service.optimize_resources(optimization_request)
    except PlanNotFoundError:
        logger.error(f"Plan not found: {optimization_request.plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {optimization_request.plan_id}"
        )
    except OptimizationTimeoutError as e:
        logger.error(f"Optimization timeout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Optimization timeout: {str(e)}"
        )
    except InfeasibleAllocationError as e:
        logger.error(f"Infeasible allocation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Infeasible allocation: {str(e)}"
        )
    except ResourceAllocationError as e:
        logger.error(f"Resource allocation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Resource allocation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error optimizing resources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error optimizing resources: {str(e)}"
        )

@router.get("/resources/{plan_id}/latest", response_model=OptimizationResult)
async def get_latest_optimization(
    plan_id: UUID = Path(..., description="Plan ID"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Get the latest resource optimization for a plan.
    
    Args:
        plan_id: Plan ID
        service: Planning service
        
    Returns:
        OptimizationResult: Latest optimization result
        
    Raises:
        HTTPException: If optimization not found
    """
    logger.info(f"Getting latest optimization for plan: {plan_id}")
    try:
        optimization = await service.get_latest_optimization(plan_id)
        if not optimization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No optimization found for plan: {plan_id}"
            )
        return optimization
    except PlanNotFoundError:
        logger.error(f"Plan not found: {plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}"
        )
    except Exception as e:
        logger.error(f"Error getting latest optimization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting latest optimization: {str(e)}"
        )

@router.get("/resources/{plan_id}/history", response_model=PaginatedResponse)
async def get_optimization_history(
    plan_id: UUID = Path(..., description="Plan ID"),
    pagination: PaginationParams = Depends(),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Get the history of resource optimizations for a plan.
    
    Args:
        plan_id: Plan ID
        pagination: Pagination parameters
        service: Planning service
        
    Returns:
        PaginatedResponse: Paginated list of optimizations
        
    Raises:
        HTTPException: If getting optimization history fails
    """
    logger.info(f"Getting optimization history for plan: {plan_id}")
    try:
        return await service.get_optimization_history(
            plan_id=plan_id,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except PlanNotFoundError:
        logger.error(f"Plan not found: {plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}"
        )
    except Exception as e:
        logger.error(f"Error getting optimization history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting optimization history: {str(e)}"
        )

@router.post("/schedule", response_model=Dict[str, Any])
async def optimize_schedule(
    plan_id: UUID,
    options: Optional[Dict[str, Any]] = None,
    service: PlanningService = Depends(get_planning_service)
):
    """
    Optimize the schedule for a plan.
    
    Args:
        plan_id: Plan ID
        options: Optional scheduling options
        service: Planning service
        
    Returns:
        Dict[str, Any]: Schedule optimization result
        
    Raises:
        HTTPException: If schedule optimization fails
    """
    logger.info(f"Optimizing schedule for plan: {plan_id}")
    try:
        return await service.optimize_schedule(plan_id, options or {})
    except PlanNotFoundError:
        logger.error(f"Plan not found: {plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}"
        )
    except OptimizationTimeoutError as e:
        logger.error(f"Schedule optimization timeout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Schedule optimization timeout: {str(e)}"
        )
    except ResourceAllocationError as e:
        logger.error(f"Resource allocation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Resource allocation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error optimizing schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error optimizing schedule: {str(e)}"
        )

@router.get("/resource-utilization/{plan_id}", response_model=Dict[str, Any])
async def get_resource_utilization(
    plan_id: UUID = Path(..., description="Plan ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Get resource utilization for a plan.
    
    Args:
        plan_id: Plan ID
        start_date: Optional start date
        end_date: Optional end date
        service: Planning service
        
    Returns:
        Dict[str, Any]: Resource utilization data
        
    Raises:
        HTTPException: If getting resource utilization fails
    """
    logger.info(f"Getting resource utilization for plan: {plan_id}")
    try:
        return await service.get_resource_utilization(plan_id, start_date, end_date)
    except PlanNotFoundError:
        logger.error(f"Plan not found: {plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}"
        )
    except ValueError as e:
        logger.error(f"Invalid date format: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting resource utilization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting resource utilization: {str(e)}"
        )

@router.post("/what-if", response_model=Dict[str, Any])
async def run_what_if_analysis(
    plan_id: UUID,
    scenario: Dict[str, Any],
    service: PlanningService = Depends(get_planning_service)
):
    """
    Run a what-if analysis for a plan.
    
    Args:
        plan_id: Plan ID
        scenario: What-if scenario data
        service: Planning service
        
    Returns:
        Dict[str, Any]: What-if analysis result
        
    Raises:
        HTTPException: If what-if analysis fails
    """
    logger.info(f"Running what-if analysis for plan: {plan_id}")
    try:
        return await service.run_what_if_analysis(plan_id, scenario)
    except PlanNotFoundError:
        logger.error(f"Plan not found: {plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}"
        )
    except ValueError as e:
        logger.error(f"Invalid scenario data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error running what-if analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running what-if analysis: {str(e)}"
        )
