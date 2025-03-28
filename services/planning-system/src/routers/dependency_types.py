"""
Dependency Types router for the Planning System service.

This module implements API endpoints for managing dependency types.
"""

from fastapi import APIRouter, Depends, Path, Query, HTTPException, status
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..models.api import (
    DependencyType,
    DependencyTypeInfo
)
from ..services.dependency_type_service import DependencyTypeService
from ..dependencies import get_dependency_type_service

router = APIRouter(
    prefix="/dependency-types",
    tags=["dependency-types"],
)

@router.get("", response_model=List[DependencyTypeInfo])
async def get_dependency_types(
    dependency_type_service: DependencyTypeService = Depends(get_dependency_type_service),
):
    """
    Get all dependency types.
    """
    return await dependency_type_service.get_dependency_types()

@router.get("/{dependency_type}", response_model=DependencyTypeInfo)
async def get_dependency_type_info(
    dependency_type: str = Path(..., description="Dependency type"),
    dependency_type_service: DependencyTypeService = Depends(get_dependency_type_service),
):
    """
    Get information about a specific dependency type.
    """
    info = await dependency_type_service.get_dependency_type_info(dependency_type)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dependency type '{dependency_type}' not found"
        )
    return info

@router.post("/{dependency_type}/validate", response_model=List[str])
async def validate_dependency_type(
    dependency_type: str = Path(..., description="Dependency type"),
    from_task_id: UUID = Query(..., description="Source task ID"),
    to_task_id: UUID = Query(..., description="Target task ID"),
    lag: Optional[int] = Query(None, description="Lag value"),
    dependency_type_service: DependencyTypeService = Depends(get_dependency_type_service),
):
    """
    Validate a dependency type for a specific dependency.
    """
    validation_errors = await dependency_type_service.validate_dependency_type(
        dependency_type=dependency_type,
        from_task_id=from_task_id,
        to_task_id=to_task_id,
        lag=lag
    )
    return validation_errors

@router.post("/{dependency_type}/calculate-dates", response_model=Dict[str, Any])
async def calculate_task_dates(
    dependency_type: str = Path(..., description="Dependency type"),
    task_id: UUID = Query(..., description="Task ID"),
    predecessor_id: UUID = Query(..., description="Predecessor task ID"),
    lag: int = Query(0, description="Lag value in hours"),
    dependency_type_service: DependencyTypeService = Depends(get_dependency_type_service),
):
    """
    Calculate task dates based on dependency type and predecessor.
    """
    dates = await dependency_type_service.calculate_task_dates(
        task_id=task_id,
        dependency_type=dependency_type,
        predecessor_id=predecessor_id,
        lag=lag
    )
    return {
        "earliest_start": dates["earliest_start"].isoformat(),
        "earliest_finish": dates["earliest_finish"].isoformat()
    }

@router.get("/plan/{plan_id}/visualization", response_model=Dict[str, Any])
async def get_dependency_visualization(
    plan_id: UUID = Path(..., description="Plan ID"),
    dependency_type_service: DependencyTypeService = Depends(get_dependency_type_service),
):
    """
    Get visualization data for dependencies in a plan.
    """
    return await dependency_type_service.get_dependency_visualization_data(plan_id)

@router.get("/plan/{plan_id}/analysis", response_model=Dict[str, Any])
async def analyze_dependency_network(
    plan_id: UUID = Path(..., description="Plan ID"),
    dependency_type_service: DependencyTypeService = Depends(get_dependency_type_service),
):
    """
    Analyze the dependency network for a plan.
    """
    return await dependency_type_service.analyze_dependency_network(plan_id)
