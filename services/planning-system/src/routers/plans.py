"""
Plans router for the Planning System service.

This module defines the FastAPI routes for plan management,
including creating, reading, updating, and deleting strategic plans.
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status

from ..dependencies import get_planning_service
from ..models.api import (
    StrategicPlanCreate,
    StrategicPlanUpdate,
    StrategicPlanResponse,
    PaginatedResponse,
    PaginationParams,
    PlanStatus
)
from ..services.planning_service import PlanningService
from ..exceptions import PlanNotFoundError, PlanValidationError

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=StrategicPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_data: StrategicPlanCreate,
    service: PlanningService = Depends(get_planning_service)
):
    """
    Create a new strategic plan.
    
    Args:
        plan_data: Plan data
        service: Planning service
        
    Returns:
        StrategicPlanResponse: Created plan
        
    Raises:
        HTTPException: If plan creation fails
        PlanValidationError: If plan data is invalid
    """
    logger.info(f"Creating plan: {plan_data.name}")
    try:
        return await service.create_plan(plan_data)
    except PlanValidationError as e:
        logger.error(f"Plan validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating plan: {str(e)}"
        )

@router.get("/{plan_id}", response_model=StrategicPlanResponse)
async def get_plan(
    plan_id: UUID = Path(..., description="Plan ID"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Get a strategic plan by ID.
    
    Args:
        plan_id: Plan ID
        service: Planning service
        
    Returns:
        StrategicPlanResponse: Plan data
        
    Raises:
        HTTPException: If plan not found
    """
    logger.info(f"Getting plan: {plan_id}")
    try:
        return await service.get_plan(plan_id)
    except PlanNotFoundError:
        logger.error(f"Plan not found: {plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}"
        )
    except Exception as e:
        logger.error(f"Error getting plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting plan: {str(e)}"
        )

@router.get("/", response_model=PaginatedResponse)
async def list_plans(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    status: Optional[PlanStatus] = Query(None, description="Filter by status"),
    pagination: PaginationParams = Depends(),
    service: PlanningService = Depends(get_planning_service)
):
    """
    List strategic plans with filtering and pagination.
    
    Args:
        project_id: Optional project ID filter
        status: Optional status filter
        pagination: Pagination parameters
        service: Planning service
        
    Returns:
        PaginatedResponse: Paginated list of plans
        
    Raises:
        HTTPException: If listing plans fails
    """
    logger.info(f"Listing plans (project_id={project_id}, status={status})")
    try:
        return await service.list_plans(
            project_id=project_id,
            status=status, 
            page=pagination.page, 
            page_size=pagination.page_size
        )
    except Exception as e:
        logger.error(f"Error listing plans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing plans: {str(e)}"
        )

@router.put("/{plan_id}", response_model=StrategicPlanResponse)
async def update_plan(
    plan_data: StrategicPlanUpdate,
    plan_id: UUID = Path(..., description="Plan ID"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Update a strategic plan.
    
    Args:
        plan_data: Plan data to update
        plan_id: Plan ID
        service: Planning service
        
    Returns:
        StrategicPlanResponse: Updated plan
        
    Raises:
        HTTPException: If plan not found or update fails
    """
    logger.info(f"Updating plan: {plan_id}")
    try:
        return await service.update_plan(plan_id, plan_data)
    except PlanNotFoundError:
        logger.error(f"Plan not found: {plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}"
        )
    except PlanValidationError as e:
        logger.error(f"Plan validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error updating plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating plan: {str(e)}"
        )

@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: UUID = Path(..., description="Plan ID"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Delete a strategic plan.
    
    Args:
        plan_id: Plan ID
        service: Planning service
        
    Raises:
        HTTPException: If plan not found or deletion fails
    """
    logger.info(f"Deleting plan: {plan_id}")
    try:
        await service.delete_plan(plan_id)
    except PlanNotFoundError:
        logger.error(f"Plan not found: {plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}"
        )
    except Exception as e:
        logger.error(f"Error deleting plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting plan: {str(e)}"
        )

@router.post("/{plan_id}/activate", response_model=StrategicPlanResponse)
async def activate_plan(
    plan_id: UUID = Path(..., description="Plan ID"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Activate a strategic plan.
    
    Args:
        plan_id: Plan ID
        service: Planning service
        
    Returns:
        StrategicPlanResponse: Activated plan
        
    Raises:
        HTTPException: If plan not found or activation fails
    """
    logger.info(f"Activating plan: {plan_id}")
    try:
        return await service.activate_plan(plan_id)
    except PlanNotFoundError:
        logger.error(f"Plan not found: {plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}"
        )
    except Exception as e:
        logger.error(f"Error activating plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error activating plan: {str(e)}"
        )

@router.post("/{plan_id}/clone", response_model=StrategicPlanResponse)
async def clone_plan(
    plan_id: UUID = Path(..., description="Source plan ID"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Clone a strategic plan.
    
    Args:
        plan_id: Source plan ID
        service: Planning service
        
    Returns:
        StrategicPlanResponse: Cloned plan
        
    Raises:
        HTTPException: If plan not found or cloning fails
    """
    logger.info(f"Cloning plan: {plan_id}")
    try:
        return await service.clone_plan(plan_id)
    except PlanNotFoundError:
        logger.error(f"Plan not found: {plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}"
        )
    except Exception as e:
        logger.error(f"Error cloning plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cloning plan: {str(e)}"
        )

@router.get("/{plan_id}/history", response_model=List[dict])
async def get_plan_history(
    plan_id: UUID = Path(..., description="Plan ID"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of history entries"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Get history of changes to a strategic plan.
    
    Args:
        plan_id: Plan ID
        limit: Maximum number of history entries
        service: Planning service
        
    Returns:
        List[dict]: Plan history entries
        
    Raises:
        HTTPException: If plan not found or getting history fails
    """
    logger.info(f"Getting plan history: {plan_id}")
    try:
        return await service.get_plan_history(plan_id, limit)
    except PlanNotFoundError:
        logger.error(f"Plan not found: {plan_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}"
        )
    except Exception as e:
        logger.error(f"Error getting plan history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting plan history: {str(e)}"
        )
