"""
Project Facade service for Project Coordinator service.

This module provides a unified facade for all project-related operations, 
coordinating between various specialized services.
"""
import logging
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime

from fastapi import UploadFile

from ..config import Settings
from ..repositories.project import ProjectRepository
from ..models.api import (
    ProjectCreateRequest, ProjectUpdateRequest, ProjectResponse,
    ProjectStateTransitionRequest, ProjectProgressUpdateRequest,
    ResourceAllocationRequest, ResourceOptimizationRequest,
    ArtifactCreateRequest, AnalyticsType
)
from ..exceptions import ProjectNotFoundError, InvalidProjectStateError
from .lifecycle.manager import LifecycleManager
from .progress.tracker import ProgressTracker
from .resources.manager import ResourceManager
from .analytics.engine import AnalyticsEngine
from .artifacts.store import ArtifactStore


class ProjectFacade:
    """
    Project Facade service.
    
    This facade coordinates operations between specialized services and provides
    a simplified interface for the API layer.
    
    Attributes:
        project_repo: Project repository
        lifecycle_manager: Lifecycle management service
        progress_tracker: Progress tracking service
        resource_manager: Resource management service
        analytics_engine: Analytics generation service
        artifact_store: Artifact storage service
        settings: Application settings
        logger: Logger instance
    """
    
    def __init__(
        self,
        project_repo: ProjectRepository,
        lifecycle_manager: LifecycleManager,
        progress_tracker: ProgressTracker,
        resource_manager: ResourceManager,
        analytics_engine: AnalyticsEngine,
        artifact_store: ArtifactStore,
        settings: Settings,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the Project Facade service.
        
        Args:
            project_repo: Project repository
            lifecycle_manager: Lifecycle management service
            progress_tracker: Progress tracking service
            resource_manager: Resource management service
            analytics_engine: Analytics generation service
            artifact_store: Artifact storage service
            settings: Application settings
            logger: Logger instance (optional)
        """
        self.project_repo = project_repo
        self.lifecycle_manager = lifecycle_manager
        self.progress_tracker = progress_tracker
        self.resource_manager = resource_manager
        self.analytics_engine = analytics_engine
        self.artifact_store = artifact_store
        self.settings = settings
        self.logger = logger or logging.getLogger("project_facade")
    
    # Project CRUD operations
    
    async def create_project(self, project_data: ProjectCreateRequest) -> ProjectResponse:
        """
        Create a new project.
        
        Args:
            project_data: Project creation data
            
        Returns:
            Created project
        """
        self.logger.info(f"Creating project: {project_data.name}")
        
        # Create project in database
        project = self.project_repo.create(obj_in=project_data)
        
        # Initialize project state
        self.lifecycle_manager.initialize_project(project.id)
        
        # Convert to response model
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            owner_id=project.owner_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            metadata=project.project_metadata or {}
        )
    
    async def get_project(self, project_id: UUID) -> ProjectResponse:
        """
        Get project details.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project details
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        self.logger.info(f"Getting project: {project_id}")
        
        # Get project from database
        project = self.project_repo.get_project_or_404(project_id)
        
        # Convert to response model
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            owner_id=project.owner_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            metadata=project.project_metadata or {}
        )
    
    async def update_project(
        self, 
        project_id: UUID, 
        project_data: ProjectUpdateRequest
    ) -> ProjectResponse:
        """
        Update project details.
        
        Args:
            project_id: Project ID
            project_data: Project update data
            
        Returns:
            Updated project
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        self.logger.info(f"Updating project: {project_id}")
        
        # Get project from database
        project = self.project_repo.get_project_or_404(project_id)
        
        # Check if status is being updated
        if project_data.status is not None and project_data.status != project.status:
            # Handle state transition via lifecycle manager
            self.lifecycle_manager.transition_state(
                project_id=project_id,
                target_state=project_data.status,
                reason="Updated via API"
            )
        
        # Update project
        updated_project = self.project_repo.update(
            db_obj=project,
            obj_in=project_data.model_dump(exclude_unset=True)
        )
        
        # Convert to response model
        return ProjectResponse(
            id=updated_project.id,
            name=updated_project.name,
            description=updated_project.description,
            status=updated_project.status,
            owner_id=updated_project.owner_id,
            created_at=updated_project.created_at,
            updated_at=updated_project.updated_at,
            metadata=updated_project.project_metadata or {}
        )
    
    async def list_projects(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[ProjectResponse]:
        """
        List projects with optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional filter by status
            
        Returns:
            List of projects
        """
        self.logger.info(f"Listing projects (skip={skip}, limit={limit}, status={status})")
        
        # Prepare filters
        filters = {}
        if status:
            filters["status"] = status
        
        # Get projects from database
        projects = self.project_repo.get_multi(
            skip=skip,
            limit=limit,
            filters=filters
        )
        
        # Convert to response models
        return [
            ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                status=project.status,
                owner_id=project.owner_id,
                created_at=project.created_at,
                updated_at=project.updated_at,
            metadata=project.project_metadata or {}
            )
            for project in projects
        ]
    
    async def archive_project(self, project_id: UUID) -> ProjectResponse:
        """
        Archive a project.
        
        This is a specialized operation that transitions the project to ARCHIVED state.
        
        Args:
            project_id: Project ID
            
        Returns:
            Archived project
            
        Raises:
            ProjectNotFoundError: If project not found
            InvalidProjectStateError: If project cannot be archived in its current state
        """
        self.logger.info(f"Archiving project: {project_id}")
        
        # Use lifecycle manager to handle state transition
        self.lifecycle_manager.archive_project(project_id)
        
        # Get updated project
        project = self.project_repo.get_project_or_404(project_id)
        
        # Convert to response model
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            owner_id=project.owner_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            metadata=project.project_metadata or {}
        )
    
    # Lifecycle operations
    
    async def transition_state(
        self, 
        project_id: UUID, 
        transition_data: ProjectStateTransitionRequest
    ) -> ProjectResponse:
        """
        Transition project state.
        
        Args:
            project_id: Project ID
            transition_data: State transition data
            
        Returns:
            Updated project
            
        Raises:
            ProjectNotFoundError: If project not found
            InvalidProjectStateError: If state transition is invalid
        """
        self.logger.info(f"Transitioning project {project_id} to {transition_data.target_state}")
        
        # Use lifecycle manager to handle state transition
        self.lifecycle_manager.transition_state(
            project_id=project_id,
            target_state=transition_data.target_state,
            reason=transition_data.reason
        )
        
        # Get updated project
        project = self.project_repo.get_project_or_404(project_id)
        
        # Convert to response model
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            owner_id=project.owner_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            metadata=project.project_metadata or {}
        )
    
    async def get_state_history(self, project_id: UUID, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get project state transition history.
        
        Args:
            project_id: Project ID
            limit: Maximum number of records to return
            
        Returns:
            State transition history
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        self.logger.info(f"Getting state history for project: {project_id}")
        
        # Ensure project exists
        self.project_repo.get_project_or_404(project_id)
        
        # Get state history
        return self.lifecycle_manager.get_state_history(project_id, limit)
    
    # Progress tracking operations
    
    async def update_progress(
        self, 
        project_id: UUID, 
        progress_data: ProjectProgressUpdateRequest
    ) -> Dict[str, Any]:
        """
        Update project progress.
        
        Args:
            project_id: Project ID
            progress_data: Progress update data
            
        Returns:
            Updated progress record
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        self.logger.info(f"Updating progress for project {project_id}: {progress_data.percentage}%")
        
        # Use progress tracker to record progress
        return self.progress_tracker.record_progress(
            project_id=project_id,
            percentage=progress_data.percentage,
            metrics=progress_data.metrics,
            milestone=progress_data.milestone
        )
    
    async def get_progress(self, project_id: UUID) -> Dict[str, Any]:
        """
        Get current project progress.
        
        Args:
            project_id: Project ID
            
        Returns:
            Current progress
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        self.logger.info(f"Getting progress for project: {project_id}")
        
        # Use progress tracker to get current progress
        return self.progress_tracker.get_current_progress(project_id)
    
    async def get_progress_history(self, project_id: UUID, limit: int = 100) -> Dict[str, Any]:
        """
        Get project progress history.
        
        Args:
            project_id: Project ID
            limit: Maximum number of records to return
            
        Returns:
            Progress history
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        self.logger.info(f"Getting progress history for project: {project_id}")
        
        # Use progress tracker to get progress history
        return self.progress_tracker.get_progress_history(project_id, limit)
    
    # Resource operations
    
    async def allocate_resource(
        self, 
        project_id: UUID, 
        resource_data: ResourceAllocationRequest
    ) -> Dict[str, Any]:
        """
        Allocate a resource to a project.
        
        Args:
            project_id: Project ID
            resource_data: Resource allocation data
            
        Returns:
            Allocated resource
            
        Raises:
            ProjectNotFoundError: If project not found
            ResourceAllocationError: If resource allocation fails
        """
        self.logger.info(
            f"Allocating {resource_data.resource_type} resource {resource_data.resource_id} "
            f"to project {project_id} at {resource_data.allocation * 100}%"
        )
        
        # Use resource manager to allocate resource
        return self.resource_manager.allocate_resource(
            project_id=project_id,
            resource_type=resource_data.resource_type,
            resource_id=resource_data.resource_id,
            allocation=resource_data.allocation,
            start_date=resource_data.start_date,
            end_date=resource_data.end_date,
            metadata=resource_data.metadata
        )
    
    async def get_resources(
        self, 
        project_id: UUID,
        resource_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get resources allocated to a project.
        
        Args:
            project_id: Project ID
            resource_type: Optional filter by resource type
            
        Returns:
            List of allocated resources
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        self.logger.info(f"Getting resources for project: {project_id}")
        
        # Use resource manager to get resources
        return self.resource_manager.get_resources(
            project_id=project_id,
            resource_type=resource_type
        )
    
    async def optimize_resources(
        self, 
        project_id: UUID, 
        optimization_data: ResourceOptimizationRequest
    ) -> Dict[str, Any]:
        """
        Optimize resource allocation for a project.
        
        Args:
            project_id: Project ID
            optimization_data: Resource optimization data
            
        Returns:
            Optimization result
            
        Raises:
            ProjectNotFoundError: If project not found
            ResourceAllocationError: If resource optimization fails
        """
        self.logger.info(f"Optimizing resources for project {project_id} with target: {optimization_data.target}")
        
        # Use resource manager to optimize resources
        return self.resource_manager.optimize_resources(
            project_id=project_id,
            target=optimization_data.target,
            constraints=optimization_data.constraints
        )
    
    # Artifact operations
    
    async def add_artifact(
        self, 
        project_id: UUID, 
        artifact_data: ArtifactCreateRequest, 
        file: UploadFile
    ) -> Dict[str, Any]:
        """
        Add an artifact to a project.
        
        Args:
            project_id: Project ID
            artifact_data: Artifact metadata
            file: Uploaded file
            
        Returns:
            Created artifact
            
        Raises:
            ProjectNotFoundError: If project not found
            ArtifactStorageError: If artifact storage fails
        """
        self.logger.info(f"Adding artifact {artifact_data.name} to project {project_id}")
        
        # Use artifact store to save artifact
        return await self.artifact_store.store_artifact(
            project_id=project_id,
            artifact_data=artifact_data,
            file=file
        )
    
    async def get_artifacts(
        self, 
        project_id: UUID,
        artifact_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get artifacts for a project.
        
        Args:
            project_id: Project ID
            artifact_type: Optional filter by artifact type
            
        Returns:
            List of artifacts
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        self.logger.info(f"Getting artifacts for project: {project_id}")
        
        # Use artifact store to get artifacts
        return self.artifact_store.get_artifacts(
            project_id=project_id,
            artifact_type=artifact_type
        )
    
    async def get_artifact(self, project_id: UUID, artifact_id: UUID) -> Dict[str, Any]:
        """
        Get artifact details.
        
        Args:
            project_id: Project ID
            artifact_id: Artifact ID
            
        Returns:
            Artifact details
            
        Raises:
            ProjectNotFoundError: If project not found
            ArtifactStorageError: If artifact not found
        """
        self.logger.info(f"Getting artifact {artifact_id} from project {project_id}")
        
        # Use artifact store to get artifact
        return self.artifact_store.get_artifact(
            project_id=project_id,
            artifact_id=artifact_id
        )
    
    # Analytics operations
    
    async def generate_analytics(
        self, 
        project_id: UUID, 
        analytics_type: AnalyticsType,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate analytics for a project.
        
        Args:
            project_id: Project ID
            analytics_type: Type of analytics to generate
            parameters: Optional parameters for analytics generation
            
        Returns:
            Generated analytics
            
        Raises:
            ProjectNotFoundError: If project not found
            AnalyticsGenerationError: If analytics generation fails
        """
        self.logger.info(f"Generating {analytics_type} analytics for project {project_id}")
        
        # Use analytics engine to generate analytics
        return self.analytics_engine.generate_analytics(
            project_id=project_id,
            analytics_type=analytics_type,
            parameters=parameters
        )
    
    # Project Planning integration
    
    async def store_planning_results(
        self, 
        project_id: UUID, 
        planning_results: Dict[str, Any]
    ) -> ProjectResponse:
        """
        Store planning results for a project.
        
        This method is used by the Service Integration's Project Planning workflow
        to update the project with the results of planning.
        
        Args:
            project_id: Project ID
            planning_results: Planning results data
            
        Returns:
            Updated project
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        self.logger.info(f"Storing planning results for project {project_id}")
        
        # Get project from database
        project = self.project_repo.get_project_or_404(project_id)
        
        # Update project metadata with planning results
        metadata = project.project_metadata or {}
        metadata["planning"] = planning_results
        
        # Update project
        updated_project = self.project_repo.update(
            db_obj=project,
            obj_in={"project_metadata": metadata}
        )
        
        # Transition state to PLANNING
        self.lifecycle_manager.transition_state(
            project_id=project_id,
            target_state="PLANNING",
            reason="Planning results received"
        )
        
        # Convert to response model
        return ProjectResponse(
            id=updated_project.id,
            name=updated_project.name,
            description=updated_project.description,
            status=updated_project.status,
            owner_id=updated_project.owner_id,
            created_at=updated_project.created_at,
            updated_at=updated_project.updated_at,
            metadata=updated_project.project_metadata or {}
        )
