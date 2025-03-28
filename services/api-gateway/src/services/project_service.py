from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
from datetime import datetime

# Import shared modules
from shared.utils.src.logging import get_logger
from shared.utils.src.messaging import get_event_bus, get_command_bus
from shared.models.src.project import Project, ProjectCreate, ProjectUpdate, ProjectSummary, ProjectWithStats

# Import database models (these would be SQLAlchemy ORM models)
from ..models.project import ProjectModel
from ..models.agent import AgentModel
from ..models.task import TaskModel

# Setup logging
logger = get_logger(__name__)


class ProjectService:
    """
    Service for project operations.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the project service.
        
        Args:
            db: Database session
        """
        self.db = db
        
    async def get_projects(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[ProjectSummary]:
        """
        Get a list of projects.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by status
            
        Returns:
            List[ProjectSummary]: List of projects
        """
        # Build query
        query = select(ProjectModel).where(ProjectModel.owner_id == user_id)
        
        # Apply filters
        if status:
            query = query.where(ProjectModel.status == status)
            
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        projects = result.scalars().all()
        
        # Convert to Pydantic models
        return [ProjectSummary.from_orm(project) for project in projects]
        
    async def create_project(
        self,
        project: ProjectCreate,
        user_id: UUID,
    ) -> Project:
        """
        Create a new project.
        
        Args:
            project: Project data
            user_id: User ID
            
        Returns:
            Project: Created project
        """
        # Create project model
        db_project = ProjectModel(
            name=project.name,
            description=project.description,
            status=project.status,
            project_metadata=project.metadata,  # Using project_metadata field name to match the model
            owner_id=user_id,
        )
        
        # Add to database
        self.db.add(db_project)
        await self.db.commit()
        await self.db.refresh(db_project)
        
        # Publish event
        event_bus = get_event_bus()
        await event_bus.publish_event(
            event_type="project.created",
            data={"project_id": str(db_project.id), "user_id": str(user_id)},
        )
        
        # Convert to Pydantic model
        return Project.from_orm(db_project)
        
    async def get_project(
        self,
        project_id: UUID,
        user_id: UUID,
    ) -> Optional[Project]:
        """
        Get a project by ID.
        
        Args:
            project_id: Project ID
            user_id: User ID
            
        Returns:
            Optional[Project]: Project if found, None otherwise
        """
        # Build query
        query = (
            select(ProjectModel)
            .where(ProjectModel.id == project_id)
            .where(ProjectModel.owner_id == user_id)
        )
        
        # Execute query
        result = await self.db.execute(query)
        project = result.scalar_one_or_none()
        
        # Return None if not found
        if project is None:
            return None
            
        # Convert to Pydantic model
        return Project.from_orm(project)
        
    async def update_project(
        self,
        project_id: UUID,
        project: ProjectUpdate,
        user_id: UUID,
    ) -> Optional[Project]:
        """
        Update a project.
        
        Args:
            project_id: Project ID
            project: Project data
            user_id: User ID
            
        Returns:
            Optional[Project]: Updated project if found, None otherwise
        """
        # Get current project
        current_project = await self.get_project(project_id, user_id)
        
        # Return None if not found
        if current_project is None:
            return None
            
        # Build update values
        update_values = {}
        
        if project.name is not None:
            update_values["name"] = project.name
            
        if project.description is not None:
            update_values["description"] = project.description
            
        if project.status is not None:
            update_values["status"] = project.status
            
        if project.metadata is not None:
            update_values["project_metadata"] = project.metadata  # Using project_metadata field name to match the model
            
        # Add updated_at timestamp
        update_values["updated_at"] = datetime.utcnow()
        
        # Build query
        query = (
            update(ProjectModel)
            .where(ProjectModel.id == project_id)
            .where(ProjectModel.owner_id == user_id)
            .values(**update_values)
            .returning(ProjectModel)
        )
        
        # Execute query
        result = await self.db.execute(query)
        updated_project = result.scalar_one_or_none()
        
        # Commit changes
        await self.db.commit()
        
        # Return None if not found
        if updated_project is None:
            return None
            
        # Publish event
        event_bus = get_event_bus()
        await event_bus.publish_event(
            event_type="project.updated",
            data={"project_id": str(project_id), "user_id": str(user_id)},
        )
        
        # Convert to Pydantic model
        return Project.from_orm(updated_project)
        
    async def delete_project(
        self,
        project_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Delete a project.
        
        Args:
            project_id: Project ID
            user_id: User ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        # Build query
        query = (
            delete(ProjectModel)
            .where(ProjectModel.id == project_id)
            .where(ProjectModel.owner_id == user_id)
            .returning(ProjectModel.id)
        )
        
        # Execute query
        result = await self.db.execute(query)
        deleted_id = result.scalar_one_or_none()
        
        # Commit changes
        await self.db.commit()
        
        # Return False if not found
        if deleted_id is None:
            return False
            
        # Publish event
        event_bus = get_event_bus()
        await event_bus.publish_event(
            event_type="project.deleted",
            data={"project_id": str(project_id), "user_id": str(user_id)},
        )
        
        return True
        
    async def get_project_stats(
        self,
        project_id: UUID,
        user_id: UUID,
    ) -> Optional[ProjectWithStats]:
        """
        Get project statistics.
        
        Args:
            project_id: Project ID
            user_id: User ID
            
        Returns:
            Optional[ProjectWithStats]: Project with statistics if found, None otherwise
        """
        # Get project
        project = await self.get_project(project_id, user_id)
        
        # Return None if not found
        if project is None:
            return None
            
        # Get agent count
        agent_count_query = (
            select(func.count())
            .select_from(AgentModel)
            .where(AgentModel.project_id == project_id)
        )
        agent_count_result = await self.db.execute(agent_count_query)
        agent_count = agent_count_result.scalar_one()
        
        # Get task count
        task_count_query = (
            select(func.count())
            .select_from(TaskModel)
            .where(TaskModel.project_id == project_id)
        )
        task_count_result = await self.db.execute(task_count_query)
        task_count = task_count_result.scalar_one()
        
        # Get completed task count
        completed_task_count_query = (
            select(func.count())
            .select_from(TaskModel)
            .where(TaskModel.project_id == project_id)
            .where(TaskModel.status == "COMPLETED")
        )
        completed_task_count_result = await self.db.execute(completed_task_count_query)
        completed_task_count = completed_task_count_result.scalar_one()
        
        # Calculate progress percentage
        progress_percentage = 0.0
        if task_count > 0:
            progress_percentage = (completed_task_count / task_count) * 100.0
            
        # Create project with stats
        project_with_stats = ProjectWithStats(
            **project.dict(),
            agent_count=agent_count,
            task_count=task_count,
            completed_task_count=completed_task_count,
            progress_percentage=progress_percentage,
        )
        
        return project_with_stats
