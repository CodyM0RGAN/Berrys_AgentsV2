"""
Validation strategies for the Planning System service.

This module provides validation strategies for various entities
in the planning system, following the strategy pattern.
"""

from typing import List, Dict, Any, Optional, Type
from datetime import datetime
from uuid import UUID

from .base import ValidationStrategy
from ..models.api import (
    StrategicPlanCreate, 
    StrategicPlanUpdate,
    PlanningTaskCreate,
    PlanningTaskUpdate,
    PlanStatus,
    TaskStatus
)

class PlanValidator(ValidationStrategy):
    """
    Validation strategy for strategic plans.
    
    This strategy validates strategic plan data for creation
    and updates.
    """
    
    async def validate(
        self, 
        data: Any, 
        context: Dict[str, Any] = None
    ) -> List[str]:
        """
        Validate plan data.
        
        Args:
            data: Plan data to validate
            context: Additional validation context
            
        Returns:
            List[str]: Validation error messages, empty if valid
        """
        validation_errors = []
        
        # Determine validation type
        is_update = context and context.get("operation") == "update"
        existing_plan = context.get("existing_entity") if context else None
        
        # Validate objectives
        objectives = getattr(data, "objectives", None)
        if objectives is not None:
            if not objectives.get("goal"):
                validation_errors.append("Objectives must have a goal")
            
            if not objectives.get("success_criteria"):
                validation_errors.append("Objectives must have success criteria")
        
        # Validate status transition for updates
        if is_update and hasattr(data, "status") and data.status is not None:
            new_status = data.status
            current_status = existing_plan.status if existing_plan else None
            
            if current_status and new_status != current_status:
                # Define valid status transitions
                valid_transitions = {
                    PlanStatus.DRAFT: [PlanStatus.ACTIVE, PlanStatus.ARCHIVED, PlanStatus.CANCELLED],
                    PlanStatus.ACTIVE: [PlanStatus.COMPLETED, PlanStatus.ARCHIVED, PlanStatus.CANCELLED],
                    PlanStatus.COMPLETED: [PlanStatus.ARCHIVED],
                    PlanStatus.ARCHIVED: [],
                    PlanStatus.CANCELLED: [PlanStatus.ARCHIVED],
                }
                
                if new_status not in valid_transitions.get(current_status, []):
                    validation_errors.append(f"Invalid status transition: {current_status} -> {new_status}")
        
        # Add more validations as needed for plans
        
        return validation_errors


class TaskValidator(ValidationStrategy):
    """
    Validation strategy for planning tasks.
    
    This strategy validates planning task data for creation
    and updates.
    """
    
    async def validate(
        self, 
        data: Any, 
        context: Dict[str, Any] = None
    ) -> List[str]:
        """
        Validate task data.
        
        Args:
            data: Task data to validate
            context: Additional validation context
            
        Returns:
            List[str]: Validation error messages, empty if valid
        """
        validation_errors = []
        
        # Determine validation type
        is_update = context and context.get("operation") == "update"
        existing_task = context.get("existing_entity") if context else None
        
        # Validate required skills if present
        if hasattr(data, "required_skills") and data.required_skills:
            for skill, proficiency in data.required_skills.items():
                if not isinstance(proficiency, (int, float)) or proficiency < 0 or proficiency > 1:
                    validation_errors.append(f"Skill proficiency for {skill} must be between 0 and 1")
        
        # Validate estimated duration and effort consistency
        if hasattr(data, "estimated_duration") and hasattr(data, "estimated_effort"):
            duration = data.estimated_duration
            effort = data.estimated_effort
            
            # For create operation, both are required
            if not is_update and duration is not None and effort is not None:
                if effort < duration:
                    validation_errors.append("Estimated effort cannot be less than estimated duration")
            
            # For update operation, compare with existing values
            elif is_update:
                if duration is not None and effort is not None:
                    if effort < duration:
                        validation_errors.append("Estimated effort cannot be less than estimated duration")
                elif duration is not None and existing_task and hasattr(existing_task, "estimated_effort"):
                    if existing_task.estimated_effort < duration:
                        validation_errors.append("Estimated effort cannot be less than estimated duration")
                elif effort is not None and existing_task and hasattr(existing_task, "estimated_duration"):
                    if effort < existing_task.estimated_duration:
                        validation_errors.append("Estimated effort cannot be less than estimated duration")
        
        # Validate status transition for updates
        if is_update and hasattr(data, "status") and data.status is not None:
            new_status = data.status
            current_status = existing_task.status if existing_task else None
            
            if current_status and new_status != current_status:
                # Define valid status transitions
                valid_transitions = {
                    TaskStatus.PLANNED: [TaskStatus.READY, TaskStatus.CANCELLED],
                    TaskStatus.READY: [TaskStatus.IN_PROGRESS, TaskStatus.PLANNED, TaskStatus.CANCELLED],
                    TaskStatus.IN_PROGRESS: [TaskStatus.COMPLETED, TaskStatus.BLOCKED, TaskStatus.CANCELLED],
                    TaskStatus.BLOCKED: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
                    TaskStatus.COMPLETED: [TaskStatus.IN_PROGRESS],  # Allow reverting if needed
                    TaskStatus.CANCELLED: [TaskStatus.PLANNED],  # Allow re-opening
                }
                
                if new_status not in valid_transitions.get(current_status, []):
                    validation_errors.append(f"Invalid status transition: {current_status} -> {new_status}")
        
        # Add more validations as needed for tasks
        
        return validation_errors


class DependencyValidator(ValidationStrategy):
    """
    Validation strategy for task dependencies.
    
    This strategy validates dependency data for creation
    and updates.
    """
    
    async def validate(
        self, 
        data: Any, 
        context: Dict[str, Any] = None
    ) -> List[str]:
        """
        Validate dependency data.
        
        Args:
            data: Dependency data to validate
            context: Additional validation context
            
        Returns:
            List[str]: Validation error messages, empty if valid
        """
        validation_errors = []
        
        # Check for circular dependency if context provides the tasks
        from_task_id = getattr(data, "from_task_id", None)
        to_task_id = getattr(data, "to_task_id", None)
        
        if from_task_id and to_task_id:
            # Simple case: self-dependency
            if from_task_id == to_task_id:
                validation_errors.append("A task cannot depend on itself")
            
            # For deeper cycle detection, we would need dependency graph
            # This would typically be handled in the DependencyManager component
            if context and "dependency_manager" in context:
                dependency_manager = context["dependency_manager"]
                if await dependency_manager.would_create_cycle(from_task_id, to_task_id):
                    validation_errors.append("This dependency would create a circular reference")
        
        # Validate lag is non-negative
        if hasattr(data, "lag") and data.lag is not None and data.lag < 0:
            validation_errors.append("Lag time cannot be negative")
        
        return validation_errors


class ValidationFactory:
    """
    Factory for creating validation strategies.
    
    This factory provides access to the appropriate validation
    strategy for different entity types.
    """
    
    @staticmethod
    def get_validator(entity_type: str) -> ValidationStrategy:
        """
        Get a validator for the specified entity type.
        
        Args:
            entity_type: Type of entity to validate
            
        Returns:
            ValidationStrategy: Appropriate validation strategy
            
        Raises:
            ValueError: If no validator exists for the entity type
        """
        validators = {
            "plan": PlanValidator(),
            "task": TaskValidator(),
            "dependency": DependencyValidator(),
        }
        
        if entity_type not in validators:
            raise ValueError(f"No validator available for entity type: {entity_type}")
        
        return validators[entity_type]
