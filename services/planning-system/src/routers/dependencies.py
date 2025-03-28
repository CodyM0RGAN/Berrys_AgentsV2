"""
Dependencies router for the Planning System service.

This module defines the FastAPI routes for task dependency management,
including creating, reading, updating, and deleting task dependencies.
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status

from ..dependencies import get_planning_service
from ..models.api import (
    DependencyCreate,
    DependencyUpdate,
    DependencyResponse,
    PaginatedResponse,
    PaginationParams,
    DependencyType
)
from ..services.planning_service import PlanningService
from ..exceptions import TaskNotFoundError, InvalidDependencyError, CyclicDependencyError

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=DependencyResponse, status_code=status.HTTP_201_CREATED)
async def create_dependency(
    dependency_data: DependencyCreate,
    service: PlanningService = Depends(get_planning_service)
):
    """
    Create a new task dependency.
    
    Args:
        dependency_data: Dependency data
        service: Planning service
        
    Returns:
        DependencyResponse: Created dependency
        
    Raises:
        HTTPException: If dependency creation fails
        InvalidDependencyError: If dependency data is invalid
    """
    logger.info(f"Creating dependency: {dependency_data.from_task_id} -> {dependency_data.to_task_id}")
    try:
        return await service.create_dependency(dependency_data)
    except TaskNotFoundError as e:
        logger.error(f"Task not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {str(e)}"
        )
    except InvalidDependencyError as e:
        logger.error(f"Invalid dependency: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid dependency: {str(e)}"
        )
    except CyclicDependencyError as e:
        logger.error(f"Cyclic dependency: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cyclic dependency: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating dependency: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating dependency: {str(e)}"
        )

@router.get("/{dependency_id}", response_model=DependencyResponse)
async def get_dependency(
    dependency_id: UUID = Path(..., description="Dependency ID"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Get a dependency by ID.
    
    Args:
        dependency_id: Dependency ID
        service: Planning service
        
    Returns:
        DependencyResponse: Dependency data
        
    Raises:
        HTTPException: If dependency not found
    """
    logger.info(f"Getting dependency: {dependency_id}")
    try:
        return await service.get_dependency(dependency_id)
    except InvalidDependencyError:
        logger.error(f"Dependency not found: {dependency_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dependency not found: {dependency_id}"
        )
    except Exception as e:
        logger.error(f"Error getting dependency: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting dependency: {str(e)}"
        )

@router.get("/", response_model=PaginatedResponse)
async def list_dependencies(
    task_id: Optional[UUID] = Query(None, description="Filter by task ID (source or target)"),
    from_task_id: Optional[UUID] = Query(None, description="Filter by source task ID"),
    to_task_id: Optional[UUID] = Query(None, description="Filter by target task ID"),
    dependency_type: Optional[DependencyType] = Query(None, description="Filter by dependency type"),
    pagination: PaginationParams = Depends(),
    service: PlanningService = Depends(get_planning_service)
):
    """
    List dependencies with filtering and pagination.
    
    Args:
        task_id: Optional task ID filter (source or target)
        from_task_id: Optional source task ID filter
        to_task_id: Optional target task ID filter
        dependency_type: Optional dependency type filter
        pagination: Pagination parameters
        service: Planning service
        
    Returns:
        PaginatedResponse: Paginated list of dependencies
        
    Raises:
        HTTPException: If listing dependencies fails
    """
    logger.info(f"Listing dependencies (task_id={task_id}, from_task_id={from_task_id}, to_task_id={to_task_id}, dependency_type={dependency_type})")
    try:
        return await service.list_dependencies(
            task_id=task_id,
            from_task_id=from_task_id,
            to_task_id=to_task_id,
            dependency_type=dependency_type,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except Exception as e:
        logger.error(f"Error listing dependencies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing dependencies: {str(e)}"
        )

@router.put("/{dependency_id}", response_model=DependencyResponse)
async def update_dependency(
    dependency_data: DependencyUpdate,
    dependency_id: UUID = Path(..., description="Dependency ID"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Update a dependency.
    
    Args:
        dependency_data: Dependency data to update
        dependency_id: Dependency ID
        service: Planning service
        
    Returns:
        DependencyResponse: Updated dependency
        
    Raises:
        HTTPException: If dependency not found or update fails
    """
    logger.info(f"Updating dependency: {dependency_id}")
    try:
        return await service.update_dependency(dependency_id, dependency_data)
    except InvalidDependencyError as e:
        if "not found" in str(e).lower():
            logger.error(f"Dependency not found: {dependency_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dependency not found: {dependency_id}"
            )
        else:
            logger.error(f"Invalid dependency: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid dependency: {str(e)}"
            )
    except Exception as e:
        logger.error(f"Error updating dependency: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating dependency: {str(e)}"
        )

@router.delete("/{dependency_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dependency(
    dependency_id: UUID = Path(..., description="Dependency ID"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Delete a dependency.
    
    Args:
        dependency_id: Dependency ID
        service: Planning service
        
    Raises:
        HTTPException: If dependency not found or deletion fails
    """
    logger.info(f"Deleting dependency: {dependency_id}")
    try:
        await service.delete_dependency(dependency_id)
    except InvalidDependencyError as e:
        if "not found" in str(e).lower():
            logger.error(f"Dependency not found: {dependency_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dependency not found: {dependency_id}"
            )
        else:
            logger.error(f"Invalid dependency: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid dependency: {str(e)}"
            )
    except Exception as e:
        logger.error(f"Error deleting dependency: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting dependency: {str(e)}"
        )

@router.get("/task/{task_id}/dependencies", response_model=List[DependencyResponse])
async def get_task_dependencies(
    task_id: UUID = Path(..., description="Task ID"),
    direction: str = Query("outgoing", description="Direction of dependencies (outgoing, incoming, or both)"),
    service: PlanningService = Depends(get_planning_service)
):
    """
    Get dependencies for a specific task.
    
    Args:
        task_id: Task ID
        direction: Direction of dependencies (outgoing, incoming, or both)
        service: Planning service
        
    Returns:
        List[DependencyResponse]: List of dependencies
        
    Raises:
        HTTPException: If task not found or getting dependencies fails
    """
    logger.info(f"Getting {direction} dependencies for task: {task_id}")
    try:
        return await service.get_task_dependencies(task_id, direction)
    except TaskNotFoundError:
        logger.error(f"Task not found: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}"
        )
    except ValueError as e:
        logger.error(f"Invalid direction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid direction: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting task dependencies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting task dependencies: {str(e)}"
        )

@router.post("/validate-cycle", response_model=dict)
async def validate_dependency_cycle(
    from_task_id: UUID,
    to_task_id: UUID,
    service: PlanningService = Depends(get_planning_service)
):
    """
    Validate if adding a dependency would create a cycle.
    
    Args:
        from_task_id: Source task ID
        to_task_id: Target task ID
        service: Planning service
        
    Returns:
        dict: Validation result
        
    Raises:
        HTTPException: If validation fails
    """
    logger.info(f"Validating dependency cycle: {from_task_id} -> {to_task_id}")
    try:
        result = await service.validate_dependency_cycle(from_task_id, to_task_id)
        return {"would_create_cycle": result["would_create_cycle"], "cycle": result.get("cycle")}
    except TaskNotFoundError as e:
        logger.error(f"Task not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error validating dependency cycle: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating dependency cycle: {str(e)}"
        )
