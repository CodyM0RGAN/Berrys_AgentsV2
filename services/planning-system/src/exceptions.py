"""
Planning System Service custom exceptions.

This module defines custom exception classes for the Planning System service,
including error codes and HTTP status codes.
"""

from fastapi import status
from typing import Optional, Dict, Any

class PlanningSystemError(Exception):
    """Base exception for Planning System errors"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "PLANNING_SYSTEM_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            error_code: Error code for client identification
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)
    
    def __str__(self) -> str:
        return self.message


class PlanNotFoundError(PlanningSystemError):
    """Raised when a plan is not found"""
    
    def __init__(
        self,
        plan_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            plan_id: ID of the plan that was not found
            message: Optional custom error message
            details: Additional error details
        """
        default_message = f"Plan with ID {plan_id} not found"
        super().__init__(
            message=message or default_message,
            error_code="PLAN_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"plan_id": plan_id, **(details or {})},
        )


class TaskNotFoundError(PlanningSystemError):
    """Raised when a task is not found"""
    
    def __init__(
        self,
        task_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            task_id: ID of the task that was not found
            message: Optional custom error message
            details: Additional error details
        """
        default_message = f"Task with ID {task_id} not found"
        super().__init__(
            message=message or default_message,
            error_code="TASK_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": task_id, **(details or {})},
        )


class InvalidDependencyError(PlanningSystemError):
    """Raised when a dependency is invalid"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="INVALID_DEPENDENCY",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class CyclicDependencyError(InvalidDependencyError):
    """Raised when a cyclic dependency is detected"""
    
    def __init__(
        self,
        cycle: list,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            cycle: List of task IDs forming a cycle
            message: Optional custom error message
            details: Additional error details
        """
        default_message = f"Cyclic dependency detected in tasks: {', '.join(str(task_id) for task_id in cycle)}"
        super().__init__(
            message=message or default_message,
            details={"cycle": cycle, **(details or {})},
        )
        self.error_code = "CYCLIC_DEPENDENCY"


class ResourceAllocationError(PlanningSystemError):
    """Raised when resource allocation fails"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="RESOURCE_ALLOCATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class OptimizationTimeoutError(ResourceAllocationError):
    """Raised when resource optimization times out"""
    
    def __init__(
        self,
        timeout_seconds: int,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            timeout_seconds: Timeout in seconds
            message: Optional custom error message
            details: Additional error details
        """
        default_message = f"Resource optimization timed out after {timeout_seconds} seconds"
        super().__init__(
            message=message or default_message,
            details={"timeout_seconds": timeout_seconds, **(details or {})},
        )
        self.error_code = "OPTIMIZATION_TIMEOUT"


class InfeasibleAllocationError(ResourceAllocationError):
    """Raised when resource allocation is infeasible"""
    
    def __init__(
        self,
        constraints: list,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            constraints: List of violated constraints
            message: Optional custom error message
            details: Additional error details
        """
        default_message = "Resource allocation is infeasible with the given constraints"
        super().__init__(
            message=message or default_message,
            details={"violated_constraints": constraints, **(details or {})},
        )
        self.error_code = "INFEASIBLE_ALLOCATION"


class ForecastingError(PlanningSystemError):
    """Raised when forecasting fails"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="FORECASTING_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class InsufficientDataError(ForecastingError):
    """Raised when insufficient data is available for forecasting"""
    
    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Optional custom error message
            details: Additional error details
        """
        default_message = "Insufficient historical data for accurate forecasting"
        super().__init__(
            message=message or default_message,
            details=details,
        )
        self.error_code = "INSUFFICIENT_DATA"
        self.status_code = status.HTTP_400_BAD_REQUEST


class PlanValidationError(PlanningSystemError):
    """Raised when a plan validation fails"""
    
    def __init__(
        self,
        message: str,
        validation_errors: list,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            validation_errors: List of validation errors
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="PLAN_VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"validation_errors": validation_errors, **(details or {})},
        )


class TaskValidationError(PlanningSystemError):
    """Raised when a task validation fails"""
    
    def __init__(
        self,
        message: str,
        validation_errors: list,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            validation_errors: List of validation errors
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="TASK_VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"validation_errors": validation_errors, **(details or {})},
        )
