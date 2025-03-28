"""
Tasks router for the Planning System service.

This module defines the FastAPI routes for task management,
including creating, reading, updating, and deleting planning tasks.
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status

from ..dependencies import get_planning_service
from ..models.api import (
    PlanningTaskCreate,
    PlanningTaskUpdate,
    PlanningTaskResponse,
    PaginatedResponse,
    PaginationParams,
    TaskStatus
)
from ..services.planning_service import PlanningService
from ..exceptions import TaskNotFoundError, TaskValidationError, PlanNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=PlanningTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: PlanningTaskCreate,
    service: PlanningService = Depends(get_planning_service)
):
    """
    Create a new planning task.
    
    Args:
        task_data: Task data
        service: Planning service
        
    Returns:
        PlanningTaskResponse: Created task
        
    Raises:
        HTTPException: If task creation fails
        TaskValidationError: If task data is invalid
    """
    logger.info(f"Creating task: {task_data.name}")
    try:
        return await service.create_task(task_data)
    except TaskValidationError as e:
        logger.error(f"Task validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid task data: {str(e)}"
        )
    except PlanNotFoundError as e:
        logger.error(f"Plan not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating task: {str(e)}"
        )

@router.get("/{task_id}", response_model=PlanningTaskResponse)
async def get_task(
    task_id: UUID = Path(..., description="Task ID"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Get a planning task by ID.
    
    Args:
        task_id: Task ID
        service: Planning service
        
    Returns:
        PlanningTaskResponse: Task data
        
    Raises:
        HTTPException: If task not found
    """
    logger.info(f"Getting task: {task_id}")
    try:
        return await service.get_task(task_id)
    except TaskNotFoundError:
        logger.error(f"Task not found: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}"
        )
    except Exception as e:
        logger.error(f"Error getting task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting task: {str(e)}"
        )

@router.get("/", response_model=PaginatedResponse)
async def list_tasks(
    plan_id: UUID = Query(..., description="Plan ID"),
    phase_id: Optional[UUID] = Query(None, description="Filter by phase ID"),
    milestone_id: Optional[UUID] = Query(None, description="Filter by milestone ID"),
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    pagination: PaginationParams = Depends(),
    service: PlanningService = Depends(get_planning_service)
):
    """
    List planning tasks with filtering and pagination.
    
    Args:
        plan_id: Plan ID
        phase_id: Optional phase ID filter
        milestone_id: Optional milestone ID filter
        status: Optional status filter
        pagination: Pagination parameters
        service: Planning service
        
    Returns:
        PaginatedResponse: Paginated list of tasks
        
    Raises:
        HTTPException: If listing tasks fails
    """
    logger.info(f"Listing tasks (plan_id={plan_id}, phase_id={phase_id}, milestone_id={milestone_id}, status={status})")
    try:
        return await service.list_tasks(
            plan_id=plan_id,
            phase_id=phase_id,
            milestone_id=milestone_id,
            status=status, 
            page=pagination.page, 
            page_size=pagination.page_size
        )
    except PlanNotFoundError as e:
        logger.error(f"Plan not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing tasks: {str(e)}"
        )

@router.put("/{task_id}", response_model=PlanningTaskResponse)
async def update_task(
    task_data: PlanningTaskUpdate,
    task_id: UUID = Path(..., description="Task ID"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Update a planning task.
    
    Args:
        task_data: Task data to update
        task_id: Task ID
        service: Planning service
        
    Returns:
        PlanningTaskResponse: Updated task
        
    Raises:
        HTTPException: If task not found or update fails
    """
    logger.info(f"Updating task: {task_id}")
    try:
        return await service.update_task(task_id, task_data)
    except TaskNotFoundError:
        logger.error(f"Task not found: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}"
        )
    except TaskValidationError as e:
        logger.error(f"Task validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid task data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error updating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating task: {str(e)}"
        )

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID = Path(..., description="Task ID"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Delete a planning task.
    
    Args:
        task_id: Task ID
        service: Planning service
        
    Raises:
        HTTPException: If task not found or deletion fails
    """
    logger.info(f"Deleting task: {task_id}")
    try:
        await service.delete_task(task_id)
    except TaskNotFoundError:
        logger.error(f"Task not found: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}"
        )
    except TaskValidationError as e:
        logger.error(f"Task validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete task: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting task: {str(e)}"
        )

@router.post("/bulk-update", response_model=List[PlanningTaskResponse])
async def bulk_update_tasks(
    task_ids: List[UUID],
    update_data: dict,
    service: PlanningService = Depends(get_planning_service)
):
    """
    Update multiple tasks with the same data.
    
    Args:
        task_ids: List of task IDs
        update_data: Update data to apply to all tasks
        service: Planning service
        
    Returns:
        List[PlanningTaskResponse]: Updated tasks
        
    Raises:
        HTTPException: If any task not found or update fails
    """
    logger.info(f"Bulk updating {len(task_ids)} tasks")
    try:
        return await service.bulk_update_tasks(task_ids, update_data)
    except TaskNotFoundError as e:
        logger.error(f"Task not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {str(e)}"
        )
    except TaskValidationError as e:
        logger.error(f"Task validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid task data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error bulk updating tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error bulk updating tasks: {str(e)}"
        )
