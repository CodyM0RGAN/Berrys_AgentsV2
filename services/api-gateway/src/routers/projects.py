from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

# Import shared modules
from shared.utils.src.auth import get_current_user, require_permission
from shared.utils.src.logging import get_logger

# Import local modules
from ..database import get_db
from shared.models.src.project import (
    Project, ProjectCreate, ProjectUpdate, ProjectSummary, ProjectWithStats
)
from shared.models.src.user import User, Permission

# Import services
from ..services.project_service import ProjectService

# Setup logging
logger = get_logger(__name__)

# Create router
router = APIRouter()


@router.get("/", response_model=List[ProjectSummary])
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a list of projects.
    """
    logger.info(f"Getting projects for user {current_user.id}")
    
    # Create service
    project_service = ProjectService(db)
    
    # Get projects
    projects = await project_service.get_projects(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status=status,
    )
    
    return projects


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(require_permission(Permission.CREATE_PROJECT)),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new project.
    """
    logger.info(f"Creating project for user {current_user.id}")
    
    # Create service
    project_service = ProjectService(db)
    
    # Create project
    project = await project_service.create_project(
        project=project,
        user_id=current_user.id,
    )
    
    return project


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: UUID = Path(...),
    current_user: User = Depends(require_permission(Permission.VIEW_PROJECT)),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a project by ID.
    """
    logger.info(f"Getting project {project_id} for user {current_user.id}")
    
    # Create service
    project_service = ProjectService(db)
    
    # Get project
    project = await project_service.get_project(
        project_id=project_id,
        user_id=current_user.id,
    )
    
    # Check if project exists
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    return project


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project: ProjectUpdate,
    project_id: UUID = Path(...),
    current_user: User = Depends(require_permission(Permission.EDIT_PROJECT)),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a project.
    """
    logger.info(f"Updating project {project_id} for user {current_user.id}")
    
    # Create service
    project_service = ProjectService(db)
    
    # Update project
    updated_project = await project_service.update_project(
        project_id=project_id,
        project=project,
        user_id=current_user.id,
    )
    
    # Check if project exists
    if updated_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    return updated_project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID = Path(...),
    current_user: User = Depends(require_permission(Permission.DELETE_PROJECT)),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a project.
    """
    logger.info(f"Deleting project {project_id} for user {current_user.id}")
    
    # Create service
    project_service = ProjectService(db)
    
    # Delete project
    success = await project_service.delete_project(
        project_id=project_id,
        user_id=current_user.id,
    )
    
    # Check if project exists
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )


@router.get("/{project_id}/stats", response_model=ProjectWithStats)
async def get_project_stats(
    project_id: UUID = Path(...),
    current_user: User = Depends(require_permission(Permission.VIEW_PROJECT)),
    db: AsyncSession = Depends(get_db),
):
    """
    Get project statistics.
    """
    logger.info(f"Getting stats for project {project_id} for user {current_user.id}")
    
    # Create service
    project_service = ProjectService(db)
    
    # Get project stats
    project_stats = await project_service.get_project_stats(
        project_id=project_id,
        user_id=current_user.id,
    )
    
    # Check if project exists
    if project_stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    return project_stats
