"""
Strategic Planner component for the Planning System service.

This module implements the strategic planning component, which handles
high-level project planning and resource allocation.
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
    StrategicPlanCreate,
    StrategicPlanUpdate,
    StrategicPlanResponse,
    PaginatedResponse,
    PlanStatus
)
from ..exceptions import (
    PlanNotFoundError,
    PlanValidationError
)
from .repository import PlanningRepository
from .resource_optimizer import ResourceOptimizer

logger = logging.getLogger(__name__)

class StrategicPlanner:
    """
    Strategic planning component.
    
    This component handles high-level project planning and resource allocation,
    providing methods for creating, updating, and analyzing strategic plans.
    """
    
    def __init__(
        self,
        repository: PlanningRepository,
        event_bus: EventBus,
        resource_optimizer: ResourceOptimizer,
    ):
        """
        Initialize the strategic planner.
        
        Args:
            repository: Planning repository
            event_bus: Event bus
            resource_optimizer: Resource optimizer component
        """
        self.repository = repository
        self.event_bus = event_bus
        self.resource_optimizer = resource_optimizer
        logger.info("Strategic Planner initialized")
    
    async def create_plan(self, plan_data: StrategicPlanCreate) -> StrategicPlanResponse:
        """
        Create a new strategic plan.
        
        Args:
            plan_data: Plan data
            
        Returns:
            StrategicPlanResponse: Created plan
            
        Raises:
            PlanValidationError: If plan data is invalid
        """
        logger.info(f"Creating plan: {plan_data.name}")
        
        # Validate plan data
        await self._validate_plan_data(plan_data)
        
        # Convert to dict for repository
        plan_dict = plan_data.model_dump()
        
        # Create plan in repository
        plan = await self.repository.create_plan(plan_dict)
        
        # Publish event
        await self._publish_plan_created_event(plan)
        
        # Convert to response model
        return await self._to_response_model(plan)
    
    async def get_plan(self, plan_id: UUID) -> StrategicPlanResponse:
        """
        Get a strategic plan by ID.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            StrategicPlanResponse: Plan data
            
        Raises:
            PlanNotFoundError: If plan not found
        """
        logger.info(f"Getting plan: {plan_id}")
        
        # Get plan from repository
        plan = await self.repository.get_plan_by_id(plan_id)
        
        if not plan:
            raise PlanNotFoundError(str(plan_id))
        
        # Convert to response model
        return await self._to_response_model(plan)
    
    async def list_plans(
        self,
        project_id: Optional[UUID] = None,
        status: Optional[PlanStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """
        List strategic plans with filtering and pagination.
        
        Args:
            project_id: Optional project ID filter
            status: Optional status filter
            page: Page number
            page_size: Items per page
            
        Returns:
            PaginatedResponse: Paginated list of plans
        """
        logger.info(f"Listing plans (project_id={project_id}, status={status})")
        
        # Build filters
        filters = {}
        if project_id:
            filters["project_id"] = project_id
        if status:
            filters["status"] = status
        
        # Get plans from repository
        plans, total = await self.repository.list_plans(
            filters=filters,
            pagination={"page": page, "page_size": page_size}
        )
        
        # Load related data
        plans = await self.repository.load_plans_with_related(plans)
        
        # Convert to response models
        plan_responses = [await self._to_response_model(plan) for plan in plans]
        
        # Build paginated response
        return PaginatedResponse(
            items=plan_responses,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
    
    async def update_plan(
        self,
        plan_id: UUID,
        plan_data: StrategicPlanUpdate
    ) -> StrategicPlanResponse:
        """
        Update a strategic plan.
        
        Args:
            plan_id: Plan ID
            plan_data: Plan data to update
            
        Returns:
            StrategicPlanResponse: Updated plan
            
        Raises:
            PlanNotFoundError: If plan not found
            PlanValidationError: If update data is invalid
        """
        logger.info(f"Updating plan: {plan_id}")
        
        # Validate update data
        await self._validate_plan_update(plan_id, plan_data)
        
        # Convert to dict for repository
        update_dict = plan_data.model_dump(exclude_unset=True)
        
        # Update plan in repository
        plan = await self.repository.update_plan(plan_id, update_dict)
        
        if not plan:
            raise PlanNotFoundError(str(plan_id))
        
        # Publish event
        await self._publish_plan_updated_event(plan)
        
        # Convert to response model
        return await self._to_response_model(plan)
    
    async def delete_plan(self, plan_id: UUID) -> None:
        """
        Delete a strategic plan.
        
        Args:
            plan_id: Plan ID
            
        Raises:
            PlanNotFoundError: If plan not found
        """
        logger.info(f"Deleting plan: {plan_id}")
        
        # Get plan data for event
        plan = await self.repository.get_plan_by_id(plan_id)
        
        if not plan:
            raise PlanNotFoundError(str(plan_id))
        
        # Delete plan in repository
        success = await self.repository.delete_plan(plan_id)
        
        if not success:
            raise PlanNotFoundError(str(plan_id))
        
        # Publish event
        await self._publish_plan_deleted_event(plan)
    
    async def activate_plan(self, plan_id: UUID) -> StrategicPlanResponse:
        """
        Activate a strategic plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            StrategicPlanResponse: Activated plan
            
        Raises:
            PlanNotFoundError: If plan not found
            PlanValidationError: If plan cannot be activated
        """
        logger.info(f"Activating plan: {plan_id}")
        
        # Get plan
        plan = await self.repository.get_plan_by_id(plan_id)
        
        if not plan:
            raise PlanNotFoundError(str(plan_id))
        
        # Validate plan can be activated
        if plan.status == PlanStatus.ACTIVE:
            return await self._to_response_model(plan)
        
        if plan.status != PlanStatus.DRAFT:
            raise PlanValidationError(
                message=f"Plan cannot be activated from {plan.status} status",
                validation_errors=[f"Invalid status transition: {plan.status} -> {PlanStatus.ACTIVE}"]
            )
        
        # Update plan status
        plan = await self.repository.update_plan(
            plan_id=plan_id,
            plan_data={"status": PlanStatus.ACTIVE}
        )
        
        # Publish event
        await self._publish_plan_activated_event(plan)
        
        # Convert to response model
        return await self._to_response_model(plan)
    
    async def clone_plan(self, plan_id: UUID) -> StrategicPlanResponse:
        """
        Clone a strategic plan.
        
        Args:
            plan_id: Source plan ID
            
        Returns:
            StrategicPlanResponse: Cloned plan
            
        Raises:
            PlanNotFoundError: If plan not found
        """
        logger.info(f"Cloning plan: {plan_id}")
        
        # Get source plan
        source_plan = await self.repository.get_plan_by_id(plan_id)
        
        if not source_plan:
            raise PlanNotFoundError(str(plan_id))
        
        # Create new plan data
        new_plan_data = {
            "project_id": source_plan.project_id,
            "name": f"{source_plan.name} (Clone)",
            "description": source_plan.description,
            "constraints": source_plan.constraints,
            "objectives": source_plan.objectives,
            "status": PlanStatus.DRAFT,
        }
        
        # Create new plan
        new_plan = await self.repository.create_plan(new_plan_data)
        
        # Clone phases
        for phase in source_plan.phases:
            phase_data = {
                "plan_id": new_plan.id,
                "name": phase.name,
                "description": phase.description,
                "order": phase.order,
                "start_date": phase.start_date,
                "end_date": phase.end_date,
            }
            # Creating phases in repository is outside the scope of this example
            # This would be part of the implementation
        
        # Clone milestones
        for milestone in source_plan.milestones:
            milestone_data = {
                "plan_id": new_plan.id,
                "name": milestone.name,
                "description": milestone.description,
                "target_date": milestone.target_date,
                "actual_date": None,  # Reset actual date
                "priority": milestone.priority,
                "criteria": milestone.criteria,
            }
            # Creating milestones in repository is outside the scope of this example
            # This would be part of the implementation
        
        # Publish event
        await self._publish_plan_cloned_event(new_plan, source_plan)
        
        # Convert to response model
        return await self._to_response_model(new_plan)
    
    async def get_plan_history(self, plan_id: UUID, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get history of changes to a strategic plan.
        
        Args:
            plan_id: Plan ID
            limit: Maximum number of history entries
            
        Returns:
            List[Dict[str, Any]]: Plan history entries
            
        Raises:
            PlanNotFoundError: If plan not found
        """
        logger.info(f"Getting history for plan: {plan_id}")
        
        # Check plan exists
        plan = await self.repository.get_plan_by_id(plan_id)
        
        if not plan:
            raise PlanNotFoundError(str(plan_id))
        
        # Get history from repository
        history_entries = await self.repository.get_plan_history(plan_id, limit)
        
        # Convert to dict
        return [
            {
                "id": str(entry.id),
                "timestamp": entry.timestamp.isoformat(),
                "change_type": entry.change_type,
                "change_reason": entry.change_reason,
                "previous_state": entry.previous_state,
                "new_state": entry.new_state,
            }
            for entry in history_entries
        ]
    
    # Helper methods
    
    async def _validate_plan_data(self, plan_data: StrategicPlanCreate) -> None:
        """
        Validate plan data for creation.
        
        Args:
            plan_data: Plan data
            
        Raises:
            PlanValidationError: If plan data is invalid
        """
        validation_errors = []
        
        # Perform validation checks
        # These are just examples - real validation would likely check more
        
        # Validate objectives has required fields
        objectives = plan_data.objectives
        if not objectives.get("goal"):
            validation_errors.append("Objectives must have a goal")
        
        if not objectives.get("success_criteria"):
            validation_errors.append("Objectives must have success criteria")
        
        # Raise error if any validation errors
        if validation_errors:
            raise PlanValidationError(
                message="Invalid plan data",
                validation_errors=validation_errors
            )
    
    async def _validate_plan_update(self, plan_id: UUID, plan_data: StrategicPlanUpdate) -> None:
        """
        Validate plan data for update.
        
        Args:
            plan_id: Plan ID
            plan_data: Plan data
            
        Raises:
            PlanValidationError: If plan data is invalid
        """
        validation_errors = []
        
        # Get existing plan
        plan = await self.repository.get_plan_by_id(plan_id)
        
        if not plan:
            raise PlanNotFoundError(str(plan_id))
        
        # Validate status transition
        if plan_data.status is not None:
            valid_transitions = {
                PlanStatus.DRAFT: [PlanStatus.ACTIVE, PlanStatus.ARCHIVED, PlanStatus.CANCELLED],
                PlanStatus.ACTIVE: [PlanStatus.COMPLETED, PlanStatus.ARCHIVED, PlanStatus.CANCELLED],
                PlanStatus.COMPLETED: [PlanStatus.ARCHIVED],
                PlanStatus.ARCHIVED: [],
                PlanStatus.CANCELLED: [PlanStatus.ARCHIVED],
            }
            
            if plan_data.status not in valid_transitions.get(plan.status, []) and plan_data.status != plan.status:
                validation_errors.append(f"Invalid status transition: {plan.status} -> {plan_data.status}")
        
        # Validate objectives if present
        if plan_data.objectives is not None:
            objectives = plan_data.objectives
            if not objectives.get("goal"):
                validation_errors.append("Objectives must have a goal")
            
            if not objectives.get("success_criteria"):
                validation_errors.append("Objectives must have success criteria")
        
        # Raise error if any validation errors
        if validation_errors:
            raise PlanValidationError(
                message="Invalid plan update",
                validation_errors=validation_errors
            )
    
    async def _to_response_model(self, plan) -> StrategicPlanResponse:
        """
        Convert a plan model to a response model.
        
        Args:
            plan: Strategic plan model
            
        Returns:
            StrategicPlanResponse: Plan response model
        """
        # Count related entities
        phase_count = len(plan.phases)
        milestone_count = len(plan.milestones)
        
        # Get task count (would be implemented in repository)
        task_count = len(plan.tasks) if hasattr(plan, "tasks") and plan.tasks is not None else 0
        
        # Calculate progress (simplified in this example)
        progress = 0.0
        if task_count > 0 and hasattr(plan, "tasks") and plan.tasks is not None:
            completed_tasks = sum(1 for task in plan.tasks if task.status == TaskStatus.COMPLETED)
            progress = (completed_tasks / task_count) * 100
        
        # Convert to response model
        return StrategicPlanResponse(
            id=plan.id,
            project_id=plan.project_id,
            name=plan.name,
            description=plan.description,
            constraints=plan.constraints,
            objectives=plan.objectives,
            status=plan.status,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
            phase_count=phase_count,
            milestone_count=milestone_count,
            task_count=task_count,
            progress=progress,
        )
    
    # Event methods
    
    async def _publish_plan_created_event(self, plan) -> None:
        """
        Publish plan created event.
        
        Args:
            plan: Created plan
        """
        event_data = {
            "plan_id": str(plan.id),
            "project_id": str(plan.project_id),
            "name": plan.name,
            "status": plan.status.value,
            "created_at": plan.created_at.isoformat(),
        }
        
        await self.event_bus.publish("plan.created", event_data)
    
    async def _publish_plan_updated_event(self, plan) -> None:
        """
        Publish plan updated event.
        
        Args:
            plan: Updated plan
        """
        event_data = {
            "plan_id": str(plan.id),
            "project_id": str(plan.project_id),
            "name": plan.name,
            "status": plan.status.value,
            "updated_at": plan.updated_at.isoformat(),
        }
        
        await self.event_bus.publish("plan.updated", event_data)
    
    async def _publish_plan_deleted_event(self, plan) -> None:
        """
        Publish plan deleted event.
        
        Args:
            plan: Deleted plan
        """
        event_data = {
            "plan_id": str(plan.id),
            "project_id": str(plan.project_id),
            "name": plan.name,
        }
        
        await self.event_bus.publish("plan.deleted", event_data)
    
    async def _publish_plan_activated_event(self, plan) -> None:
        """
        Publish plan activated event.
        
        Args:
            plan: Activated plan
        """
        event_data = {
            "plan_id": str(plan.id),
            "project_id": str(plan.project_id),
            "name": plan.name,
            "activated_at": datetime.utcnow().isoformat(),
        }
        
        await self.event_bus.publish("plan.activated", event_data)
    
    async def _publish_plan_cloned_event(self, new_plan, source_plan) -> None:
        """
        Publish plan cloned event.
        
        Args:
            new_plan: Cloned plan
            source_plan: Source plan
        """
        event_data = {
            "plan_id": str(new_plan.id),
            "project_id": str(new_plan.project_id),
            "name": new_plan.name,
            "source_plan_id": str(source_plan.id),
            "source_plan_name": source_plan.name,
            "created_at": new_plan.created_at.isoformat(),
        }
        
        await self.event_bus.publish("plan.cloned", event_data)
