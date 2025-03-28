"""
Tactical Planner component for the Planning System service.

This module implements the tactical planning component, which handles
task-level planning and execution tracking.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple, Union
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from shared.utils.src.messaging import EventBus
from ..config import PlanningSystemConfig as Settings

from ..models.api import (
    PlanningTaskCreate,
    PlanningTaskUpdate,
    PlanningTaskResponse,
    PaginatedResponse,
    TaskStatus,
    PlanStatus
)
from ..exceptions import (
    TaskNotFoundError,
    PlanNotFoundError,
    TaskValidationError
)
from .repository import PlanningRepository
from .dependency_manager import DependencyManager

logger = logging.getLogger(__name__)

class TacticalPlanner:
    """
    Tactical planning component.
    
    This component handles task-level planning and execution tracking,
    providing methods for creating, updating, and analyzing planning tasks.
    """
    
    def __init__(
        self,
        repository: PlanningRepository,
        event_bus: EventBus,
        dependency_manager: DependencyManager,
    ):
        """
        Initialize the tactical planner.
        
        Args:
            repository: Planning repository
            event_bus: Event bus
            dependency_manager: Dependency manager component
        """
        self.repository = repository
        self.event_bus = event_bus
        self.dependency_manager = dependency_manager
        logger.info("Tactical Planner initialized")
    
    async def create_task(self, task_data: PlanningTaskCreate) -> PlanningTaskResponse:
        """
        Create a new planning task.
        
        Args:
            task_data: Task data
            
        Returns:
            PlanningTaskResponse: Created task
            
        Raises:
            PlanNotFoundError: If plan not found
            TaskValidationError: If task data is invalid
        """
        logger.info(f"Creating task: {task_data.name} for plan {task_data.plan_id}")
        
        # Validate plan exists
        plan = await self.repository.get_plan_by_id(task_data.plan_id)
        if not plan:
            raise PlanNotFoundError(str(task_data.plan_id))
        
        # Validate plan status
        if plan.status not in [PlanStatus.DRAFT, PlanStatus.ACTIVE]:
            raise TaskValidationError(
                message=f"Cannot add tasks to plan with status {plan.status}",
                validation_errors=[f"Invalid plan status: {plan.status}"]
            )
        
        # Validate phase exists if provided
        if task_data.phase_id:
            phase = await self.repository.get_phase_by_id(task_data.phase_id)
            if not phase or phase.plan_id != task_data.plan_id:
                raise TaskValidationError(
                    message=f"Invalid phase ID: {task_data.phase_id}",
                    validation_errors=["Phase does not exist or does not belong to the specified plan"]
                )
        
        # Validate milestone exists if provided
        if task_data.milestone_id:
            milestone = await self.repository.get_milestone_by_id(task_data.milestone_id)
            if not milestone or milestone.plan_id != task_data.plan_id:
                raise TaskValidationError(
                    message=f"Invalid milestone ID: {task_data.milestone_id}",
                    validation_errors=["Milestone does not exist or does not belong to the specified plan"]
                )
        
        # Additional validation
        await self._validate_task_data(task_data)
        
        # Convert to dict for repository
        task_dict = task_data.model_dump()
        
        # Create task in repository
        task = await self.repository.create_task(task_dict)
        
        # Publish event
        await self._publish_task_created_event(task)
        
        # Convert to response model
        return await self._to_response_model(task)
    
    async def get_task(self, task_id: UUID) -> PlanningTaskResponse:
        """
        Get a planning task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            PlanningTaskResponse: Task data
            
        Raises:
            TaskNotFoundError: If task not found
        """
        logger.info(f"Getting task: {task_id}")
        
        # Get task from repository
        task = await self.repository.get_task_by_id(task_id)
        
        if not task:
            raise TaskNotFoundError(str(task_id))
        
        # Convert to response model
        return await self._to_response_model(task)
    
    async def list_tasks(
        self,
        plan_id: UUID,
        phase_id: Optional[UUID] = None,
        milestone_id: Optional[UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """
        List planning tasks with filtering and pagination.
        
        Args:
            plan_id: Plan ID
            phase_id: Optional phase ID filter
            milestone_id: Optional milestone ID filter
            status: Optional status filter
            page: Page number
            page_size: Items per page
            
        Returns:
            PaginatedResponse: Paginated list of tasks
            
        Raises:
            PlanNotFoundError: If plan not found
        """
        logger.info(f"Listing tasks for plan {plan_id}")
        
        # Validate plan exists
        plan = await self.repository.get_plan_by_id(plan_id)
        if not plan:
            raise PlanNotFoundError(str(plan_id))
        
        # Build filters
        filters = {"plan_id": plan_id}
        if phase_id:
            filters["phase_id"] = phase_id
        if milestone_id:
            filters["milestone_id"] = milestone_id
        if status:
            filters["status"] = status
        
        # Get tasks from repository
        tasks, total = await self.repository.list_tasks(
            filters=filters,
            pagination={"page": page, "page_size": page_size}
        )
        
        # Load related data
        tasks = await self.repository.load_tasks_with_related(tasks)
        
        # Convert to response models
        task_responses = [await self._to_response_model(task) for task in tasks]
        
        # Build paginated response
        return PaginatedResponse(
            items=task_responses,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
    
    async def update_task(
        self,
        task_id: UUID,
        task_data: PlanningTaskUpdate
    ) -> PlanningTaskResponse:
        """
        Update a planning task.
        
        Args:
            task_id: Task ID
            task_data: Task data to update
            
        Returns:
            PlanningTaskResponse: Updated task
            
        Raises:
            TaskNotFoundError: If task not found
            TaskValidationError: If update data is invalid
        """
        logger.info(f"Updating task: {task_id}")
        
        # Get existing task
        task = await self.repository.get_task_by_id(task_id)
        if not task:
            raise TaskNotFoundError(str(task_id))
        
        # Get plan to validate status
        plan = await self.repository.get_plan_by_id(task.plan_id)
        if not plan:
            # This should not happen, but adding a check for robustness
            logger.error(f"Task {task_id} references non-existent plan {task.plan_id}")
            raise PlanNotFoundError(str(task.plan_id))
        
        # Validate plan status
        if plan.status not in [PlanStatus.DRAFT, PlanStatus.ACTIVE]:
            raise TaskValidationError(
                message=f"Cannot update tasks in plan with status {plan.status}",
                validation_errors=[f"Invalid plan status: {plan.status}"]
            )
        
        # Validate update data
        await self._validate_task_update(task_id, task_data)
        
        # Convert to dict for repository
        update_dict = task_data.model_dump(exclude_unset=True)
        
        # Update task in repository
        task = await self.repository.update_task(task_id, update_dict)
        
        if not task:
            raise TaskNotFoundError(str(task_id))
        
        # Publish event
        await self._publish_task_updated_event(task)
        
        # Recalculate dependencies if status changed
        if task_data.status is not None and task_data.status != task.status:
            await self.dependency_manager.update_dependent_tasks(task_id)
        
        # Convert to response model
        return await self._to_response_model(task)
    
    async def delete_task(self, task_id: UUID) -> None:
        """
        Delete a planning task.
        
        Args:
            task_id: Task ID
            
        Raises:
            TaskNotFoundError: If task not found
        """
        logger.info(f"Deleting task: {task_id}")
        
        # Get task data for event
        task = await self.repository.get_task_by_id(task_id)
        
        if not task:
            raise TaskNotFoundError(str(task_id))
        
        # Get plan to validate status
        plan = await self.repository.get_plan_by_id(task.plan_id)
        if not plan:
            # This should not happen, but adding a check for robustness
            logger.error(f"Task {task_id} references non-existent plan {task.plan_id}")
            raise PlanNotFoundError(str(task.plan_id))
        
        # Validate plan status
        if plan.status not in [PlanStatus.DRAFT, PlanStatus.ACTIVE]:
            raise TaskValidationError(
                message=f"Cannot delete tasks from plan with status {plan.status}",
                validation_errors=[f"Invalid plan status: {plan.status}"]
            )
        
        # Check if task has dependencies or dependents
        has_dependencies = await self.repository.check_task_has_dependencies(task_id)
        if has_dependencies:
            raise TaskValidationError(
                message="Cannot delete task with dependencies",
                validation_errors=["Task has dependencies or is depended upon by other tasks"]
            )
        
        # Delete task in repository
        success = await self.repository.delete_task(task_id)
        
        if not success:
            raise TaskNotFoundError(str(task_id))
        
        # Publish event
        await self._publish_task_deleted_event(task)
    
    async def get_task_by_name(self, plan_id: UUID, name: str) -> Optional[PlanningTaskResponse]:
        """
        Get a task by name within a plan.
        
        Args:
            plan_id: Plan ID
            name: Task name
            
        Returns:
            Optional[PlanningTaskResponse]: Task if found, None otherwise
        """
        logger.info(f"Getting task by name: {name} in plan {plan_id}")
        
        # Get task from repository
        task = await self.repository.get_task_by_name(plan_id, name)
        
        if not task:
            return None
        
        # Convert to response model
        return await self._to_response_model(task)
    
    async def bulk_update_tasks(
        self,
        task_ids: List[UUID],
        update_data: Dict[str, Any]
    ) -> List[PlanningTaskResponse]:
        """
        Update multiple tasks with the same data.
        
        Args:
            task_ids: List of task IDs
            update_data: Update data to apply to all tasks
            
        Returns:
            List[PlanningTaskResponse]: Updated tasks
            
        Raises:
            TaskValidationError: If any update is invalid
        """
        logger.info(f"Bulk updating {len(task_ids)} tasks")
        
        # Validate tasks exist
        tasks = []
        for task_id in task_ids:
            task = await self.repository.get_task_by_id(task_id)
            if not task:
                raise TaskNotFoundError(str(task_id))
            tasks.append(task)
        
        # Create a task update object to validate the data
        task_update = PlanningTaskUpdate(**update_data)
        
        # Update each task
        updated_tasks = []
        for task in tasks:
            # Validate update for this specific task
            await self._validate_task_update(task.id, task_update)
            
            # Update task in repository
            updated_task = await self.repository.update_task(
                task_id=task.id,
                task_data=update_data
            )
            
            # Publish event
            await self._publish_task_updated_event(updated_task)
            
            # Recalculate dependencies if status changed
            if "status" in update_data and update_data["status"] != task.status:
                await self.dependency_manager.update_dependent_tasks(task.id)
            
            # Convert to response model
            response = await self._to_response_model(updated_task)
            updated_tasks.append(response)
        
        return updated_tasks
    
    # Helper methods
    
    async def _validate_task_data(self, task_data: PlanningTaskCreate) -> None:
        """
        Validate task data for creation.
        
        Args:
            task_data: Task data
            
        Raises:
            TaskValidationError: If task data is invalid
        """
        validation_errors = []
        
        # Check for required skills if they require a minimum proficiency
        if task_data.required_skills:
            for skill, proficiency in task_data.required_skills.items():
                if not isinstance(proficiency, (int, float)) or proficiency < 0 or proficiency > 1:
                    validation_errors.append(f"Skill proficiency for {skill} must be between 0 and 1")
        
        # Validate estimated duration and effort consistency
        if task_data.estimated_duration > 0 and task_data.estimated_effort > 0:
            if task_data.estimated_effort < task_data.estimated_duration:
                validation_errors.append("Estimated effort cannot be less than estimated duration")
        
        # Raise error if any validation errors
        if validation_errors:
            raise TaskValidationError(
                message="Invalid task data",
                validation_errors=validation_errors
            )
    
    async def _validate_task_update(self, task_id: UUID, task_data: PlanningTaskUpdate) -> None:
        """
        Validate task data for update.
        
        Args:
            task_id: Task ID
            task_data: Task data
            
        Raises:
            TaskValidationError: If task data is invalid
        """
        validation_errors = []
        
        # Get existing task
        task = await self.repository.get_task_by_id(task_id)
        
        if not task:
            raise TaskNotFoundError(str(task_id))
        
        # Validate status transition
        if task_data.status is not None:
            valid_transitions = {
                TaskStatus.PLANNED: [TaskStatus.READY, TaskStatus.CANCELLED],
                TaskStatus.READY: [TaskStatus.IN_PROGRESS, TaskStatus.PLANNED, TaskStatus.CANCELLED],
                TaskStatus.IN_PROGRESS: [TaskStatus.COMPLETED, TaskStatus.BLOCKED, TaskStatus.CANCELLED],
                TaskStatus.BLOCKED: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
                TaskStatus.COMPLETED: [TaskStatus.IN_PROGRESS],  # Allow reverting if needed
                TaskStatus.CANCELLED: [TaskStatus.PLANNED],  # Allow re-opening
            }
            
            if task_data.status not in valid_transitions.get(task.status, []) and task_data.status != task.status:
                validation_errors.append(f"Invalid status transition: {task.status} -> {task_data.status}")
        
        # Validate phase change
        if task_data.phase_id is not None and task_data.phase_id != task.phase_id:
            if task_data.phase_id:
                phase = await self.repository.get_phase_by_id(task_data.phase_id)
                if not phase or phase.plan_id != task.plan_id:
                    validation_errors.append(f"Invalid phase ID: {task_data.phase_id}")
        
        # Validate milestone change
        if task_data.milestone_id is not None and task_data.milestone_id != task.milestone_id:
            if task_data.milestone_id:
                milestone = await self.repository.get_milestone_by_id(task_data.milestone_id)
                if not milestone or milestone.plan_id != task.plan_id:
                    validation_errors.append(f"Invalid milestone ID: {task_data.milestone_id}")
        
        # Check for required skills if they require a minimum proficiency
        if task_data.required_skills is not None:
            for skill, proficiency in task_data.required_skills.items():
                if not isinstance(proficiency, (int, float)) or proficiency < 0 or proficiency > 1:
                    validation_errors.append(f"Skill proficiency for {skill} must be between 0 and 1")
        
        # Validate estimated duration and effort consistency
        if task_data.estimated_duration is not None and task_data.estimated_effort is not None:
            if task_data.estimated_effort < task_data.estimated_duration:
                validation_errors.append("Estimated effort cannot be less than estimated duration")
        elif task_data.estimated_duration is not None and task.estimated_effort is not None:
            if task.estimated_effort < task_data.estimated_duration:
                validation_errors.append("Estimated effort cannot be less than estimated duration")
        elif task_data.estimated_effort is not None and task.estimated_duration is not None:
            if task_data.estimated_effort < task.estimated_duration:
                validation_errors.append("Estimated effort cannot be less than estimated duration")
        
        # Raise error if any validation errors
        if validation_errors:
            raise TaskValidationError(
                message="Invalid task update",
                validation_errors=validation_errors
            )
    
    async def _to_response_model(self, task) -> PlanningTaskResponse:
        """
        Convert a task model to a response model.
        
        Args:
            task: Planning task model
            
        Returns:
            PlanningTaskResponse: Task response model
        """
        # Get dependency counts
        dependency_count = await self.repository.count_task_dependencies(task.id, "outgoing")
        dependent_count = await self.repository.count_task_dependencies(task.id, "incoming")
        
        # Check if task is on critical path
        is_critical_path = await self.dependency_manager.is_task_on_critical_path(task.id)
        
        # Get earliest/latest start/finish times from schedule data
        # This would normally come from a scheduling algorithm
        schedule_data = await self.repository.get_task_schedule_data(task.id)
        
        # Convert to response model
        return PlanningTaskResponse(
            id=task.id,
            plan_id=task.plan_id,
            phase_id=task.phase_id,
            milestone_id=task.milestone_id,
            name=task.name,
            description=task.description,
            estimated_duration=task.estimated_duration,
            estimated_effort=task.estimated_effort,
            required_skills=task.required_skills,
            constraints=task.constraints,
            priority=task.priority,
            status=task.status,
            created_at=task.created_at,
            updated_at=task.updated_at,
            dependency_count=dependency_count,
            dependent_count=dependent_count,
            is_critical_path=is_critical_path,
            earliest_start=schedule_data.get("earliest_start") if schedule_data else None,
            earliest_finish=schedule_data.get("earliest_finish") if schedule_data else None,
            latest_start=schedule_data.get("latest_start") if schedule_data else None,
            latest_finish=schedule_data.get("latest_finish") if schedule_data else None,
            slack=schedule_data.get("slack") if schedule_data else None,
        )
    
    # Event methods
    
    async def _publish_task_created_event(self, task) -> None:
        """
        Publish task created event.
        
        Args:
            task: Created task
        """
        event_data = {
            "task_id": str(task.id),
            "plan_id": str(task.plan_id),
            "name": task.name,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
        }
        
        await self.event_bus.publish("task.created", event_data)
    
    async def _publish_task_updated_event(self, task) -> None:
        """
        Publish task updated event.
        
        Args:
            task: Updated task
        """
        event_data = {
            "task_id": str(task.id),
            "plan_id": str(task.plan_id),
            "name": task.name,
            "status": task.status.value,
            "updated_at": task.updated_at.isoformat(),
        }
        
        await self.event_bus.publish("task.updated", event_data)
    
    async def _publish_task_deleted_event(self, task) -> None:
        """
        Publish task deleted event.
        
        Args:
            task: Deleted task
        """
        event_data = {
            "task_id": str(task.id),
            "plan_id": str(task.plan_id),
            "name": task.name,
        }
        
        await self.event_bus.publish("task.deleted", event_data)
