"""
Plan Creation Service for Strategic Planning.

This module provides methods for creating strategic plans from templates
and methodologies.
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from ..repository import PlanningRepository
from ..plan_template_service import PlanTemplateService
from ..planning_methodology_service import PlanningMethodologyService
from .helper_service import HelperService
from .methodology_application_service import MethodologyApplicationService

from ...models.api import (
    StrategicPlanCreate,
    StrategicPlanResponse,
    PlanPhaseCreate,
    PlanMilestoneCreate,
    PlanningTaskCreate,
    PlanStatus,
    TaskStatus,
    TaskPriority,
    DependencyType
)
from ...exceptions import (
    TemplateNotFoundError,
    MethodologyNotFoundError,
    PlanValidationError
)

from shared.utils.src.messaging import EventBus

logger = logging.getLogger(__name__)

class PlanCreationService:
    """
    Plan creation service.
    
    This service provides methods for creating strategic plans from templates
    and methodologies.
    """
    
    def __init__(
        self,
        repository: PlanningRepository,
        template_service: PlanTemplateService,
        methodology_service: PlanningMethodologyService,
        methodology_application_service: MethodologyApplicationService,
        helper_service: HelperService,
        event_bus: EventBus,
    ):
        """
        Initialize the plan creation service.
        
        Args:
            repository: Planning repository
            template_service: Plan template service
            methodology_service: Planning methodology service
            methodology_application_service: Methodology application service
            helper_service: Helper service
            event_bus: Event bus
        """
        self.repository = repository
        self.template_service = template_service
        self.methodology_service = methodology_service
        self.methodology_application_service = methodology_application_service
        self.helper_service = helper_service
        self.event_bus = event_bus
        logger.info("Plan Creation Service initialized")
    
    async def create_plan_from_template(
        self,
        project_id: UUID,
        template_id: UUID,
        plan_name: str,
        plan_description: Optional[str] = None,
        start_date: Optional[datetime] = None,
        customization_options: Optional[Dict[str, Any]] = None
    ) -> StrategicPlanResponse:
        """
        Create a strategic plan from a template.
        
        Args:
            project_id: Project ID
            template_id: Template ID
            plan_name: Plan name
            plan_description: Optional plan description
            start_date: Optional start date (defaults to current date)
            customization_options: Optional customization options
            
        Returns:
            StrategicPlanResponse: Created plan
            
        Raises:
            TemplateNotFoundError: If template not found
            PlanValidationError: If plan data is invalid
        """
        logger.info(f"Creating plan from template: {template_id}")
        
        # Get template
        try:
            template = await self.template_service.get_template(template_id)
        except TemplateNotFoundError:
            raise TemplateNotFoundError(str(template_id))
        
        # Set default start date if not provided
        if start_date is None:
            start_date = datetime.now()
        
        # Create plan data
        plan_data = StrategicPlanCreate(
            name=plan_name,
            description=plan_description or f"Plan created from template: {template.name}",
            project_id=project_id,
            template_id=template_id,
            constraints={},
            objectives={},
            status=PlanStatus.DRAFT
        )
        
        # Create plan
        plan = await self.repository.create_plan(plan_data.model_dump())
        
        # Get template phases, milestones, and tasks
        template_phases = await self.repository.list_template_phases(template_id, pagination=None)
        template_milestones = await self.repository.list_template_milestones(template_id, pagination=None)
        template_tasks = await self.repository.list_template_tasks(template_id, pagination=None)
        
        # Create phases
        phase_mapping = {}  # Map template phase IDs to new phase IDs
        for template_phase in template_phases[0]:  # [0] contains the items, [1] contains the count
            phase_data = PlanPhaseCreate(
                plan_id=plan.id,
                name=template_phase.name,
                description=template_phase.description,
                order=template_phase.order,
                start_date=start_date + timedelta(days=template_phase.order * 14),  # Example: 2 weeks per phase
                end_date=start_date + timedelta(days=(template_phase.order + 1) * 14 - 1),
                objectives=template_phase.objectives,
                deliverables=template_phase.deliverables,
                completion_criteria=template_phase.completion_criteria
            )
            new_phase = await self.repository.create_phase(phase_data.model_dump())
            phase_mapping[template_phase.id] = new_phase.id
        
        # Create milestones
        milestone_mapping = {}  # Map template milestone IDs to new milestone IDs
        for template_milestone in template_milestones[0]:
            relative_day = template_milestone.relative_day or 0
            milestone_data = PlanMilestoneCreate(
                plan_id=plan.id,
                name=template_milestone.name,
                description=template_milestone.description,
                target_date=start_date + timedelta(days=relative_day),
                priority=template_milestone.priority,
                criteria=template_milestone.criteria
            )
            new_milestone = await self.repository.create_milestone(milestone_data.model_dump())
            milestone_mapping[template_milestone.id] = new_milestone.id
        
        # Create tasks
        task_mapping = {}  # Map template task IDs to new task IDs
        for template_task in template_tasks[0]:
            # Map phase and milestone IDs
            phase_id = phase_mapping.get(template_task.phase_id) if template_task.phase_id else None
            milestone_id = milestone_mapping.get(template_task.milestone_id) if template_task.milestone_id else None
            
            task_data = PlanningTaskCreate(
                plan_id=plan.id,
                phase_id=phase_id,
                milestone_id=milestone_id,
                name=template_task.name,
                description=template_task.description,
                estimated_duration=template_task.estimated_duration,
                estimated_effort=template_task.estimated_effort,
                required_skills=template_task.required_skills,
                constraints={},
                priority=template_task.priority,
                status=TaskStatus.PENDING,
                acceptance_criteria=template_task.acceptance_criteria_template
            )
            new_task = await self.repository.create_task(task_data.model_dump())
            task_mapping[template_task.id] = new_task.id
        
        # Create dependencies
        for template_task in template_tasks[0]:
            # Get template task dependencies
            template_dependencies = await self.repository.get_template_task_dependencies(template_task.id)
            
            # Create dependencies for new tasks
            for template_dependency in template_dependencies:
                if template_dependency.from_task_id in task_mapping and template_dependency.to_task_id in task_mapping:
                    dependency_data = {
                        "from_task_id": task_mapping[template_dependency.from_task_id],
                        "to_task_id": task_mapping[template_dependency.to_task_id],
                        "dependency_type": template_dependency.dependency_type,
                        "lag": template_dependency.lag
                    }
                    await self.repository.create_dependency(dependency_data)
        
        # Publish event
        await self.helper_service.publish_plan_created_from_template_event(plan, template, self.event_bus)
        
        # Return plan response
        return await self.helper_service.to_plan_response_model(plan)
    
    async def create_plan_with_methodology(
        self,
        project_id: UUID,
        methodology_id: UUID,
        plan_name: str,
        plan_description: Optional[str] = None,
        objectives: Dict[str, Any] = None,
        constraints: Dict[str, Any] = None,
        start_date: Optional[datetime] = None
    ) -> StrategicPlanResponse:
        """
        Create a strategic plan using a planning methodology.
        
        Args:
            project_id: Project ID
            methodology_id: Methodology ID
            plan_name: Plan name
            plan_description: Optional plan description
            objectives: Optional plan objectives
            constraints: Optional plan constraints
            start_date: Optional start date (defaults to current date)
            
        Returns:
            StrategicPlanResponse: Created plan
            
        Raises:
            MethodologyNotFoundError: If methodology not found
            PlanValidationError: If plan data is invalid
        """
        logger.info(f"Creating plan with methodology: {methodology_id}")
        
        # Get methodology
        try:
            methodology = await self.methodology_service.get_methodology(methodology_id)
        except MethodologyNotFoundError:
            raise MethodologyNotFoundError(str(methodology_id))
        
        # Set default start date if not provided
        if start_date is None:
            start_date = datetime.now()
        
        # Set default objectives and constraints if not provided
        if objectives is None:
            objectives = {}
        if constraints is None:
            constraints = {}
        
        # Create plan data
        plan_data = StrategicPlanCreate(
            name=plan_name,
            description=plan_description or f"Plan created using methodology: {methodology.name}",
            project_id=project_id,
            methodology_id=methodology_id,
            constraints=constraints,
            objectives=objectives,
            status=PlanStatus.DRAFT
        )
        
        # Create plan
        plan = await self.repository.create_plan(plan_data.model_dump())
        
        # Apply methodology to create phases, milestones, and tasks
        await self.methodology_application_service.apply_methodology_to_plan(plan, methodology, start_date)
        
        # Publish event
        await self.helper_service.publish_plan_created_with_methodology_event(plan, methodology, self.event_bus)
        
        # Return plan response
        return await self.helper_service.to_plan_response_model(plan)
