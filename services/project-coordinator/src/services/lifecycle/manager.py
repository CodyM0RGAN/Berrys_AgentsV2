"""
Lifecycle Manager for Project Coordinator service.

This module implements the State Pattern for managing project lifecycle transitions.
"""
import logging
from typing import List, Dict, Any, Optional, Set
from uuid import UUID
from datetime import datetime

from shared.models.src.project import ProjectStatus
from ...repositories.project import ProjectRepository
from ...exceptions import InvalidProjectStateError, ProjectNotFoundError
from ...config import Settings


class LifecycleManager:
    """
    Lifecycle Manager for projects.
    
    This service manages project state transitions using a state machine pattern.
    It enforces valid state transitions and maintains transition history.
    
    Attributes:
        project_repo: Project repository
        settings: Application settings
        logger: Logger instance
        valid_transitions: Dictionary of valid state transitions
    """
    
    def __init__(
        self,
        project_repo: ProjectRepository,
        settings: Settings,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the Lifecycle Manager.
        
        Args:
            project_repo: Project repository
            settings: Application settings
            logger: Logger instance (optional)
        """
        self.project_repo = project_repo
        self.settings = settings
        self.logger = logger or logging.getLogger("lifecycle_manager")
        
        # Define valid state transitions as a state machine
        self.valid_transitions = {
            ProjectStatus.DRAFT: {ProjectStatus.PLANNING, ProjectStatus.ARCHIVED},
            ProjectStatus.PLANNING: {ProjectStatus.IN_PROGRESS, ProjectStatus.DRAFT, ProjectStatus.ARCHIVED},
            ProjectStatus.IN_PROGRESS: {ProjectStatus.PAUSED, ProjectStatus.COMPLETED, ProjectStatus.ARCHIVED},
            ProjectStatus.PAUSED: {ProjectStatus.IN_PROGRESS, ProjectStatus.ARCHIVED},
            ProjectStatus.COMPLETED: {ProjectStatus.ARCHIVED},
            ProjectStatus.ARCHIVED: set()  # Terminal state - no transitions out
        }
    
    def initialize_project(self, project_id: UUID) -> Dict[str, Any]:
        """
        Initialize a new project's lifecycle.
        
        This creates the initial state record for a newly created project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Initial state record
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        self.logger.info(f"Initializing lifecycle for project: {project_id}")
        
        # Get project to ensure it exists and get current state
        project = self.project_repo.get_project_or_404(project_id)
        
        # Create initial state record
        state_record = self.project_repo.add_state_transition(
            project_id=project_id,
            state=project.status,
            reason="Project created"
        )
        
        return {
            "id": state_record.id,
            "project_id": state_record.project_id,
            "state": state_record.state,
            "transitioned_at": state_record.transitioned_at,
            "reason": state_record.reason,
            "transitioned_by": state_record.transitioned_by
        }
    
    def transition_state(
        self, 
        project_id: UUID, 
        target_state: ProjectStatus,
        reason: Optional[str] = None,
        transitioned_by: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Transition a project to a new state.
        
        This enforces valid state transitions according to the state machine.
        
        Args:
            project_id: Project ID
            target_state: Target state
            reason: Reason for transition (optional)
            transitioned_by: User ID who performed the transition (optional)
            
        Returns:
            New state record
            
        Raises:
            ProjectNotFoundError: If project not found
            InvalidProjectStateError: If state transition is invalid
        """
        self.logger.info(f"Transitioning project {project_id} to {target_state}")
        
        # Get project to ensure it exists and get current state
        project = self.project_repo.get_project_or_404(project_id)
        current_state = project.status
        
        # Check if transition is valid
        if target_state not in self.valid_transitions.get(current_state, set()):
            allowed = list(self.valid_transitions.get(current_state, set()))
            raise InvalidProjectStateError(
                project_id=str(project_id),
                current_state=current_state,
                expected_states=allowed,
                message=f"Cannot transition from {current_state} to {target_state}. Allowed transitions: {', '.join(allowed)}"
            )
        
        # Create state transition record
        state_record = self.project_repo.add_state_transition(
            project_id=project_id,
            state=target_state,
            reason=reason,
            transitioned_by=transitioned_by
        )
        
        return {
            "id": state_record.id,
            "project_id": state_record.project_id,
            "state": state_record.state,
            "transitioned_at": state_record.transitioned_at,
            "reason": state_record.reason,
            "transitioned_by": state_record.transitioned_by
        }
    
    def get_state_history(self, project_id: UUID, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get state transition history for a project.
        
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
        states = self.project_repo.get_state_history(project_id, limit)
        
        return [
            {
                "id": state.id,
                "project_id": state.project_id,
                "state": state.state,
                "transitioned_at": state.transitioned_at,
                "reason": state.reason,
                "transitioned_by": state.transitioned_by
            }
            for state in states
        ]
    
    def get_current_state(self, project_id: UUID) -> Dict[str, Any]:
        """
        Get current state for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Current state
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        self.logger.info(f"Getting current state for project: {project_id}")
        
        # Get project to ensure it exists and get current state
        project = self.project_repo.get_project_or_404(project_id)
        
        return {
            "state": project.status,
            "valid_transitions": list(self.valid_transitions.get(project.status, set()))
        }
    
    def archive_project(self, project_id: UUID) -> Dict[str, Any]:
        """
        Archive a project.
        
        This is a specialized operation that transitions any project to ARCHIVED state,
        regardless of current state.
        
        Args:
            project_id: Project ID
            
        Returns:
            New state record
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        self.logger.info(f"Archiving project: {project_id}")
        
        # Get project to ensure it exists
        project = self.project_repo.get_project_or_404(project_id)
        
        # Skip if already archived
        if project.status == ProjectStatus.ARCHIVED:
            self.logger.info(f"Project {project_id} is already archived")
            return {
                "state": ProjectStatus.ARCHIVED,
                "message": "Project is already archived"
            }
        
        # Create state transition record
        state_record = self.project_repo.add_state_transition(
            project_id=project_id,
            state=ProjectStatus.ARCHIVED,
            reason="Project archived"
        )
        
        return {
            "id": state_record.id,
            "project_id": state_record.project_id,
            "state": state_record.state,
            "transitioned_at": state_record.transitioned_at,
            "reason": state_record.reason,
            "transitioned_by": state_record.transitioned_by
        }
    
    def get_allowed_transitions(self, state: ProjectStatus) -> List[ProjectStatus]:
        """
        Get allowed transitions for a given state.
        
        Args:
            state: Project state
            
        Returns:
            List of allowed target states
        """
        return list(self.valid_transitions.get(state, set()))
