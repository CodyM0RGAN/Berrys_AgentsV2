"""
Custom exceptions for the Project Coordinator service.

This module defines custom exceptions that the service can raise to indicate
various error conditions, with appropriate HTTP status codes and error messages.
"""
from typing import Optional, Dict, Any


class ProjectCoordinatorError(Exception):
    """
    Base exception for Project Coordinator service errors.
    
    Attributes:
        message: Error message
        status_code: HTTP status code
        error_code: Internal error code for more specific error handling
        details: Additional error details
    """
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "internal_error",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ProjectNotFoundError(ProjectCoordinatorError):
    """Raised when a project is not found."""
    def __init__(
        self,
        project_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = message or f"Project with ID {project_id} not found"
        super().__init__(
            message=message,
            status_code=404,
            error_code="project_not_found",
            details=details or {"project_id": project_id}
        )


class InvalidProjectStateError(ProjectCoordinatorError):
    """Raised when a project is in an invalid state for an operation."""
    def __init__(
        self,
        project_id: str,
        current_state: str,
        expected_states: list[str],
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = message or f"Project {project_id} is in state {current_state}, expected one of: {', '.join(expected_states)}"
        super().__init__(
            message=message,
            status_code=400,
            error_code="invalid_project_state",
            details=details or {
                "project_id": project_id,
                "current_state": current_state,
                "expected_states": expected_states
            }
        )


class ResourceAllocationError(ProjectCoordinatorError):
    """Raised when there is an error allocating resources."""
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code="resource_allocation_error",
            details=details or {"resource_type": resource_type}
        )


class ArtifactStorageError(ProjectCoordinatorError):
    """Raised when there is an error storing or retrieving artifacts."""
    def __init__(
        self,
        message: str,
        artifact_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code="artifact_storage_error",
            details=details or {"artifact_id": artifact_id}
        )


class ProjectLimitExceededError(ProjectCoordinatorError):
    """Raised when a project limit is exceeded."""
    def __init__(
        self,
        message: str,
        limit_type: str,
        current_value: int,
        max_value: int,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code="project_limit_exceeded",
            details=details or {
                "limit_type": limit_type,
                "current_value": current_value,
                "max_value": max_value
            }
        )


class AnalyticsGenerationError(ProjectCoordinatorError):
    """Raised when there is an error generating analytics."""
    def __init__(
        self,
        message: str,
        analytics_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code="analytics_generation_error",
            details=details or {"analytics_type": analytics_type}
        )


class InvalidTransitionError(ProjectCoordinatorError):
    """Raised when a state transition is invalid."""
    def __init__(
        self,
        from_state: str,
        to_state: str,
        allowed_transitions: list[str],
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = message or f"Cannot transition from {from_state} to {to_state}. Allowed transitions: {', '.join(allowed_transitions)}"
        super().__init__(
            message=message,
            status_code=400,
            error_code="invalid_transition",
            details=details or {
                "from_state": from_state,
                "to_state": to_state,
                "allowed_transitions": allowed_transitions
            }
        )


class DependencyError(ProjectCoordinatorError):
    """Raised when there is an error with dependencies."""
    def __init__(
        self,
        message: str,
        dependency_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code="dependency_error",
            details=details or {"dependency_type": dependency_type}
        )
