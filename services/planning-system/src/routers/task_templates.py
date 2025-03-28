"""
Task Templates router for the Planning System service.

This module implements API endpoints for managing task templates.
"""

from fastapi import APIRouter, Depends, Path, Query, HTTPException, status
from typing import List, Optional
from uuid import UUID

from ..models.api import (
    TaskTemplateCreate,
    TaskTemplateUpdate,
    TaskTemplateResponse,
    TaskTemplateListResponse,
    PaginatedResponse,
    PlanningTaskCreate
)
from ..services.task_template_service import TaskTemplateService
from ..dependencies import get_task_template_service

router = APIRouter(
    prefix="/task-templates",
    tags=["task-templates"],
)

@router.post("", response_model=TaskTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_task_template(
    template_data: TaskTemplateCreate,
    task_template_service: TaskTemplateService = Depends(get_task_template_service),
):
    """
    Create a new task template.
    """
    return await task_template_service.create_template(template_data)

@router.get("/{template_id}", response_model=TaskTemplateResponse)
async def get_task_template(
    template_id: UUID = Path(..., description="Task template ID"),
    task_template_service: TaskTemplateService = Depends(get_task_template_service),
):
    """
    Get a task template by ID.
    """
    return await task_template_service.get_template(template_id)

@router.get("", response_model=PaginatedResponse)
async def list_task_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    task_template_service: TaskTemplateService = Depends(get_task_template_service),
):
    """
    List task templates with filtering and pagination.
    """
    return await task_template_service.list_templates(
        category=category,
        tags=tags,
        page=page,
        page_size=page_size
    )

@router.put("/{template_id}", response_model=TaskTemplateResponse)
async def update_task_template(
    template_data: TaskTemplateUpdate,
    template_id: UUID = Path(..., description="Task template ID"),
    task_template_service: TaskTemplateService = Depends(get_task_template_service),
):
    """
    Update a task template.
    """
    return await task_template_service.update_template(template_id, template_data)

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_template(
    template_id: UUID = Path(..., description="Task template ID"),
    task_template_service: TaskTemplateService = Depends(get_task_template_service),
):
    """
    Delete a task template.
    """
    await task_template_service.delete_template(template_id)
    return None

@router.post("/{template_id}/generate-task", response_model=PlanningTaskCreate)
async def generate_task_from_template(
    template_id: UUID = Path(..., description="Task template ID"),
    plan_id: UUID = Query(..., description="Plan ID"),
    phase_id: Optional[UUID] = Query(None, description="Phase ID"),
    milestone_id: Optional[UUID] = Query(None, description="Milestone ID"),
    task_template_service: TaskTemplateService = Depends(get_task_template_service),
):
    """
    Generate a task from a template.
    """
    return await task_template_service.generate_task_from_template(
        template_id=template_id,
        plan_id=plan_id,
        phase_id=phase_id,
        milestone_id=milestone_id
    )

@router.post("/generate-acceptance-criteria", response_model=List[str])
async def generate_acceptance_criteria(
    task_description: str = Query(..., description="Task description"),
    task_type: Optional[str] = Query(None, description="Task type"),
    num_criteria: int = Query(3, ge=1, le=10, description="Number of criteria to generate"),
    task_template_service: TaskTemplateService = Depends(get_task_template_service),
):
    """
    Generate acceptance criteria for a task.
    """
    return await task_template_service.generate_acceptance_criteria(
        task_description=task_description,
        task_type=task_type,
        num_criteria=num_criteria
    )
