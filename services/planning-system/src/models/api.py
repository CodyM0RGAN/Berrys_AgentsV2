"""
Planning System Service API models.

This module defines Pydantic models for API requests and responses,
providing validation and serialization for the Planning System service.
"""

from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator, model_validator

# Import shared components
from shared.models.src.base import StandardEntityModel
from shared.models.src.api.responses import (
    create_data_response_model, 
    create_list_response_model,
    ListRequestParams,
    PaginatedResponse
)

# Import shared enums
from shared.models.src.enums import (
    TaskStatus, 
    DependencyType, 
    ResourceType, 
    TaskPriority, 
    ProjectStatus,
    OptimizationTarget
)

# Use ProjectStatus values for now, but this should be replaced with a proper PlanStatus enum
PlanStatus = ProjectStatus

# Pagination
class PaginationParams(ListRequestParams):
    """Parameters for pagination"""
    pass

# Strategic Plan models
class StrategicPlanBase(BaseModel):
    """Base properties for a strategic plan"""
    name: str = Field(..., min_length=1, max_length=200, description="Plan name")
    description: Optional[str] = Field(None, description="Plan description")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Plan constraints")
    objectives: Dict[str, Any] = Field(..., description="Plan objectives")
    status: PlanStatus = Field(PlanStatus.DRAFT, description="Plan status")
    
    # Add validator for status to handle string values
    @validator('status', pre=True)
    def validate_status(cls, v):
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in PlanStatus:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v
    
class StrategicPlanCreate(StrategicPlanBase):
    """Properties to create a strategic plan"""
    project_id: UUID = Field(..., description="Project ID")
    methodology_id: Optional[UUID] = Field(None, description="Planning methodology ID")
    template_id: Optional[UUID] = Field(None, description="Plan template ID")

class StrategicPlanUpdate(BaseModel):
    """Properties to update a strategic plan"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Plan name")
    description: Optional[str] = Field(None, description="Plan description")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Plan constraints")
    objectives: Optional[Dict[str, Any]] = Field(None, description="Plan objectives")
    status: Optional[PlanStatus] = Field(None, description="Plan status")
    methodology_id: Optional[UUID] = Field(None, description="Planning methodology ID")
    template_id: Optional[UUID] = Field(None, description="Plan template ID")
    
    # Add validator for status to handle string values
    @validator('status', pre=True)
    def validate_status(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in PlanStatus:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v

class StrategicPlanResponseData(StandardEntityModel, StrategicPlanBase):
    """Strategic plan response model"""
    project_id: UUID = Field(..., description="Project ID")
    methodology_id: Optional[UUID] = Field(None, description="Planning methodology ID")
    template_id: Optional[UUID] = Field(None, description="Plan template ID")
    phase_count: int = Field(..., description="Number of phases in the plan")
    milestone_count: int = Field(..., description="Number of milestones in the plan")
    task_count: int = Field(..., description="Number of tasks in the plan")
    progress: float = Field(..., ge=0, le=100, description="Overall plan progress percentage")
    methodology_name: Optional[str] = Field(None, description="Planning methodology name")
    template_name: Optional[str] = Field(None, description="Plan template name")

class PlanPhaseBase(BaseModel):
    """Base properties for a plan phase"""
    name: str = Field(..., min_length=1, max_length=200, description="Phase name")
    description: Optional[str] = Field(None, description="Phase description")
    order: int = Field(..., ge=0, description="Phase order")
    start_date: Optional[datetime] = Field(None, description="Phase start date")
    end_date: Optional[datetime] = Field(None, description="Phase end date")
    objectives: Optional[Dict[str, Any]] = Field(None, description="Phase objectives")
    deliverables: Optional[Dict[str, Any]] = Field(None, description="Phase deliverables")
    completion_criteria: Optional[Dict[str, Any]] = Field(None, description="Phase completion criteria")

class PlanPhaseCreate(PlanPhaseBase):
    """Properties to create a plan phase"""
    plan_id: UUID = Field(..., description="Strategic plan ID")

class PlanPhaseUpdate(BaseModel):
    """Properties to update a plan phase"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Phase name")
    description: Optional[str] = Field(None, description="Phase description")
    order: Optional[int] = Field(None, ge=0, description="Phase order")
    start_date: Optional[datetime] = Field(None, description="Phase start date")
    end_date: Optional[datetime] = Field(None, description="Phase end date")
    objectives: Optional[Dict[str, Any]] = Field(None, description="Phase objectives")
    deliverables: Optional[Dict[str, Any]] = Field(None, description="Phase deliverables")
    completion_criteria: Optional[Dict[str, Any]] = Field(None, description="Phase completion criteria")

