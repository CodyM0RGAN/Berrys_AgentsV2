"""
Plan Generation Service for Strategic Planning.

This module provides methods for generating strategic plan structures.
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from ..repository import PlanningRepository
from .helper_service import HelperService

from ...models.api import (
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
    PlanNotFoundError,
    PlanValidationError
)

from shared.utils.src.messaging import EventBus

logger = logging.getLogger(__name__)

class PlanGenerationService:
    """
    Plan generation service.
    
    This service provides methods for generating strategic plan structures.
    """
    
    def __init__(
        self,
        repository: PlanningRepository,
        helper_service: HelperService,
        event_bus: EventBus,
    ):
        """
        Initialize the plan generation service.
        
        Args:
            repository: Planning repository
            helper_service: Helper service
            event_bus: Event bus
        """
        self.repository = repository
        self.helper_service = helper_service
        self.event_bus = event_bus
        logger.info("Plan Generation Service initialized")
    
    async def generate_plan_structure(
        self,
        plan_id: UUID,
        generation_options: Dict[str, Any] = None
    ) -> StrategicPlanResponse:
        """
        Generate plan structure using AI assistance.
        
        Args:
            plan_id: Plan ID
            generation_options: Optional generation options
            
        Returns:
            StrategicPlanResponse: Updated plan
            
        Raises:
            PlanNotFoundError: If plan not found
            PlanValidationError: If plan is not in DRAFT status
        """
        logger.info(f"Generating plan structure for plan: {plan_id}")
        
        # Get plan
        plan = await self.repository.get_plan_by_id(plan_id)
        if not plan:
            raise PlanNotFoundError(str(plan_id))
        
        # Validate plan is in DRAFT status
        if plan.status != PlanStatus.DRAFT:
            raise PlanValidationError(
                message="Cannot generate structure for non-draft plan",
                validation_errors=["Plan must be in DRAFT status to generate structure"]
            )
        
        # Set default generation options if not provided
        if generation_options is None:
            generation_options = {
                "complexity": "medium",
                "detail_level": "medium",
                "include_milestones": True,
                "include_dependencies": True
            }
        
        # Get project details for context
        project = await self.repository.get_project_by_id(plan.project_id)
        
        # Generate plan structure using AI
        structure = await self._generate_ai_plan_structure(plan, project, generation_options)
        
        # Apply generated structure to plan
        await self._apply_generated_structure(plan, structure)
        
        # Publish event
        await self.helper_service.publish_plan_structure_generated_event(plan, self.event_bus)
        
        # Return updated plan response
        return await self.helper_service.to_plan_response_model(plan)
    
    async def _generate_ai_plan_structure(
        self,
        plan,
        project,
        generation_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate plan structure using AI.
        
        Args:
            plan: Plan model
            project: Project model
            generation_options: Generation options
            
        Returns:
            Dict[str, Any]: Generated structure
        """
        # This is a placeholder for actual AI-based generation
        # In a real implementation, this would call an AI service
        
        complexity = generation_options.get("complexity", "medium")
        detail_level = generation_options.get("detail_level", "medium")
        include_milestones = generation_options.get("include_milestones", True)
        include_dependencies = generation_options.get("include_dependencies", True)
        
        # Generate a basic structure based on options
        structure = {
            "phases": [],
            "milestones": [],
            "tasks": [],
            "dependencies": []
        }
        
        # Generate phases
        num_phases = {"low": 3, "medium": 5, "high": 8}[complexity]
        for i in range(num_phases):
            phase = {
                "name": f"Phase {i + 1}",
                "description": f"Description for Phase {i + 1}",
                "order": i,
                "start_date": (plan.created_at + timedelta(weeks=i * 4)).isoformat(),
                "end_date": (plan.created_at + timedelta(weeks=(i + 1) * 4 - 1)).isoformat(),
                "objectives": {"goal": f"Complete Phase {i + 1}"},
                "deliverables": {"deliverable": f"Phase {i + 1} deliverables"},
                "completion_criteria": {"criteria": f"Phase {i + 1} criteria met"}
            }
            structure["phases"].append(phase)
        
        # Generate milestones if requested
        if include_milestones:
            # Start milestone
            structure["milestones"].append({
                "name": "Project Start",
                "description": "Project kickoff",
                "target_date": plan.created_at.isoformat(),
                "priority": "HIGH",
                "criteria": {"criteria": "Project approved and resources allocated"}
            })
            
            # Mid-project milestones
            for i in range(num_phases // 2):
                milestone_date = (plan.created_at + timedelta(weeks=(i + 1) * 8)).isoformat()
                structure["milestones"].append({
                    "name": f"Milestone {i + 1}",
                    "description": f"Milestone {i + 1} description",
                    "target_date": milestone_date,
                    "priority": "MEDIUM",
                    "criteria": {"criteria": f"Milestone {i + 1} criteria met"}
                })
            
            # End milestone
            end_date = (plan.created_at + timedelta(weeks=num_phases * 4)).isoformat()
            structure["milestones"].append({
                "name": "Project Complete",
                "description": "Project completion",
                "target_date": end_date,
                "priority": "HIGH",
                "criteria": {"criteria": "All deliverables accepted and project closed"}
            })
        
        # Generate tasks
        tasks_per_phase = {"low": 3, "medium": 5, "high": 8}[detail_level]
        task_id = 0
        
        for phase_idx, phase in enumerate(structure["phases"]):
            for i in range(tasks_per_phase):
                task = {
                    "id": task_id,
                    "name": f"Task {phase_idx + 1}.{i + 1}",
                    "description": f"Description for Task {phase_idx + 1}.{i + 1}",
                    "phase_idx": phase_idx,
                    "estimated_duration": 40,  # 40 hours
                    "estimated_effort": 40,  # 40 person-hours
                    "priority": "MEDIUM",
                    "status": "PENDING"
                }
                structure["tasks"].append(task)
                task_id += 1
        
        # Generate dependencies if requested
        if include_dependencies and structure["tasks"]:
            # Create finish-to-start dependencies between consecutive tasks in the same phase
            for phase_idx in range(len(structure["phases"])):
                phase_tasks = [t for t in structure["tasks"] if t["phase_idx"] == phase_idx]
                for i in range(len(phase_tasks) - 1):
                    dependency = {
                        "from_task_id": phase_tasks[i]["id"],
                        "to_task_id": phase_tasks[i + 1]["id"],
                        "dependency_type": "FINISH_TO_START",
                        "lag": 0
                    }
                    structure["dependencies"].append(dependency)
            
            # Create dependencies between the last task of a phase and the first task of the next phase
            for phase_idx in range(len(structure["phases"]) - 1):
                current_phase_tasks = [t for t in structure["tasks"] if t["phase_idx"] == phase_idx]
                next_phase_tasks = [t for t in structure["tasks"] if t["phase_idx"] == phase_idx + 1]
                
                if current_phase_tasks and next_phase_tasks:
                    dependency = {
                        "from_task_id": current_phase_tasks[-1]["id"],
                        "to_task_id": next_phase_tasks[0]["id"],
                        "dependency_type": "FINISH_TO_START",
                        "lag": 0
                    }
                    structure["dependencies"].append(dependency)
        
        return structure
    
    async def _apply_generated_structure(
        self,
        plan,
        structure: Dict[str, Any]
    ) -> None:
        """
        Apply generated structure to plan.
        
        Args:
            plan: Plan model
            structure: Generated structure
        """
        # Create phases
        phase_mapping = {}  # Map structure phase indices to actual phase IDs
        for i, phase_data in enumerate(structure["phases"]):
            phase_create = PlanPhaseCreate(
                plan_id=plan.id,
                name=phase_data["name"],
                description=phase_data["description"],
                order=phase_data["order"],
                start_date=datetime.fromisoformat(phase_data["start_date"]),
                end_date=datetime.fromisoformat(phase_data["end_date"]),
                objectives=phase_data["objectives"],
                deliverables=phase_data["deliverables"],
                completion_criteria=phase_data["completion_criteria"]
            )
            phase = await self.repository.create_phase(phase_create.model_dump())
            phase_mapping[i] = phase.id
        
        # Create milestones
        milestone_mapping = {}  # Map structure milestone indices to actual milestone IDs
        for i, milestone_data in enumerate(structure["milestones"]):
            milestone_create = PlanMilestoneCreate(
                plan_id=plan.id,
                name=milestone_data["name"],
                description=milestone_data["description"],
                target_date=datetime.fromisoformat(milestone_data["target_date"]),
                priority=TaskPriority[milestone_data["priority"]],
                criteria=milestone_data["criteria"]
            )
            milestone = await self.repository.create_milestone(milestone_create.model_dump())
            milestone_mapping[i] = milestone.id
        
        # Create tasks
        task_mapping = {}  # Map structure task IDs to actual task IDs
        for task_data in structure["tasks"]:
            phase_id = phase_mapping.get(task_data["phase_idx"])
            
            task_create = PlanningTaskCreate(
                plan_id=plan.id,
                phase_id=phase_id,
                milestone_id=None,  # No milestone association in this simple example
                name=task_data["name"],
                description=task_data["description"],
                estimated_duration=task_data["estimated_duration"],
                estimated_effort=task_data["estimated_effort"],
                required_skills={},
                constraints={},
                priority=TaskPriority[task_data["priority"]],
                status=TaskStatus[task_data["status"]],
                acceptance_criteria={}
            )
            task = await self.repository.create_task(task_create.model_dump())
            task_mapping[task_data["id"]] = task.id
        
        # Create dependencies
        for dependency_data in structure["dependencies"]:
            from_task_id = task_mapping.get(dependency_data["from_task_id"])
            to_task_id = task_mapping.get(dependency_data["to_task_id"])
            
            if from_task_id and to_task_id:
                dependency_create = {
                    "from_task_id": from_task_id,
                    "to_task_id": to_task_id,
                    "dependency_type": DependencyType[dependency_data["dependency_type"]],
                    "lag": dependency_data["lag"]
                }
                await self.repository.create_dependency(dependency_create)
