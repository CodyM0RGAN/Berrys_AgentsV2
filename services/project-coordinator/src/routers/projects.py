"""
Projects router for the Project Coordinator service.

This module provides API endpoints for project CRUD operations.
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse

from ..dependencies import get_project_facade
from ..models.api import (
    ProjectCreateRequest, ProjectUpdateRequest, ProjectResponse,
    ProjectListResponse
)
from ..exceptions import ProjectNotFoundError, ProjectCoordinatorError
from ..services.project_facade import ProjectFacade


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new project with the provided information."
)
async def create_project(
    project_data: ProjectCreateRequest,
    project_facade: ProjectFacade = Depends(get_project_facade)
) -> ProjectResponse:
    """
    Create a new project.
    
    Args:
        project_data: Project creation data
        project_facade: Project facade service
        
    Returns:
        Created project
    """
    return await project_facade.create_project(project_data)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project details",
    description="Get detailed information about a specific project."
)
async def get_project(
    project_id: UUID = Path(..., description="Project ID"),
    project_facade: ProjectFacade = Depends(get_project_facade)
) -> ProjectResponse:
    """
    Get project details.
    
    Args:
        project_id: Project ID
        project_facade: Project facade service
        
    Returns:
        Project details
        
    Raises:
        HTTPException: If project not found
    """
    try:
        return await project_facade.get_project(project_id)
    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    description="Update an existing project with the provided information."
)
async def update_project(
    project_data: ProjectUpdateRequest,
    project_id: UUID = Path(..., description="Project ID"),
    project_facade: ProjectFacade = Depends(get_project_facade)
) -> ProjectResponse:
    """
    Update a project.
    
    Args:
        project_data: Project update data
        project_id: Project ID
        project_facade: Project facade service
        
    Returns:
        Updated project
        
    Raises:
        HTTPException: If project not found
    """
    try:
        return await project_facade.update_project(project_id, project_data)
    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ProjectCoordinatorError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )


@router.get(
    "/",
    response_model=ProjectListResponse,
    summary="List projects",
    description="Get a list of projects with optional filtering."
)
async def list_projects(
    skip: int = Query(0, description="Skip N projects", ge=0),
    limit: int = Query(100, description="Limit to N projects", ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status"),
    project_facade: ProjectFacade = Depends(get_project_facade)
) -> ProjectListResponse:
    """
    List projects.
    
    Args:
        skip: Number of projects to skip
        limit: Maximum number of projects to return
        status: Optional filter by status
        project_facade: Project facade service
        
    Returns:
        List of projects
    """
    projects = await project_facade.list_projects(skip, limit, status)
    return ProjectListResponse(
        projects=projects,
        total=len(projects),
        page=skip // limit + 1,
        page_size=limit
    )


@router.post(
    "/{project_id}/archive",
    response_model=ProjectResponse,
    summary="Archive project",
    description="Archive a project, changing its status to ARCHIVED."
)
async def archive_project(
    project_id: UUID = Path(..., description="Project ID"),
    project_facade: ProjectFacade = Depends(get_project_facade)
) -> ProjectResponse:
    """
    Archive a project.
    
    Args:
        project_id: Project ID
        project_facade: Project facade service
        
    Returns:
        Archived project
        
    Raises:
        HTTPException: If project not found or cannot be archived
    """
    try:
        return await project_facade.archive_project(project_id)
    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ProjectCoordinatorError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
