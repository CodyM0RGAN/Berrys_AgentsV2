"""
Project repository for Project Coordinator service.

This module provides repository implementation for Project and related entities.
"""
from typing import List, Optional, Dict, Any, Union, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from ..models.internal import (
    Project, ProjectState, ProjectProgress, 
    ProjectResource, ProjectArtifact, ProjectAnalytics
)
from ..models.api import (
    ProjectCreateRequest, ProjectUpdateRequest,
    ProjectStateTransitionRequest, ProjectProgressUpdateRequest,
    ResourceAllocationRequest, ArtifactCreateRequest
)
from ..exceptions import ProjectNotFoundError
from .base import BaseRepository


class ProjectRepository(BaseRepository[Project, ProjectCreateRequest, ProjectUpdateRequest]):
    """
    Repository for Project and related entities.
    
    This repository extends the BaseRepository with specific operations for 
    Project and its related entities.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the repository with database session.
        
        Args:
            db: SQLAlchemy session
        """
        super().__init__(db, Project)
    
    def get_with_relationships(
        self, 
        project_id: UUID,
        include_state_history: bool = False,
        include_progress: bool = False,
        include_resources: bool = False,
        include_artifacts: bool = False
    ) -> Optional[Project]:
        """
        Get a project by ID with optional related entities.
        
        Args:
            project_id: Project ID
            include_state_history: Whether to include state history
            include_progress: Whether to include progress records
            include_resources: Whether to include resources
            include_artifacts: Whether to include artifacts
            
        Returns:
            Project if found, None otherwise
        """
        query = self.db.query(Project)
        
        if include_state_history:
            query = query.options(joinedload(Project.state_history))
        
        if include_progress:
            query = query.options(joinedload(Project.progress_records))
        
        if include_resources:
            query = query.options(joinedload(Project.resources))
        
        if include_artifacts:
            query = query.options(joinedload(Project.artifacts))
        
        return query.filter(Project.id == project_id).first()
    
    def get_project_or_404(self, project_id: UUID) -> Project:
        """
        Get a project by ID or raise 404 error.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        project = self.get(project_id)
        if not project:
            raise ProjectNotFoundError(project_id=str(project_id))
        return project
    
    # State history methods
    
    def add_state_transition(
        self, 
        project_id: UUID, 
        state: str, 
        reason: Optional[str] = None,
        transitioned_by: Optional[UUID] = None
    ) -> ProjectState:
        """
        Record a state transition for a project.
        
        Args:
            project_id: Project ID
            state: New state
            reason: Reason for transition
            transitioned_by: User ID who performed the transition
            
        Returns:
            Created ProjectState record
        """
        # Ensure project exists
        project = self.get_project_or_404(project_id)
        
        # Create state transition
        state_record = ProjectState(
            project_id=project_id,
            state=state,
            reason=reason,
            transitioned_by=transitioned_by
        )
        
        self.db.add(state_record)
        
        # Update project state
        project.status = state
        self.db.add(project)
        
        self.db.commit()
        self.db.refresh(state_record)
        return state_record
    
    def get_state_history(
        self, 
        project_id: UUID,
        limit: int = 100
    ) -> List[ProjectState]:
        """
        Get state transition history for a project.
        
        Args:
            project_id: Project ID
            limit: Maximum number of records to return
            
        Returns:
            List of ProjectState records
        """
        return (
            self.db.query(ProjectState)
            .filter(ProjectState.project_id == project_id)
            .order_by(desc(ProjectState.transitioned_at))
            .limit(limit)
            .all()
        )
    
    # Progress tracking methods
    
    def add_progress_record(
        self,
        project_id: UUID,
        percentage: float,
        metrics: Optional[Dict[str, Any]] = None,
        milestone: Optional[str] = None
    ) -> ProjectProgress:
        """
        Record progress for a project.
        
        Args:
            project_id: Project ID
            percentage: Progress percentage (0-100)
            metrics: Additional metrics
            milestone: Optional milestone name
            
        Returns:
            Created ProjectProgress record
        """
        # Ensure project exists
        self.get_project_or_404(project_id)
        
        # Create progress record
        progress_record = ProjectProgress(
            project_id=project_id,
            percentage=percentage,
            metrics=metrics,
            milestone=milestone
        )
        
        self.db.add(progress_record)
        self.db.commit()
        self.db.refresh(progress_record)
        return progress_record
    
    def get_latest_progress(self, project_id: UUID) -> Optional[ProjectProgress]:
        """
        Get latest progress record for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Latest ProjectProgress record if any, None otherwise
        """
        return (
            self.db.query(ProjectProgress)
            .filter(ProjectProgress.project_id == project_id)
            .order_by(desc(ProjectProgress.recorded_at))
            .first()
        )
    
    def get_progress_history(
        self, 
        project_id: UUID,
        limit: int = 100
    ) -> List[ProjectProgress]:
        """
        Get progress history for a project.
        
        Args:
            project_id: Project ID
            limit: Maximum number of records to return
            
        Returns:
            List of ProjectProgress records
        """
        return (
            self.db.query(ProjectProgress)
            .filter(ProjectProgress.project_id == project_id)
            .order_by(desc(ProjectProgress.recorded_at))
            .limit(limit)
            .all()
        )
    
    # Resource methods
    
    def allocate_resource(
        self,
        project_id: UUID,
        resource_type: str,
        resource_id: str,
        allocation: float,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProjectResource:
        """
        Allocate a resource to a project.
        
        Args:
            project_id: Project ID
            resource_type: Resource type
            resource_id: Resource ID
            allocation: Allocation percentage (0.0-1.0)
            start_date: Optional start date
            end_date: Optional end date
            metadata: Additional metadata
            
        Returns:
            Created ProjectResource record
        """
        # Ensure project exists
        self.get_project_or_404(project_id)
        
        # Create resource allocation
        resource = ProjectResource(
            project_id=project_id,
            resource_type=resource_type,
            resource_id=resource_id,
            allocation=allocation,
            start_date=start_date,
            end_date=end_date,
            resource_metadata=metadata
        )
        
        self.db.add(resource)
        self.db.commit()
        self.db.refresh(resource)
        return resource
    
    def get_project_resources(
        self, 
        project_id: UUID,
        resource_type: Optional[str] = None
    ) -> List[ProjectResource]:
        """
        Get resources allocated to a project.
        
        Args:
            project_id: Project ID
            resource_type: Optional filter by resource type
            
        Returns:
            List of ProjectResource records
        """
        query = (
            self.db.query(ProjectResource)
            .filter(ProjectResource.project_id == project_id)
            .filter(ProjectResource.released_at.is_(None))
        )
        
        if resource_type:
            query = query.filter(ProjectResource.resource_type == resource_type)
        
        return query.all()
    
    def release_resource(
        self,
        resource_id: UUID
    ) -> ProjectResource:
        """
        Release a resource allocation.
        
        Args:
            resource_id: Resource allocation ID
            
        Returns:
            Updated ProjectResource record
        """
        resource = self.db.query(ProjectResource).get(resource_id)
        if resource:
            resource.released_at = datetime.utcnow()
            self.db.add(resource)
            self.db.commit()
            self.db.refresh(resource)
        
        return resource
        
    def update_resource_allocation(
        self,
        resource_id: UUID,
        allocation: float
    ) -> ProjectResource:
        """
        Update the allocation percentage of a resource.
        
        Args:
            resource_id: Resource allocation ID
            allocation: New allocation percentage (0.0-1.0)
            
        Returns:
            Updated ProjectResource record
        """
        resource = self.db.query(ProjectResource).get(resource_id)
        if resource:
            resource.allocation = allocation
            self.db.add(resource)
            self.db.commit()
            self.db.refresh(resource)
        
        return resource
    
    # Artifact methods
    
    def add_artifact(
        self,
        project_id: UUID,
        name: str,
        artifact_type: str,
        storage_path: str,
        size_bytes: int,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProjectArtifact:
        """
        Add an artifact to a project.
        
        Args:
            project_id: Project ID
            name: Artifact name
            artifact_type: Artifact type
            storage_path: Path where artifact is stored
            size_bytes: Size in bytes
            description: Optional description
            metadata: Additional metadata
            
        Returns:
            Created ProjectArtifact record
        """
        # Ensure project exists
        self.get_project_or_404(project_id)
        
        # Create artifact
        artifact = ProjectArtifact(
            project_id=project_id,
            name=name,
            type=artifact_type,
            storage_path=storage_path,
            size_bytes=size_bytes,
            description=description,
            artifact_metadata=metadata
        )
        
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact
    
    def get_project_artifacts(
        self, 
        project_id: UUID,
        artifact_type: Optional[str] = None
    ) -> List[ProjectArtifact]:
        """
        Get artifacts for a project.
        
        Args:
            project_id: Project ID
            artifact_type: Optional filter by artifact type
            
        Returns:
            List of ProjectArtifact records
        """
        query = (
            self.db.query(ProjectArtifact)
            .filter(ProjectArtifact.project_id == project_id)
        )
        
        if artifact_type:
            query = query.filter(ProjectArtifact.type == artifact_type)
        
        return query.all()
    
    def get_artifact(self, artifact_id: UUID) -> Optional[ProjectArtifact]:
        """
        Get an artifact by ID.
        
        Args:
            artifact_id: Artifact ID
            
        Returns:
            ProjectArtifact if found, None otherwise
        """
        return self.db.query(ProjectArtifact).get(artifact_id)
    
    def delete_artifact(self, artifact_id: UUID) -> None:
        """
        Delete an artifact by ID.
        
        Args:
            artifact_id: Artifact ID
            
        Returns:
            None
        """
        artifact = self.db.query(ProjectArtifact).get(artifact_id)
        if artifact:
            self.db.delete(artifact)
            self.db.commit()
    
    # Analytics methods
    
    def save_analytics(
        self,
        project_id: UUID,
        analytics_type: str,
        data: Dict[str, Any],
        visualization_config: Optional[Dict[str, Any]] = None,
        expiry: Optional[datetime] = None
    ) -> ProjectAnalytics:
        """
        Save analytics data for a project.
        
        Args:
            project_id: Project ID
            analytics_type: Analytics type
            data: Analytics data
            visualization_config: Optional visualization configuration
            expiry: Optional expiry date for cached analytics
            
        Returns:
            Created ProjectAnalytics record
        """
        # Ensure project exists
        self.get_project_or_404(project_id)
        
        # Create analytics
        analytics = ProjectAnalytics(
            project_id=project_id,
            analytics_type=analytics_type,
            data=data,
            visualization_config=visualization_config,
            expiry=expiry
        )
        
        self.db.add(analytics)
        self.db.commit()
        self.db.refresh(analytics)
        return analytics
    
    def get_latest_analytics(
        self,
        project_id: UUID,
        analytics_type: str
    ) -> Optional[ProjectAnalytics]:
        """
        Get latest analytics data for a project and type.
        
        Args:
            project_id: Project ID
            analytics_type: Analytics type
            
        Returns:
            ProjectAnalytics if found, None otherwise
        """
        return (
            self.db.query(ProjectAnalytics)
            .filter(ProjectAnalytics.project_id == project_id)
            .filter(ProjectAnalytics.analytics_type == analytics_type)
            .order_by(desc(ProjectAnalytics.generated_at))
            .first()
        )
