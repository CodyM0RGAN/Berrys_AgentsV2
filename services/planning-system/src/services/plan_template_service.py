"""
Plan Template Service for the Planning System.

This module implements the plan template service, which handles
template management for strategic plans.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from shared.utils.src.messaging import EventBus

from ..config import PlanningSystemConfig as Settings
from ..models.api import (
    PlanTemplateCreate,
    PlanTemplateUpdate,
    PlanTemplateResponse,
    TemplatePhaseCreate,
    TemplatePhaseUpdate,
    TemplatePhaseResponse,
    TemplateMilestoneCreate,
    TemplateMilestoneUpdate,
    TemplateMilestoneResponse,
    TemplateTaskCreate,
    TemplateTaskUpdate,
    TemplateTaskResponse,
    PaginatedResponse
)
from ..exceptions import (
    TemplateNotFoundError,
    TemplateValidationError,
    TemplatePhaseNotFoundError,
    TemplateMilestoneNotFoundError,
    TemplateTaskNotFoundError
)
from .repository import PlanningRepository

logger = logging.getLogger(__name__)

class PlanTemplateService:
    """
    Plan template service.
    
    This service handles template management for strategic plans,
    providing methods for creating, updating, and managing plan templates.
    """
    
    def __init__(
        self,
        repository: PlanningRepository,
        event_bus: EventBus,
    ):
        """
        Initialize the plan template service.
        
        Args:
            repository: Planning repository
            event_bus: Event bus
        """
        self.repository = repository
        self.event_bus = event_bus
        logger.info("Plan Template Service initialized")
    
    async def create_template(self, template_data: PlanTemplateCreate) -> PlanTemplateResponse:
        """
        Create a new plan template.
        
        Args:
            template_data: Template data
            
        Returns:
            PlanTemplateResponse: Created template
            
        Raises:
            TemplateValidationError: If template data is invalid
        """
        logger.info(f"Creating template: {template_data.name}")
        
        # Validate template data
        await self._validate_template_data(template_data)
        
        # Convert to dict for repository
        template_dict = template_data.model_dump()
        
        # Create template in repository
        template = await self.repository.create_template(template_dict)
        
        # Publish event
        await self._publish_template_created_event(template)
        
        # Convert to response model
        return await self._to_template_response_model(template)
    
    async def get_template(self, template_id: UUID) -> PlanTemplateResponse:
        """
        Get a plan template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            PlanTemplateResponse: Template data
            
        Raises:
            TemplateNotFoundError: If template not found
        """
        logger.info(f"Getting template: {template_id}")
        
        # Get template from repository
        template = await self.repository.get_template_by_id(template_id)
        
        if not template:
            raise TemplateNotFoundError(str(template_id))
        
        # Convert to response model
        return await self._to_template_response_model(template)
    
    async def list_templates(
        self,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """
        List plan templates with filtering and pagination.
        
        Args:
            is_active: Optional active status filter
            page: Page number
            page_size: Items per page
            
        Returns:
            PaginatedResponse: Paginated list of templates
        """
        logger.info(f"Listing templates (is_active={is_active})")
        
        # Build filters
        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active
        
        # Get templates from repository
        templates, total = await self.repository.list_templates(
            filters=filters,
            pagination={"page": page, "page_size": page_size}
        )
        
        # Load related data
        templates = await self.repository.load_templates_with_related(templates)
        
        # Convert to response models
        template_responses = [await self._to_template_response_model(template) for template in templates]
        
        # Build paginated response
        return PaginatedResponse(
            items=template_responses,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
    
    async def update_template(
        self,
        template_id: UUID,
        template_data: PlanTemplateUpdate
    ) -> PlanTemplateResponse:
        """
        Update a plan template.
        
        Args:
            template_id: Template ID
            template_data: Template data to update
            
        Returns:
            PlanTemplateResponse: Updated template
            
        Raises:
            TemplateNotFoundError: If template not found
            TemplateValidationError: If update data is invalid
        """
        logger.info(f"Updating template: {template_id}")
        
        # Validate update data
        await self._validate_template_update(template_id, template_data)
        
        # Convert to dict for repository
        update_dict = template_data.model_dump(exclude_unset=True)
        
        # Update template in repository
        template = await self.repository.update_template(template_id, update_dict)
        
        if not template:
            raise TemplateNotFoundError(str(template_id))
        
        # Publish event
        await self._publish_template_updated_event(template)
        
        # Convert to response model
        return await self._to_template_response_model(template)
    
    async def delete_template(self, template_id: UUID) -> None:
        """
        Delete a plan template.
        
        Args:
            template_id: Template ID
            
        Raises:
            TemplateNotFoundError: If template not found
            TemplateValidationError: If template is in use
        """
        logger.info(f"Deleting template: {template_id}")
        
        # Get template data for event
        template = await self.repository.get_template_by_id(template_id)
        
        if not template:
            raise TemplateNotFoundError(str(template_id))
        
        # Check if template is in use
        plans_using_template = await self.repository.count_plans_using_template(template_id)
        if plans_using_template > 0:
            raise TemplateValidationError(
                message=f"Cannot delete template that is in use by {plans_using_template} plans",
                validation_errors=["Template is in use by existing plans"]
            )
        
        # Delete template in repository
        success = await self.repository.delete_template(template_id)
        
        if not success:
            raise TemplateNotFoundError(str(template_id))
        
        # Publish event
        await self._publish_template_deleted_event(template)
    
    async def clone_template(self, template_id: UUID, new_name: str, new_version: str) -> PlanTemplateResponse:
        """
        Clone a plan template.
        
        Args:
            template_id: Source template ID
            new_name: Name for the cloned template
            new_version: Version for the cloned template
            
        Returns:
            PlanTemplateResponse: Cloned template
            
        Raises:
            TemplateNotFoundError: If template not found
        """
        logger.info(f"Cloning template: {template_id}")
        
        # Get source template
        source_template = await self.repository.get_template_by_id(template_id)
        
        if not source_template:
            raise TemplateNotFoundError(str(template_id))
        
        # Create new template data
        new_template_data = {
            "name": new_name,
            "description": source_template.description,
            "version": new_version,
            "structure": source_template.structure,
            "customization_options": source_template.customization_options,
            "metadata": source_template.metadata,
            "is_active": True,
        }
        
        # Create new template
        new_template = await self.repository.create_template(new_template_data)
        
        # Clone phases
        for phase in source_template.phases:
            phase_data = {
                "template_id": new_template.id,
                "name": phase.name,
                "description": phase.description,
                "order": phase.order,
                "duration_estimate": phase.duration_estimate,
                "objectives": phase.objectives,
                "deliverables": phase.deliverables,
                "completion_criteria": phase.completion_criteria,
            }
            await self.repository.create_template_phase(phase_data)
        
        # Clone milestones
        for milestone in source_template.milestones:
            milestone_data = {
                "template_id": new_template.id,
                "name": milestone.name,
                "description": milestone.description,
                "relative_day": milestone.relative_day,
                "priority": milestone.priority,
                "criteria": milestone.criteria,
            }
            await self.repository.create_template_milestone(milestone_data)
        
        # Clone tasks
        for task in source_template.tasks:
            task_data = {
                "template_id": new_template.id,
                "phase_id": None,  # Will be updated after phases are created
                "milestone_id": None,  # Will be updated after milestones are created
                "name": task.name,
                "description": task.description,
                "estimated_duration": task.estimated_duration,
                "estimated_effort": task.estimated_effort,
                "required_skills": task.required_skills,
                "priority": task.priority,
                "acceptance_criteria_template": task.acceptance_criteria_template,
            }
            await self.repository.create_template_task(task_data)
        
        # Publish event
        await self._publish_template_cloned_event(new_template, source_template)
        
        # Convert to response model
        return await self._to_template_response_model(new_template)
    
    # Template Phase methods
    
    async def create_template_phase(self, phase_data: TemplatePhaseCreate) -> TemplatePhaseResponse:
        """
        Create a new template phase.
        
        Args:
            phase_data: Phase data
            
        Returns:
            TemplatePhaseResponse: Created phase
            
        Raises:
            TemplateNotFoundError: If template not found
            TemplateValidationError: If phase data is invalid
        """
        logger.info(f"Creating template phase: {phase_data.name}")
        
        # Validate template exists
        template = await self.repository.get_template_by_id(phase_data.template_id)
        if not template:
            raise TemplateNotFoundError(str(phase_data.template_id))
        
        # Validate phase data
        await self._validate_template_phase_data(phase_data)
        
        # Convert to dict for repository
        phase_dict = phase_data.model_dump()
        
        # Create phase in repository
        phase = await self.repository.create_template_phase(phase_dict)
        
        # Publish event
        await self._publish_template_phase_created_event(phase)
        
        # Convert to response model
        return await self._to_template_phase_response_model(phase)
    
    async def get_template_phase(self, phase_id: UUID) -> TemplatePhaseResponse:
        """
        Get a template phase by ID.
        
        Args:
            phase_id: Phase ID
            
        Returns:
            TemplatePhaseResponse: Phase data
            
        Raises:
            TemplatePhaseNotFoundError: If phase not found
        """
        logger.info(f"Getting template phase: {phase_id}")
        
        # Get phase from repository
        phase = await self.repository.get_template_phase_by_id(phase_id)
        
        if not phase:
            raise TemplatePhaseNotFoundError(str(phase_id))
        
        # Convert to response model
        return await self._to_template_phase_response_model(phase)
    
    async def list_template_phases(
        self,
        template_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """
        List template phases with pagination.
        
        Args:
            template_id: Template ID
            page: Page number
            page_size: Items per page
            
        Returns:
            PaginatedResponse: Paginated list of phases
            
        Raises:
            TemplateNotFoundError: If template not found
        """
        logger.info(f"Listing phases for template {template_id}")
        
        # Validate template exists
        template = await self.repository.get_template_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(str(template_id))
        
        # Get phases from repository
        phases, total = await self.repository.list_template_phases(
            template_id=template_id,
            pagination={"page": page, "page_size": page_size}
        )
        
        # Convert to response models
        phase_responses = [await self._to_template_phase_response_model(phase) for phase in phases]
        
        # Build paginated response
        return PaginatedResponse(
            items=phase_responses,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
    
    # Helper methods
    
    async def _validate_template_data(self, template_data: PlanTemplateCreate) -> None:
        """
        Validate template data for creation.
        
        Args:
            template_data: Template data
            
        Raises:
            TemplateValidationError: If template data is invalid
        """
        validation_errors = []
        
        # Validate structure has required fields
        structure = template_data.structure
        if not structure.get("phases"):
            validation_errors.append("Template structure must have phases")
        
        # Raise error if any validation errors
        if validation_errors:
            raise TemplateValidationError(
                message="Invalid template data",
                validation_errors=validation_errors
            )
    
    async def _validate_template_update(self, template_id: UUID, template_data: PlanTemplateUpdate) -> None:
        """
        Validate template data for update.
        
        Args:
            template_id: Template ID
            template_data: Template data
            
        Raises:
            TemplateValidationError: If template data is invalid
        """
        validation_errors = []
        
        # Get existing template
        template = await self.repository.get_template_by_id(template_id)
        
        if not template:
            raise TemplateNotFoundError(str(template_id))
        
        # Validate structure has required fields if provided
        if template_data.structure is not None:
            structure = template_data.structure
            if not structure.get("phases"):
                validation_errors.append("Template structure must have phases")
        
        # Raise error if any validation errors
        if validation_errors:
            raise TemplateValidationError(
                message="Invalid template update",
                validation_errors=validation_errors
            )
    
    async def _validate_template_phase_data(self, phase_data: TemplatePhaseCreate) -> None:
        """
        Validate template phase data for creation.
        
        Args:
            phase_data: Phase data
            
        Raises:
            TemplateValidationError: If phase data is invalid
        """
        validation_errors = []
        
        # Perform validation checks
        # These are just examples - real validation would likely check more
        
        # Raise error if any validation errors
        if validation_errors:
            raise TemplateValidationError(
                message="Invalid template phase data",
                validation_errors=validation_errors
            )
    
    async def _to_template_response_model(self, template) -> PlanTemplateResponse:
        """
        Convert a template model to a response model.
        
        Args:
            template: Plan template model
            
        Returns:
            PlanTemplateResponse: Template response model
        """
        # Count related entities
        phase_count = len(template.phases) if hasattr(template, "phases") and template.phases is not None else 0
        milestone_count = len(template.milestones) if hasattr(template, "milestones") and template.milestones is not None else 0
        task_count = len(template.tasks) if hasattr(template, "tasks") and template.tasks is not None else 0
        
        # Count plans using this template
        plan_count = await self.repository.count_plans_using_template(template.id)
        
        # Convert to response model
        return PlanTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            version=template.version,
            structure=template.structure,
            customization_options=template.customization_options,
            metadata=template.metadata,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at,
            phase_count=phase_count,
            milestone_count=milestone_count,
            task_count=task_count,
            plan_count=plan_count,
        )
    
    async def _to_template_phase_response_model(self, phase) -> TemplatePhaseResponse:
        """
        Convert a template phase model to a response model.
        
        Args:
            phase: Template phase model
            
        Returns:
            TemplatePhaseResponse: Phase response model
        """
        # Count tasks in this phase
        task_count = await self.repository.count_template_tasks_in_phase(phase.id)
        
        # Convert to response model
        return TemplatePhaseResponse(
            id=phase.id,
            template_id=phase.template_id,
            name=phase.name,
            description=phase.description,
            order=phase.order,
            duration_estimate=phase.duration_estimate,
            objectives=phase.objectives,
            deliverables=phase.deliverables,
            completion_criteria=phase.completion_criteria,
            created_at=phase.created_at,
            updated_at=phase.updated_at,
            task_count=task_count,
        )
    
    # Event methods
    
    async def _publish_template_created_event(self, template) -> None:
        """
        Publish template created event.
        
        Args:
            template: Created template
        """
        event_data = {
            "template_id": str(template.id),
            "name": template.name,
            "version": template.version,
            "created_at": template.created_at.isoformat(),
        }
        
        await self.event_bus.publish("template.created", event_data)
    
    async def _publish_template_updated_event(self, template) -> None:
        """
        Publish template updated event.
        
        Args:
            template: Updated template
        """
        event_data = {
            "template_id": str(template.id),
            "name": template.name,
            "version": template.version,
            "updated_at": template.updated_at.isoformat(),
        }
        
        await self.event_bus.publish("template.updated", event_data)
    
    async def _publish_template_deleted_event(self, template) -> None:
        """
        Publish template deleted event.
        
        Args:
            template: Deleted template
        """
        event_data = {
            "template_id": str(template.id),
            "name": template.name,
            "version": template.version,
        }
        
        await self.event_bus.publish("template.deleted", event_data)
    
    async def _publish_template_cloned_event(self, new_template, source_template) -> None:
        """
        Publish template cloned event.
        
        Args:
            new_template: Cloned template
            source_template: Source template
        """
        event_data = {
            "template_id": str(new_template.id),
            "name": new_template.name,
            "version": new_template.version,
            "source_template_id": str(source_template.id),
            "source_template_name": source_template.name,
            "source_template_version": source_template.version,
            "created_at": new_template.created_at.isoformat(),
        }
        
        await self.event_bus.publish("template.cloned", event_data)
    
    async def _publish_template_phase_created_event(self, phase) -> None:
        """
        Publish template phase created event.
        
        Args:
            phase: Created phase
        """
        event_data = {
            "phase_id": str(phase.id),
            "template_id": str(phase.template_id),
            "name": phase.name,
            "created_at": phase.created_at.isoformat(),
        }
        
        await self.event_bus.publish("template.phase.created", event_data)
