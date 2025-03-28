"""
Methodology Application Service for Strategic Planning.

This module provides methods for applying planning methodologies to strategic plans.
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from ..repository import PlanningRepository

from ...models.api import (
    PlanPhaseCreate,
    PlanMilestoneCreate,
    PlanningTaskCreate,
    TaskStatus,
    TaskPriority,
    DependencyType
)

logger = logging.getLogger(__name__)

class MethodologyApplicationService:
    """
    Methodology application service.
    
    This service provides methods for applying planning methodologies to strategic plans.
    """
    
    def __init__(self, repository: PlanningRepository):
        """
        Initialize the methodology application service.
        
        Args:
            repository: Planning repository
        """
        self.repository = repository
        logger.info("Methodology Application Service initialized")
    
    async def apply_methodology_to_plan(
        self,
        plan,
        methodology,
        start_date: datetime
    ) -> None:
        """
        Apply a planning methodology to create plan structure.
        
        Args:
            plan: Plan model
            methodology: Methodology model
            start_date: Start date
        """
        methodology_type = methodology.methodology_type.upper()
        parameters = methodology.parameters
        
        if methodology_type == "AGILE":
            await self.apply_agile_methodology(plan, parameters, start_date)
        elif methodology_type == "WATERFALL":
            await self.apply_waterfall_methodology(plan, parameters, start_date)
        elif methodology_type == "CRITICAL_PATH":
            await self.apply_critical_path_methodology(plan, parameters, start_date)
        else:
            # Default methodology application
            await self.apply_default_methodology(plan, parameters, start_date)
    
    async def apply_agile_methodology(
        self,
        plan,
        parameters: Dict[str, Any],
        start_date: datetime
    ) -> None:
        """
        Apply Agile methodology to create plan structure.
        
        Args:
            plan: Plan model
            parameters: Methodology parameters
            start_date: Start date
        """
        # Extract parameters
        sprint_duration = parameters.get("sprint_duration", 2)  # Default: 2 weeks
        num_sprints = parameters.get("num_sprints", 6)  # Default: 6 sprints
        backlog_phase = parameters.get("include_backlog_phase", True)
        
        # Create phases
        phases = []
        
        # Create backlog phase if specified
        if backlog_phase:
            backlog_phase_data = PlanPhaseCreate(
                plan_id=plan.id,
                name="Product Backlog",
                description="Initial product backlog items",
                order=0,
                start_date=start_date,
                end_date=start_date + timedelta(days=7),
                objectives={"goal": "Define initial product backlog"},
                deliverables={"deliverable": "Prioritized product backlog"},
                completion_criteria={"criteria": "Product backlog prioritized and estimated"}
            )
            phases.append(await self.repository.create_phase(backlog_phase_data.model_dump()))
        
        # Create sprint phases
        for i in range(num_sprints):
            sprint_start = start_date + timedelta(days=7 if backlog_phase else 0) + timedelta(weeks=i * sprint_duration)
            sprint_end = sprint_start + timedelta(weeks=sprint_duration) - timedelta(days=1)
            
            sprint_phase_data = PlanPhaseCreate(
                plan_id=plan.id,
                name=f"Sprint {i + 1}",
                description=f"Sprint {i + 1} execution",
                order=i + (1 if backlog_phase else 0),
                start_date=sprint_start,
                end_date=sprint_end,
                objectives={"goal": f"Complete Sprint {i + 1} goals"},
                deliverables={"deliverable": "Working software increment"},
                completion_criteria={"criteria": "Sprint goals achieved"}
            )
            phases.append(await self.repository.create_phase(sprint_phase_data.model_dump()))
        
        # Create milestones
        milestones = []
        
        # Initial milestone
        initial_milestone_data = PlanMilestoneCreate(
            plan_id=plan.id,
            name="Project Kickoff",
            description="Project kickoff and initial planning",
            target_date=start_date,
            priority=TaskPriority.HIGH,
            criteria={"criteria": "Project team assembled and initial planning complete"}
        )
        milestones.append(await self.repository.create_milestone(initial_milestone_data.model_dump()))
        
        # Release milestones
        num_releases = parameters.get("num_releases", 2)  # Default: 2 releases
        for i in range(num_releases):
            release_sprint = ((i + 1) * num_sprints) // num_releases
            release_date = start_date + timedelta(days=7 if backlog_phase else 0) + timedelta(weeks=release_sprint * sprint_duration)
            
            release_milestone_data = PlanMilestoneCreate(
                plan_id=plan.id,
                name=f"Release {i + 1}",
                description=f"Release {i + 1} to production",
                target_date=release_date,
                priority=TaskPriority.HIGH,
                criteria={"criteria": f"Release {i + 1} criteria met"}
            )
            milestones.append(await self.repository.create_milestone(release_milestone_data.model_dump()))
        
        # Create standard tasks for each sprint
        for i, phase in enumerate(phases):
            if i == 0 and backlog_phase:
                # Backlog phase tasks
                tasks = [
                    {"name": "Define product vision", "duration": 8, "effort": 8},
                    {"name": "Create initial user stories", "duration": 16, "effort": 16},
                    {"name": "Prioritize backlog", "duration": 8, "effort": 8},
                    {"name": "Estimate backlog items", "duration": 8, "effort": 16}
                ]
            else:
                # Sprint phase tasks
                tasks = [
                    {"name": "Sprint planning", "duration": 4, "effort": 16},
                    {"name": "Daily standups", "duration": sprint_duration * 5 * 0.25, "effort": sprint_duration * 5 * 1},
                    {"name": "Development work", "duration": sprint_duration * 5 * 6, "effort": sprint_duration * 5 * 6},
                    {"name": "Sprint review", "duration": 2, "effort": 8},
                    {"name": "Sprint retrospective", "duration": 2, "effort": 8}
                ]
            
            # Create tasks for this phase
            for j, task_info in enumerate(tasks):
                task_data = PlanningTaskCreate(
                    plan_id=plan.id,
                    phase_id=phase.id,
                    milestone_id=None,
                    name=task_info["name"],
                    description=f"{task_info['name']} for {phase.name}",
                    estimated_duration=task_info["duration"],
                    estimated_effort=task_info["effort"],
                    required_skills={},
                    constraints={},
                    priority=TaskPriority.MEDIUM,
                    status=TaskStatus.PENDING,
                    acceptance_criteria={}
                )
                await self.repository.create_task(task_data.model_dump())
    
    async def apply_waterfall_methodology(
        self,
        plan,
        parameters: Dict[str, Any],
        start_date: datetime
    ) -> None:
        """
        Apply Waterfall methodology to create plan structure.
        
        Args:
            plan: Plan model
            parameters: Methodology parameters
            start_date: Start date
        """
        # Extract parameters
        phase_structure = parameters.get("phase_structure", [
            {"name": "Requirements", "duration": 4},
            {"name": "Design", "duration": 6},
            {"name": "Implementation", "duration": 12},
            {"name": "Testing", "duration": 6},
            {"name": "Deployment", "duration": 2},
            {"name": "Maintenance", "duration": 4}
        ])
        
        # Create phases
        phases = []
        current_date = start_date
        
        for i, phase_info in enumerate(phase_structure):
            phase_duration = phase_info.get("duration", 4)  # Default: 4 weeks
            phase_end = current_date + timedelta(weeks=phase_duration) - timedelta(days=1)
            
            phase_data = PlanPhaseCreate(
                plan_id=plan.id,
                name=phase_info["name"],
                description=f"{phase_info['name']} phase",
                order=i,
                start_date=current_date,
                end_date=phase_end,
                objectives={"goal": f"Complete {phase_info['name']} phase"},
                deliverables={"deliverable": f"{phase_info['name']} deliverables"},
                completion_criteria={"criteria": f"{phase_info['name']} criteria met"}
            )
            phases.append(await self.repository.create_phase(phase_data.model_dump()))
            
            # Update current date for next phase
            current_date = phase_end + timedelta(days=1)
        
        # Create milestones
        milestones = []
        
        # Project start milestone
        start_milestone_data = PlanMilestoneCreate(
            plan_id=plan.id,
            name="Project Start",
            description="Project kickoff",
            target_date=start_date,
            priority=TaskPriority.HIGH,
            criteria={"criteria": "Project approved and resources allocated"}
        )
        milestones.append(await self.repository.create_milestone(start_milestone_data.model_dump()))
        
        # Phase completion milestones
        for i, phase in enumerate(phases):
            milestone_data = PlanMilestoneCreate(
                plan_id=plan.id,
                name=f"{phase.name} Complete",
                description=f"Completion of {phase.name} phase",
                target_date=phase.end_date,
                priority=TaskPriority.MEDIUM,
                criteria={"criteria": f"{phase.name} deliverables approved"}
            )
            milestones.append(await self.repository.create_milestone(milestone_data.model_dump()))
        
        # Project completion milestone
        end_date = phases[-1].end_date if phases else start_date + timedelta(weeks=24)
        end_milestone_data = PlanMilestoneCreate(
            plan_id=plan.id,
            name="Project Complete",
            description="Project completion",
            target_date=end_date,
            priority=TaskPriority.HIGH,
            criteria={"criteria": "All deliverables accepted and project closed"}
        )
        milestones.append(await self.repository.create_milestone(end_milestone_data.model_dump()))
        
        # Create standard tasks for each phase
        for phase in phases:
            # Define phase-specific tasks
            if phase.name == "Requirements":
                tasks = [
                    {"name": "Gather requirements", "duration": 40, "effort": 80},
                    {"name": "Document requirements", "duration": 40, "effort": 40},
                    {"name": "Review requirements", "duration": 16, "effort": 32},
                    {"name": "Approve requirements", "duration": 8, "effort": 16}
                ]
            elif phase.name == "Design":
                tasks = [
                    {"name": "Create system architecture", "duration": 40, "effort": 40},
                    {"name": "Design database", "duration": 40, "effort": 40},
                    {"name": "Design UI/UX", "duration": 40, "effort": 40},
                    {"name": "Review design", "duration": 16, "effort": 32},
                    {"name": "Approve design", "duration": 8, "effort": 16}
                ]
            elif phase.name == "Implementation":
                tasks = [
                    {"name": "Develop backend", "duration": 120, "effort": 120},
                    {"name": "Develop frontend", "duration": 120, "effort": 120},
                    {"name": "Integrate components", "duration": 40, "effort": 40},
                    {"name": "Code review", "duration": 24, "effort": 48}
                ]
            elif phase.name == "Testing":
                tasks = [
                    {"name": "Create test plan", "duration": 16, "effort": 16},
                    {"name": "Develop test cases", "duration": 24, "effort": 24},
                    {"name": "Execute tests", "duration": 80, "effort": 80},
                    {"name": "Fix defects", "duration": 40, "effort": 40},
                    {"name": "Regression testing", "duration": 24, "effort": 24}
                ]
            elif phase.name == "Deployment":
                tasks = [
                    {"name": "Create deployment plan", "duration": 8, "effort": 8},
                    {"name": "Prepare environment", "duration": 16, "effort": 16},
                    {"name": "Deploy application", "duration": 8, "effort": 16},
                    {"name": "Verify deployment", "duration": 8, "effort": 16}
                ]
            elif phase.name == "Maintenance":
                tasks = [
                    {"name": "Monitor system", "duration": 40, "effort": 40},
                    {"name": "Fix issues", "duration": 24, "effort": 24},
                    {"name": "Document lessons learned", "duration": 16, "effort": 16}
                ]
            else:
                tasks = [
                    {"name": f"{phase.name} Task 1", "duration": 40, "effort": 40},
                    {"name": f"{phase.name} Task 2", "duration": 40, "effort": 40}
                ]
            
            # Create tasks for this phase
            for task_info in tasks:
                task_data = PlanningTaskCreate(
                    plan_id=plan.id,
                    phase_id=phase.id,
                    milestone_id=None,
                    name=task_info["name"],
                    description=f"{task_info['name']} for {phase.name} phase",
                    estimated_duration=task_info["duration"],
                    estimated_effort=task_info["effort"],
                    required_skills={},
                    constraints={},
                    priority=TaskPriority.MEDIUM,
                    status=TaskStatus.PENDING,
                    acceptance_criteria={}
                )
                await self.repository.create_task(task_data.model_dump())
    
    async def apply_critical_path_methodology(
        self,
        plan,
        parameters: Dict[str, Any],
        start_date: datetime
    ) -> None:
        """
        Apply Critical Path methodology to create plan structure.
        
        Args:
            plan: Plan model
            parameters: Methodology parameters
            start_date: Start date
        """
        # Extract parameters
        algorithm = parameters.get("critical_path_algorithm", "standard")
        task_structure = parameters.get("task_structure", [
            {"name": "Project Planning", "duration": 2, "dependencies": []},
            {"name": "Requirements Analysis", "duration": 3, "dependencies": [0]},
            {"name": "Design", "duration": 4, "dependencies": [1]},
            {"name": "Implementation", "duration": 8, "dependencies": [2]},
            {"name": "Testing", "duration": 4, "dependencies": [3]},
            {"name": "Deployment", "duration": 2, "dependencies": [4]},
            {"name": "Documentation", "duration": 3, "dependencies": [2, 3]},
            {"name": "Training", "duration": 2, "dependencies": [5, 6]}
        ])
        
        # Create a single phase
        phase_data = PlanPhaseCreate(
            plan_id=plan.id,
            name="Project Execution",
            description="Project execution phase",
            order=0,
            start_date=start_date,
            end_date=start_date + timedelta(weeks=12),  # Placeholder end date
            objectives={"goal": "Complete project on schedule"},
            deliverables={"deliverable": "Project deliverables"},
            completion_criteria={"criteria": "All tasks completed"}
        )
        phase = await self.repository.create_phase(phase_data.model_dump())
        
        # Create tasks
        tasks = []
        current_date = start_date
        
        for i, task_info in enumerate(task_structure):
            task_duration = task_info.get("duration", 1)  # Default: 1 week
            
            task_data = PlanningTaskCreate(
                plan_id=plan.id,
                phase_id=phase.id,
                milestone_id=None,
                name=task_info["name"],
                description=f"{task_info['name']} task",
                estimated_duration=task_duration * 40,  # Convert weeks to hours
                estimated_effort=task_duration * 40,  # Assume 1:1 duration to effort
                required_skills={},
                constraints={},
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                acceptance_criteria={}
            )
            task = await self.repository.create_task(task_data.model_dump())
            tasks.append(task)
        
        # Create dependencies
        for i, task_info in enumerate(task_structure):
            for dep_idx in task_info.get("dependencies", []):
                if dep_idx < len(tasks):
                    dependency_data = {
                        "from_task_id": tasks[dep_idx].id,
                        "to_task_id": tasks[i].id,
                        "dependency_type": DependencyType.FINISH_TO_START,
                        "lag": 0
                    }
                    await self.repository.create_dependency(dependency_data)
        
        # Create milestones
        # Project start milestone
        start_milestone_data = PlanMilestoneCreate(
            plan_id=plan.id,
            name="Project Start",
            description="Project kickoff",
            target_date=start_date,
            priority=TaskPriority.HIGH,
            criteria={"criteria": "Project approved and resources allocated"}
        )
        await self.repository.create_milestone(start_milestone_data.model_dump())
        
        # Project end milestone
        end_date = start_date + timedelta(weeks=sum(task["duration"] for task in task_structure))
        end_milestone_data = PlanMilestoneCreate(
            plan_id=plan.id,
            name="Project Complete",
            description="Project completion",
            target_date=end_date,
            priority=TaskPriority.HIGH,
            criteria={"criteria": "All deliverables accepted and project closed"}
        )
        await self.repository.create_milestone(end_milestone_data.model_dump())
    
    async def apply_default_methodology(
        self,
        plan,
        parameters: Dict[str, Any],
        start_date: datetime
    ) -> None:
        """
        Apply default methodology to create plan structure.
        
        Args:
            plan: Plan model
            parameters: Methodology parameters
            start_date: Start date
        """
        # Create basic phases
        phases = []
        phase_names = ["Planning", "Execution", "Monitoring", "Closure"]
        
        for i, name in enumerate(phase_names):
            phase_start = start_date + timedelta(weeks=i * 4)
            phase_end = phase_start + timedelta(weeks=4) - timedelta(days=1)
            
            phase_data = PlanPhaseCreate(
                plan_id=plan.id,
                name=name,
                description=f"{name} phase",
                order=i,
                start_date=phase_start,
                end_date=phase_end,
                objectives={"goal": f"Complete {name} phase"},
                deliverables={"deliverable": f"{name} deliverables"},
                completion_criteria={"criteria": f"{name} criteria met"}
            )
            phases.append(await self.repository.create_phase(phase_data.model_dump()))
        
        # Create basic milestones
        milestones = []
        
        # Project start milestone
        start_milestone_data = PlanMilestoneCreate(
            plan_id=plan.id,
            name="Project Start",
            description="Project kickoff",
            target_date=start_date,
            priority=TaskPriority.HIGH,
            criteria={"criteria": "Project approved and resources allocated"}
        )
        milestones.append(await self.repository.create_milestone(start_milestone_data.model_dump()))
        
        # Project end milestone
        end_date = phases[-1].end_date if phases else start_date + timedelta(weeks=16)
        end_milestone_data = PlanMilestoneCreate(
            plan_id=plan.id,
            name="Project Complete",
            description="Project completion",
            target_date=end_date,
            priority=TaskPriority.HIGH,
            criteria={"criteria": "All deliverables accepted and project closed"}
        )
        milestones.append(await self.repository.create_milestone(end_milestone_data.model_dump()))
        
        # Create basic tasks for each phase
        for phase in phases:
            # Create 3 tasks per phase
            for i in range(3):
                task_data = PlanningTaskCreate(
                    plan_id=plan.id,
                    phase_id=phase.id,
                    milestone_id=None,
                    name=f"{phase.name} Task {i + 1}",
                    description=f"Task {i + 1} for {phase.name} phase",
                    estimated_duration=40,  # 40 hours
                    estimated_effort=40,  # 40 person-hours
                    required_skills={},
                    constraints={},
                    priority=TaskPriority.MEDIUM,
                    status=TaskStatus.PENDING,
                    acceptance_criteria={}
                )
                await self.repository.create_task(task_data.model_dump())