class PlanPhaseResponseData(StandardEntityModel, PlanPhaseBase):
    """Plan phase response model"""
    plan_id: UUID = Field(..., description="Strategic plan ID")
    task_count: int = Field(..., description="Number of tasks in the phase")
    progress: float = Field(..., ge=0, le=100, description="Phase progress percentage")

class PlanMilestone(BaseModel):
    """Milestone in a strategic plan"""
    name: str = Field(..., min_length=1, max_length=200, description="Milestone name")
    description: Optional[str] = Field(None, description="Milestone description")
    target_date: datetime = Field(..., description="Target completion date")
    actual_date: Optional[datetime] = Field(None, description="Actual completion date")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Priority level")
    criteria: Optional[Dict[str, Any]] = Field(None, description="Completion criteria")
    
    # Add validator for priority to handle string values
    @validator('priority', pre=True)
    def validate_priority(cls, v):
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in TaskPriority:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v
            # If no match, let Pydantic handle the validation error
        return v
    
class PlanMilestoneCreate(PlanMilestone):
    """Properties to create a plan milestone"""
    plan_id: UUID = Field(..., description="Strategic plan ID")

class PlanMilestoneUpdate(BaseModel):
    """Properties to update a plan milestone"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Milestone name")
    description: Optional[str] = Field(None, description="Milestone description")
    target_date: Optional[datetime] = Field(None, description="Target completion date")
    actual_date: Optional[datetime] = Field(None, description="Actual completion date")
    priority: Optional[TaskPriority] = Field(None, description="Priority level")
    criteria: Optional[Dict[str, Any]] = Field(None, description="Completion criteria")
    
    # Add validator for priority to handle string values
    @validator('priority', pre=True)
    def validate_priority(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in TaskPriority:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v

class PlanMilestoneResponseData(StandardEntityModel, PlanMilestone):
    """Plan milestone response model"""
    plan_id: UUID = Field(..., description="Strategic plan ID")
    is_completed: bool = Field(..., description="Whether the milestone is completed")
    
# Planning Task models
class PlanningTaskBase(BaseModel):
    """Base properties for a planning task"""
    name: str = Field(..., min_length=1, max_length=200, description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    estimated_duration: float = Field(..., gt=0, description="Estimated duration in hours")
    estimated_effort: float = Field(..., gt=0, description="Estimated effort in person-hours")
    required_skills: Optional[Dict[str, float]] = Field(None, description="Required skills with proficiency levels")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Task constraints")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Priority level")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Task status")
    acceptance_criteria: Optional[Dict[str, Any]] = Field(None, description="Task acceptance criteria")
    assigned_to: Optional[UUID] = Field(None, description="Assigned resource ID")
    
    # Add validator for priority to handle string values
    @validator('priority', pre=True)
    def validate_priority(cls, v):
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in TaskPriority:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v
    
    # Add validator for status to handle string values
    @validator('status', pre=True)
    def validate_status(cls, v):
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in TaskStatus:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v
    
class PlanningTaskCreate(PlanningTaskBase):
    """Properties to create a planning task"""
    plan_id: UUID = Field(..., description="Strategic plan ID")
    phase_id: Optional[UUID] = Field(None, description="Plan phase ID")
    milestone_id: Optional[UUID] = Field(None, description="Milestone ID")
    
    @model_validator(mode='after')
    def validate_phase_or_milestone(self):
        """Ensure task is associated with either a phase or milestone or both"""
        if not self.phase_id and not self.milestone_id:
            raise ValueError("Task must be associated with either a phase, milestone, or both")
        return self

class PlanningTaskUpdate(BaseModel):
    """Properties to update a planning task"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    estimated_duration: Optional[float] = Field(None, gt=0, description="Estimated duration in hours")
    estimated_effort: Optional[float] = Field(None, gt=0, description="Estimated effort in person-hours")
    required_skills: Optional[Dict[str, float]] = Field(None, description="Required skills with proficiency levels")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Task constraints")
    priority: Optional[TaskPriority] = Field(None, description="Priority level")
    status: Optional[TaskStatus] = Field(None, description="Task status")
    phase_id: Optional[UUID] = Field(None, description="Plan phase ID")
    milestone_id: Optional[UUID] = Field(None, description="Milestone ID")
    acceptance_criteria: Optional[Dict[str, Any]] = Field(None, description="Task acceptance criteria")
    assigned_to: Optional[UUID] = Field(None, description="Assigned resource ID")
    
    # Add validator for priority to handle string values
    @validator('priority', pre=True)
    def validate_priority(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in TaskPriority:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v
    
    # Add validator for status to handle string values
    @validator('status', pre=True)
    def validate_status(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in TaskStatus:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v

class PlanningTaskResponseData(StandardEntityModel, PlanningTaskBase):
    """Planning task response model"""
    plan_id: UUID = Field(..., description="Strategic plan ID")
    phase_id: Optional[UUID] = Field(None, description="Plan phase ID")
    milestone_id: Optional[UUID] = Field(None, description="Milestone ID")
    dependency_count: int = Field(..., description="Number of dependencies")
    dependent_count: int = Field(..., description="Number of tasks dependent on this task")
    is_critical_path: bool = Field(..., description="Whether task is on the critical path")
    earliest_start: Optional[datetime] = Field(None, description="Earliest possible start time")
    earliest_finish: Optional[datetime] = Field(None, description="Earliest possible finish time")
    latest_start: Optional[datetime] = Field(None, description="Latest possible start time")
    latest_finish: Optional[datetime] = Field(None, description="Latest possible finish time")
    slack: Optional[float] = Field(None, description="Slack time in hours")
    phase_name: Optional[str] = Field(None, description="Phase name")
    milestone_name: Optional[str] = Field(None, description="Milestone name")
    assigned_resource_name: Optional[str] = Field(None, description="Assigned resource name")

# Dependency models
class DependencyBase(BaseModel):
    """Base properties for a task dependency"""
    dependency_type: DependencyType = Field(DependencyType.FINISH_TO_START, description="Type of dependency")
    lag: float = Field(0, ge=0, description="Lag time in hours")
    
    # Add validator for dependency_type to handle string values
    @validator('dependency_type', pre=True)
    def validate_dependency_type(cls, v):
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in DependencyType:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v
    
class DependencyCreate(DependencyBase):
    """Properties to create a task dependency"""
    from_task_id: UUID = Field(..., description="Source task ID")
    to_task_id: UUID = Field(..., description="Target task ID")
    
    @validator("to_task_id")
    def validate_different_tasks(cls, v, values):
        """Ensure from_task_id and to_task_id are different"""
        if "from_task_id" in values and v == values["from_task_id"]:
            raise ValueError("Tasks cannot depend on themselves")
        return v

class DependencyUpdate(BaseModel):
    """Properties to update a task dependency"""
    dependency_type: Optional[DependencyType] = Field(None, description="Type of dependency")
    lag: Optional[float] = Field(None, ge=0, description="Lag time in hours")
    
    # Add validator for dependency_type to handle string values
    @validator('dependency_type', pre=True)
    def validate_dependency_type(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in DependencyType:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v

class DependencyResponseData(StandardEntityModel, DependencyBase):
    """Task dependency response model"""
    from_task_id: UUID = Field(..., description="Source task ID")
    to_task_id: UUID = Field(..., description="Target task ID")
    from_task_name: str = Field(..., description="Source task name")
    to_task_name: str = Field(..., description="Target task name")
    critical: bool = Field(..., description="Whether the dependency is on the critical path")

# Resource models
class ResourceBase(BaseModel):
    """Base properties for a resource"""
    name: str = Field(..., min_length=1, max_length=200, description="Resource name")
    resource_type: ResourceType = Field(..., description="Type of resource")
    description: Optional[str] = Field(None, description="Resource description")
    skills: Optional[Dict[str, float]] = Field(None, description="Skills with proficiency levels")
    availability: Optional[Dict[str, Any]] = Field(None, description="Availability information")
    capacity_hours: float = Field(40.0, gt=0, description="Capacity in hours per week")
    cost_rate: Optional[float] = Field(None, ge=0, description="Cost rate per hour")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Resource constraints")
    external_id: Optional[str] = Field(None, description="External system identifier")
    
    # Add validator for resource_type to handle string values
    @validator('resource_type', pre=True)
    def validate_resource_type(cls, v):
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in ResourceType:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v

class ResourceCreate(ResourceBase):
    """Properties to create a resource"""
    pass

class ResourceUpdate(BaseModel):
    """Properties to update a resource"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Resource name")
    resource_type: Optional[ResourceType] = Field(None, description="Type of resource")
    description: Optional[str] = Field(None, description="Resource description")
    skills: Optional[Dict[str, float]] = Field(None, description="Skills with proficiency levels")
    availability: Optional[Dict[str, Any]] = Field(None, description="Availability information")
    capacity_hours: Optional[float] = Field(None, gt=0, description="Capacity in hours per week")
    cost_rate: Optional[float] = Field(None, ge=0, description="Cost rate per hour")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Resource constraints")
    external_id: Optional[str] = Field(None, description="External system identifier")
    
    # Add validator for resource_type to handle string values
    @validator('resource_type', pre=True)
    def validate_resource_type(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in ResourceType:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v

class ResourceResponseData(StandardEntityModel, ResourceBase):
    """Resource response model"""
    allocation_count: int = Field(..., description="Number of allocations")
    utilization_percentage: float = Field(..., ge=0, le=100, description="Current utilization percentage")
    is_overallocated: bool = Field(..., description="Whether the resource is overallocated")

# Resource Allocation models
class ResourceAllocationBase(BaseModel):
    """Base properties for resource allocation"""
    allocation_percentage: float = Field(..., ge=0, le=100, description="Allocation percentage")
    assigned_hours: float = Field(..., ge=0, description="Assigned hours")
    start_date: datetime = Field(..., description="Start date of allocation")
    end_date: datetime = Field(..., description="End date of allocation")
    
    @validator("end_date")
    def validate_dates(cls, v, values):
        """Ensure end_date is after start_date"""
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("End date must be after start date")
        return v
    
class ResourceAllocationCreate(ResourceAllocationBase):
    """Properties to create a resource allocation"""
    task_id: UUID = Field(..., description="Task ID")
    resource_id: UUID = Field(..., description="Resource ID")

class ResourceAllocationUpdate(BaseModel):
    """Properties to update a resource allocation"""
    allocation_percentage: Optional[float] = Field(None, ge=0, le=100, description="Allocation percentage")
    assigned_hours: Optional[float] = Field(None, ge=0, description="Assigned hours")
    start_date: Optional[datetime] = Field(None, description="Start date of allocation")
    end_date: Optional[datetime] = Field(None, description="End date of allocation")
    
    @model_validator(mode='after')
    def validate_dates(self):
        """Ensure end_date is after start_date if both are provided"""
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")
        return self

class ResourceAllocationResponseData(StandardEntityModel, ResourceAllocationBase):
    """Resource allocation response model"""
    task_id: UUID = Field(..., description="Task ID")
    resource_id: UUID = Field(..., description="Resource ID")
    task_name: str = Field(..., description="Task name")
    resource_name: str = Field(..., description="Resource name")
    is_overallocated: bool = Field(..., description="Whether the resource is overallocated")

# Plan Template models
class PlanTemplateBase(BaseModel):
    """Base properties for a plan template"""
    name: str = Field(..., min_length=1, max_length=200, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    version: str = Field(..., min_length=1, max_length=50, description="Template version")
    structure: Dict[str, Any] = Field(..., description="Template structure")
    customization_options: Optional[Dict[str, Any]] = Field(None, description="Customization options")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Template metadata")
    is_active: bool = Field(True, description="Whether the template is active")

class PlanTemplateCreate(PlanTemplateBase):
    """Properties to create a plan template"""
    pass

class PlanTemplateUpdate(BaseModel):
    """Properties to update a plan template"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    version: Optional[str] = Field(None, min_length=1, max_length=50, description="Template version")
    structure: Optional[Dict[str, Any]] = Field(None, description="Template structure")
    customization_options: Optional[Dict[str, Any]] = Field(None, description="Customization options")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Template metadata")
    is_active: Optional[bool] = Field(None, description="Whether the template is active")

class PlanTemplateResponseData(StandardEntityModel, PlanTemplateBase):
    """Plan template response model"""
    phase_count: int = Field(..., description="Number of phases in the template")
    milestone_count: int = Field(..., description="Number of milestones in the template")
    task_count: int = Field(..., description="Number of tasks in the template")
    plan_count: int = Field(..., description="Number of plans using this template")

# Template Phase models
class TemplatePhaseBase(BaseModel):
    """Base properties for a template phase"""
    name: str = Field(..., min_length=1, max_length=200, description="Phase name")
    description: Optional[str] = Field(None, description="Phase description")
    order: int = Field(..., ge=0, description="Phase order")
    duration_estimate: Optional[float] = Field(None, gt=0, description="Estimated duration in days")
    objectives: Optional[Dict[str, Any]] = Field(None, description="Phase objectives")
    deliverables: Optional[Dict[str, Any]] = Field(None, description="Phase deliverables")
    completion_criteria: Optional[Dict[str, Any]] = Field(None, description="Phase completion criteria")

class TemplatePhaseCreate(TemplatePhaseBase):
    """Properties to create a template phase"""
    template_id: UUID = Field(..., description="Plan template ID")

class TemplatePhaseUpdate(BaseModel):
    """Properties to update a template phase"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Phase name")
    description: Optional[str] = Field(None, description="Phase description")
    order: Optional[int] = Field(None, ge=0, description="Phase order")
    duration_estimate: Optional[float] = Field(None, gt=0, description="Estimated duration in days")
    objectives: Optional[Dict[str, Any]] = Field(None, description="Phase objectives")
    deliverables: Optional[Dict[str, Any]] = Field(None, description="Phase deliverables")
    completion_criteria: Optional[Dict[str, Any]] = Field(None, description="Phase completion criteria")

class TemplatePhaseResponseData(StandardEntityModel, TemplatePhaseBase):
    """Template phase response model"""
    template_id: UUID = Field(..., description="Plan template ID")
    task_count: int = Field(..., description="Number of tasks in the phase")

# Template Milestone models
class TemplateMilestoneBase(BaseModel):
    """Base properties for a template milestone"""
    name: str = Field(..., min_length=1, max_length=200, description="Milestone name")
    description: Optional[str] = Field(None, description="Milestone description")
    relative_day: Optional[int] = Field(None, description="Relative day from project start")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Priority level")
    criteria: Optional[Dict[str, Any]] = Field(None, description="Completion criteria")
    
    # Add validator for priority to handle string values
    @validator('priority', pre=True)
    def validate_priority(cls, v):
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in TaskPriority:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v

class TemplateMilestoneCreate(TemplateMilestoneBase):
    """Properties to create a template milestone"""
    template_id: UUID = Field(..., description="Plan template ID")

class TemplateMilestoneUpdate(BaseModel):
    """Properties to update a template milestone"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Milestone name")
    description: Optional[str] = Field(None, description="Milestone description")
    relative_day: Optional[int] = Field(None, description="Relative day from project start")
    priority: Optional[TaskPriority] = Field(None, description="Priority level")
    criteria: Optional[Dict[str, Any]] = Field(None, description="Completion criteria")
    
    # Add validator for priority to handle string values
    @validator('priority', pre=True)
    def validate_priority(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in TaskPriority:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v

class TemplateMilestoneResponseData(StandardEntityModel, TemplateMilestoneBase):
    """Template milestone response model"""
    template_id: UUID = Field(..., description="Plan template ID")
    task_count: int = Field(..., description="Number of tasks associated with the milestone")

# Template Task models
class TemplateTaskBase(BaseModel):
    """Base properties for a template task"""
    name: str = Field(..., min_length=1, max_length=200, description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    estimated_duration: float = Field(..., gt=0, description="Estimated duration in hours")
    estimated_effort: float = Field(..., gt=0, description="Estimated effort in person-hours")
    required_skills: Optional[Dict[str, float]] = Field(None, description="Required skills with proficiency levels")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Priority level")
    acceptance_criteria_template: Optional[Dict[str, Any]] = Field(None, description="Acceptance criteria template")
    
    # Add validator for priority to handle string values
    @validator('priority', pre=True)
    def validate_priority(cls, v):
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in TaskPriority:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v

class TemplateTaskCreate(TemplateTaskBase):
    """Properties to create a template task"""
    template_id: UUID = Field(..., description="Plan template ID")
    phase_id: Optional[UUID] = Field(None, description="Template phase ID")
    milestone_id: Optional[UUID] = Field(None, description="Template milestone ID")

class TemplateTaskUpdate(BaseModel):
    """Properties to update a template task"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    estimated_duration: Optional[float] = Field(None, gt=0, description="Estimated duration in hours")
    estimated_effort: Optional[float] = Field(None, gt=0, description="Estimated effort in person-hours")
    required_skills: Optional[Dict[str, float]] = Field(None, description="Required skills with proficiency levels")
    priority: Optional[TaskPriority] = Field(None, description="Priority level")
    acceptance_criteria_template: Optional[Dict[str, Any]] = Field(None, description="Acceptance criteria template")
    phase_id: Optional[UUID] = Field(None, description="Template phase ID")
    milestone_id: Optional[UUID] = Field(None, description="Template milestone ID")
    
    # Add validator for priority to handle string values
    @validator('priority', pre=True)
    def validate_priority(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in TaskPriority:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v

class TemplateTaskResponseData(StandardEntityModel, TemplateTaskBase):
    """Template task response model"""
    template_id: UUID = Field(..., description="Plan template ID")
    phase_id: Optional[UUID] = Field(None, description="Template phase ID")
    milestone_id: Optional[UUID] = Field(None, description="Template milestone ID")
    dependency_count: int = Field(..., description="Number of dependencies")
    dependent_count: int = Field(..., description="Number of tasks dependent on this task")
    phase_name: Optional[str] = Field(None, description="Phase name")
    milestone_name: Optional[str] = Field(None, description="Milestone name")

# Planning Methodology models
class PlanningMethodologyBase(BaseModel):
    """Base properties for a planning methodology"""
    name: str = Field(..., min_length=1, max_length=200, description="Methodology name")
    description: Optional[str] = Field(None, description="Methodology description")
    methodology_type: str = Field(..., min_length=1, max_length=50, description="Methodology type")
    parameters: Dict[str, Any] = Field(..., description="Methodology parameters")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Methodology constraints")
    is_active: bool = Field(True, description="Whether the methodology is active")

class PlanningMethodologyCreate(PlanningMethodologyBase):
    """Properties to create a planning methodology"""
    pass

class PlanningMethodologyUpdate(BaseModel):
    """Properties to update a planning methodology"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Methodology name")
    description: Optional[str] = Field(None, description="Methodology description")
    methodology_type: Optional[str] = Field(None, min_length=1, max_length=50, description="Methodology type")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Methodology parameters")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Methodology constraints")
    is_active: Optional[bool] = Field(None, description="Whether the methodology is active")

class PlanningMethodologyResponseData(StandardEntityModel, PlanningMethodologyBase):
    """Planning methodology response model"""
    plan_count: int = Field(..., description="Number of plans using this methodology")

# Forecasting models
class TimelinePoint(BaseModel):
    """Point in a timeline forecast"""
    date: datetime = Field(..., description="Forecast date")
    value: float = Field(..., description="Forecast value")
    lower_bound: Optional[float] = Field(None, description="Lower confidence bound")
    upper_bound: Optional[float] = Field(None, description="Upper confidence bound")

class TimelineForecastData(BaseModel):
    """Timeline forecast model"""
    plan_id: UUID = Field(..., description="Strategic plan ID")
    generated_at: datetime = Field(..., description="Generation timestamp")
    confidence_interval: float = Field(..., ge=0, le=1, description="Confidence interval used (0.0-1.0)")
    timeline: List[TimelinePoint] = Field(..., description="Timeline points")
    expected_completion: datetime = Field(..., description="Expected completion date")
    best_case_completion: datetime = Field(..., description="Best case completion date")
    worst_case_completion: datetime = Field(..., description="Worst case completion date")
    
class ForecastRequest(BaseModel):
    """Request to generate a forecast"""
    plan_id: UUID = Field(..., description="Strategic plan ID")
    confidence_interval: Optional[float] = Field(None, ge=0, le=1, description="Confidence interval (0.0-1.0)")
    include_historical: bool = Field(False, description="Include historical data in response")
    time_unit: str = Field("day", description="Time unit for forecast (hour, day, week, month)")

class BottleneckAnalysisData(BaseModel):
    """Bottleneck analysis model"""
    plan_id: UUID = Field(..., description="Strategic plan ID")
    generated_at: datetime = Field(..., description="Generation timestamp")
    bottlenecks: List[Dict[str, Any]] = Field(..., description="Identified bottlenecks")
    recommendations: List[Dict[str, Any]] = Field(..., description="Recommendations to resolve bottlenecks")
    impact_analysis: Dict[str, Any] = Field(..., description="Impact analysis of bottlenecks")

# Optimization models
class OptimizationRequest(BaseModel):
    """Request for resource optimization"""
    plan_id: UUID = Field(..., description="Strategic plan ID")
    optimization_target: OptimizationTarget = Field(OptimizationTarget.PERFORMANCE, description="Optimization target")
    constraints: Dict[str, Any] = Field(..., description="Optimization constraints")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Optimization preferences")
    
    # Add validator for optimization_target to handle string values
    @validator('optimization_target', pre=True)
    def validate_optimization_target(cls, v):
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in OptimizationTarget:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v

class OptimizationResultData(BaseModel):
    """Result of resource optimization"""
    plan_id: UUID = Field(..., description="Strategic plan ID")
    generated_at: datetime = Field(..., description="Generation timestamp")
    optimization_target: OptimizationTarget = Field(..., description="Optimization target used")
    status: str = Field(..., description="Optimization status (optimal, suboptimal, infeasible)")
    task_adjustments: Dict[UUID, Dict[str, Any]] = Field(..., description="Adjustments to tasks")
    resource_assignments: Dict[UUID, List[Dict[str, Any]]] = Field(..., description="Resource assignments")
    metrics: Dict[str, Any] = Field(..., description="Optimization metrics")
    improvements: Dict[str, Any] = Field(..., description="Improvements over original plan")
    
    # Add validator for optimization_target to handle string values
    @validator('optimization_target', pre=True)
    def validate_optimization_target(cls, v):
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in OptimizationTarget:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v

# Create response models using shared templates
StrategicPlanResponse = create_data_response_model(StrategicPlanResponseData)
StrategicPlanListResponse = create_list_response_model(StrategicPlanResponseData)

PlanPhaseResponse = create_data_response_model(PlanPhaseResponseData)
PlanPhaseListResponse = create_list_response_model(PlanPhaseResponseData)

PlanMilestoneResponse = create_data_response_model(PlanMilestoneResponseData)
PlanMilestoneListResponse = create_list_response_model(PlanMilestoneResponseData)

PlanningTaskResponse = create_data_response_model(PlanningTaskResponseData)
PlanningTaskListResponse = create_list_response_model(PlanningTaskResponseData)

DependencyResponse = create_data_response_model(DependencyResponseData)
DependencyListResponse = create_list_response_model(DependencyResponseData)

ResourceResponse = create_data_response_model(ResourceResponseData)
ResourceListResponse = create_list_response_model(ResourceResponseData)

ResourceAllocationResponse = create_data_response_model(ResourceAllocationResponseData)
ResourceAllocationListResponse = create_list_response_model(ResourceAllocationResponseData)

PlanTemplateResponse = create_data_response_model(PlanTemplateResponseData)
PlanTemplateListResponse = create_list_response_model(PlanTemplateResponseData)

TemplatePhaseResponse = create_data_response_model(TemplatePhaseResponseData)
TemplatePhaseListResponse = create_list_response_model(TemplatePhaseResponseData)

TemplateMilestoneResponse = create_data_response_model(TemplateMilestoneResponseData)
TemplateMilestoneListResponse = create_list_response_model(TemplateMilestoneResponseData)

TemplateTaskResponse = create_data_response_model(TemplateTaskResponseData)
TemplateTaskListResponse = create_list_response_model(TemplateTaskResponseData)

PlanningMethodologyResponse = create_data_response_model(PlanningMethodologyResponseData)
PlanningMethodologyListResponse = create_list_response_model(PlanningMethodologyResponseData)

TimelineForecastResponse = create_data_response_model(TimelineForecastData)
BottleneckAnalysisResponse = create_data_response_model(BottleneckAnalysisData)
OptimizationResultResponse = create_data_response_model(OptimizationResultData)

# Aliases for backward compatibility
TimelineForecast = TimelineForecastResponse
BottleneckAnalysis = BottleneckAnalysisResponse
OptimizationResult = OptimizationResultResponse
