"""
Task Template Service for the Planning System.

This module implements the task template service, which manages task templates
for generating standardized tasks with predefined attributes.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple, Union
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from shared.utils.src.messaging import EventBus

from ..models.api import (
    TaskTemplateCreate,
    TaskTemplateUpdate,
    TaskTemplateResponse,
    PlanningTaskCreate,
    PaginatedResponse
)
from ..exceptions import (
    TemplateNotFoundError,
    TemplateValidationError
)
from .repository import PlanningRepository
from .base import BasePlannerComponent

logger = logging.getLogger(__name__)

class TaskTemplateService(BasePlannerComponent):
    """
    Task Template Service.
    
    This service manages task templates for generating standardized tasks
    with predefined attributes, acceptance criteria, and dependencies.
    """
    
    def __init__(
        self,
        repository: PlanningRepository,
        event_bus: EventBus,
    ):
        """
        Initialize the task template service.
        
        Args:
            repository: Planning repository
            event_bus: Event bus
        """
        super().__init__(repository, event_bus, "TaskTemplateService")
    
    async def create_template(self, template_data: TaskTemplateCreate) -> TaskTemplateResponse:
        """
        Create a new task template.
        
        Args:
            template_data: Template data
            
        Returns:
            TaskTemplateResponse: Created template
            
        Raises:
            TemplateValidationError: If template data is invalid
        """
        await self._log_operation("Creating", "task template", entity_name=template_data.name)
        
        # Validate template data
        validation_errors = await self._validate_template_data(template_data)
        if validation_errors:
            raise TemplateValidationError(
                message="Invalid template data",
                validation_errors=validation_errors
            )
        
        # Convert to dict for repository
        template_dict = template_data.model_dump()
        
        # Create template in repository
        template = await self.repository.create_task_template(template_dict)
        
        # Publish event
        await self._publish_event("task_template.created", template)
        
        # Convert to response model
        return await self._to_response_model(template)
    
    async def get_template(self, template_id: UUID) -> TaskTemplateResponse:
        """
        Get a task template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            TaskTemplateResponse: Template data
            
        Raises:
            TemplateNotFoundError: If template not found
        """
        await self._log_operation("Getting", "task template", entity_id=template_id)
        
        # Get template from repository
        template = await self.repository.get_task_template_by_id(template_id)
        
        if not template:
            await self._handle_not_found_error("task template", template_id, TemplateNotFoundError)
        
        # Convert to response model
        return await self._to_response_model(template)
    
    async def list_templates(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """
        List task templates with filtering and pagination.
        
        Args:
            category: Optional category filter
            tags: Optional tags filter
            page: Page number
            page_size: Items per page
            
        Returns:
            PaginatedResponse: Paginated list of templates
        """
        await self._log_operation("Listing", "task templates")
        
        # Build filters
        filters = {}
        if category:
            filters["category"] = category
        if tags:
            filters["tags"] = tags
        
        # Get templates from repository
        templates, total = await self.repository.list_task_templates(
            filters=filters,
            pagination={"page": page, "page_size": page_size}
        )
        
        # Convert to response models
        template_responses = [await self._to_response_model(template) for template in templates]
        
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
        template_data: TaskTemplateUpdate
    ) -> TaskTemplateResponse:
        """
        Update a task template.
        
        Args:
            template_id: Template ID
            template_data: Template data to update
            
        Returns:
            TaskTemplateResponse: Updated template
            
        Raises:
            TemplateNotFoundError: If template not found
            TemplateValidationError: If update data is invalid
        """
        await self._log_operation("Updating", "task template", entity_id=template_id)
        
        # Get existing template
        template = await self.repository.get_task_template_by_id(template_id)
        if not template:
            await self._handle_not_found_error("task template", template_id, TemplateNotFoundError)
        
        # Validate update data
        validation_errors = await self._validate_template_update(template_id, template_data)
        if validation_errors:
            raise TemplateValidationError(
                message="Invalid template update",
                validation_errors=validation_errors
            )
        
        # Convert to dict for repository
        update_dict = template_data.model_dump(exclude_unset=True)
        
        # Update template in repository
        template = await self.repository.update_task_template(template_id, update_dict)
        
        if not template:
            await self._handle_not_found_error("task template", template_id, TemplateNotFoundError)
        
        # Publish event
        await self._publish_event("task_template.updated", template)
        
        # Convert to response model
        return await self._to_response_model(template)
    
    async def delete_template(self, template_id: UUID) -> None:
        """
        Delete a task template.
        
        Args:
            template_id: Template ID
            
        Raises:
            TemplateNotFoundError: If template not found
        """
        await self._log_operation("Deleting", "task template", entity_id=template_id)
        
        # Get template data for event
        template = await self.repository.get_task_template_by_id(template_id)
        
        if not template:
            await self._handle_not_found_error("task template", template_id, TemplateNotFoundError)
        
        # Delete template in repository
        success = await self.repository.delete_task_template(template_id)
        
        if not success:
            await self._handle_not_found_error("task template", template_id, TemplateNotFoundError)
        
        # Publish event
        await self._publish_event("task_template.deleted", template)
    
    async def generate_task_from_template(
        self,
        template_id: UUID,
        plan_id: UUID,
        phase_id: Optional[UUID] = None,
        milestone_id: Optional[UUID] = None,
        custom_attributes: Optional[Dict[str, Any]] = None
    ) -> PlanningTaskCreate:
        """
        Generate a task from a template.
        
        Args:
            template_id: Template ID
            plan_id: Plan ID
            phase_id: Optional phase ID
            milestone_id: Optional milestone ID
            custom_attributes: Optional custom attributes to override template defaults
            
        Returns:
            PlanningTaskCreate: Generated task data
            
        Raises:
            TemplateNotFoundError: If template not found
        """
        await self._log_operation(
            "Generating", 
            "task from template", 
            entity_id=template_id,
            entity_name=f"for plan {plan_id}"
        )
        
        # Get template
        template = await self.repository.get_task_template_by_id(template_id)
        
        if not template:
            await self._handle_not_found_error("task template", template_id, TemplateNotFoundError)
        
        # Merge custom attributes with template defaults
        task_attributes = {
            "name": template.name,
            "description": template.description,
            "estimated_duration": template.estimated_duration,
            "estimated_effort": template.estimated_effort,
            "required_skills": template.required_skills,
            "constraints": template.constraints,
            "priority": template.priority,
            "acceptance_criteria": template.acceptance_criteria,
            "plan_id": plan_id,
            "phase_id": phase_id,
            "milestone_id": milestone_id,
        }
        
        # Override with custom attributes
        if custom_attributes:
            task_attributes.update(custom_attributes)
        
        # Create task data
        task_data = PlanningTaskCreate(**task_attributes)
        
        return task_data
    
    async def generate_tasks_from_category(
        self,
        category: str,
        plan_id: UUID,
        phase_id: Optional[UUID] = None,
        milestone_id: Optional[UUID] = None,
        custom_attributes: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[PlanningTaskCreate]:
        """
        Generate multiple tasks from templates in a category.
        
        Args:
            category: Template category
            plan_id: Plan ID
            phase_id: Optional phase ID
            milestone_id: Optional milestone ID
            custom_attributes: Optional custom attributes by template ID
            
        Returns:
            List[PlanningTaskCreate]: Generated task data
            
        Raises:
            TemplateNotFoundError: If no templates found in category
        """
        await self._log_operation(
            "Generating", 
            "tasks from category", 
            entity_name=f"{category} for plan {plan_id}"
        )
        
        # Get templates in category
        templates, _ = await self.repository.list_task_templates(
            filters={"category": category},
            pagination=None  # Get all
        )
        
        if not templates:
            raise TemplateNotFoundError(f"No templates found in category: {category}")
        
        # Generate tasks from each template
        tasks = []
        for template in templates:
            # Get custom attributes for this template, if any
            template_custom_attrs = None
            if custom_attributes and str(template.id) in custom_attributes:
                template_custom_attrs = custom_attributes[str(template.id)]
            
            # Generate task
            task_data = await self.generate_task_from_template(
                template_id=template.id,
                plan_id=plan_id,
                phase_id=phase_id,
                milestone_id=milestone_id,
                custom_attributes=template_custom_attrs
            )
            
            tasks.append(task_data)
        
        return tasks
    
    async def generate_acceptance_criteria(
        self,
        task_description: str,
        task_type: Optional[str] = None,
        num_criteria: int = 3
    ) -> List[str]:
        """
        Generate acceptance criteria for a task.
        
        Args:
            task_description: Task description
            task_type: Optional task type
            num_criteria: Number of criteria to generate
            
        Returns:
            List[str]: Generated acceptance criteria
        """
        await self._log_operation("Generating", "acceptance criteria")
        
        # In a real implementation, this might use an AI service or predefined patterns
        # For this example, we'll use simple templates
        
        criteria = []
        
        # Basic criteria templates
        templates = [
            "The {task_type} should {action} when {condition}.",
            "Verify that {requirement} is implemented correctly.",
            "The {task_type} must {requirement} with {quality} quality.",
            "All {components} should be {state} after {action}.",
            "The {task_type} should handle {edge_case} gracefully.",
            "Documentation for {task_type} is complete and accurate.",
            "All tests for {task_type} pass successfully.",
            "The {task_type} meets performance requirements under {condition}.",
            "User feedback confirms that {requirement} works as expected.",
            "Code review confirms that {task_type} follows best practices."
        ]
        
        # Extract keywords from description
        keywords = task_description.lower().split()
        keywords = [word for word in keywords if len(word) > 3]
        
        # Default task type if not provided
        if not task_type:
            task_type = "component"
        
        # Generate criteria
        import random
        random.seed(hash(task_description))  # Deterministic but unique to the task
        
        for i in range(min(num_criteria, len(templates))):
            template = templates[i]
            
            # Replace placeholders with relevant content
            criteria_text = template.format(
                task_type=task_type,
                action=random.choice(["function correctly", "perform as expected", "meet requirements"]),
                condition=random.choice(["normal conditions", "edge cases", "high load"]),
                requirement=random.choice(["functionality", "feature", "behavior"]),
                quality=random.choice(["high", "acceptable", "production-ready"]),
                components=random.choice(["components", "modules", "elements"]),
                state=random.choice(["functional", "validated", "documented"]),
                edge_case=random.choice(["error conditions", "invalid input", "resource constraints"])
            )
            
            criteria.append(criteria_text)
        
        return criteria
    
    # Helper methods
    
    async def _validate_template_data(self, template_data: TaskTemplateCreate) -> List[str]:
        """
        Validate template data for creation.
        
        Args:
            template_data: Template data
            
        Returns:
            List[str]: Validation errors, empty if valid
        """
        validation_errors = []
        
        # Check for required skills if they require a minimum proficiency
        if template_data.required_skills:
            for skill, proficiency in template_data.required_skills.items():
                if not isinstance(proficiency, (int, float)) or proficiency < 0 or proficiency > 1:
                    validation_errors.append(f"Skill proficiency for {skill} must be between 0 and 1")
        
        # Validate estimated duration and effort consistency
        if template_data.estimated_duration > 0 and template_data.estimated_effort > 0:
            if template_data.estimated_effort < template_data.estimated_duration:
                validation_errors.append("Estimated effort cannot be less than estimated duration")
        
        # Validate acceptance criteria
        if template_data.acceptance_criteria:
            if not isinstance(template_data.acceptance_criteria, list):
                validation_errors.append("Acceptance criteria must be a list")
            elif any(not isinstance(criteria, str) for criteria in template_data.acceptance_criteria):
                validation_errors.append("Each acceptance criterion must be a string")
        
        return validation_errors
    
    async def _validate_template_update(self, template_id: UUID, template_data: TaskTemplateUpdate) -> List[str]:
        """
        Validate template data for update.
        
        Args:
            template_id: Template ID
            template_data: Template data
            
        Returns:
            List[str]: Validation errors, empty if valid
        """
        validation_errors = []
        
        # Check for required skills if they require a minimum proficiency
        if template_data.required_skills is not None:
            for skill, proficiency in template_data.required_skills.items():
                if not isinstance(proficiency, (int, float)) or proficiency < 0 or proficiency > 1:
                    validation_errors.append(f"Skill proficiency for {skill} must be between 0 and 1")
        
        # Validate estimated duration and effort consistency
        if template_data.estimated_duration is not None and template_data.estimated_effort is not None:
            if template_data.estimated_effort < template_data.estimated_duration:
                validation_errors.append("Estimated effort cannot be less than estimated duration")
        
        # Validate acceptance criteria
        if template_data.acceptance_criteria is not None:
            if not isinstance(template_data.acceptance_criteria, list):
                validation_errors.append("Acceptance criteria must be a list")
            elif any(not isinstance(criteria, str) for criteria in template_data.acceptance_criteria):
                validation_errors.append("Each acceptance criterion must be a string")
        
        return validation_errors
    
    async def _to_response_model(self, template) -> TaskTemplateResponse:
        """
        Convert a template model to a response model.
        
        Args:
            template: Task template model
            
        Returns:
            TaskTemplateResponse: Template response model
        """
        # Convert to response model
        return TaskTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            category=template.category,
            tags=template.tags,
            estimated_duration=template.estimated_duration,
            estimated_effort=template.estimated_effort,
            required_skills=template.required_skills,
            constraints=template.constraints,
            priority=template.priority,
            acceptance_criteria=template.acceptance_criteria,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
