"""
Plan Template API models.
"""

from .common import *

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

# Create response models using shared templates
PlanTemplateResponse = create_data_response_model(PlanTemplateResponseData)
PlanTemplateListResponse = create_list_response_model(PlanTemplateResponseData)

TemplatePhaseResponse = create_data_response_model(TemplatePhaseResponseData)
TemplatePhaseListResponse = create_list_response_model(TemplatePhaseResponseData)

TemplateMilestoneResponse = create_data_response_model(TemplateMilestoneResponseData)
TemplateMilestoneListResponse = create_list_response_model(TemplateMilestoneResponseData)

TemplateTaskResponse = create_data_response_model(TemplateTaskResponseData)
TemplateTaskListResponse = create_list_response_model(TemplateTaskResponseData)
