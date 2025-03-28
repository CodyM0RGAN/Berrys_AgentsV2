"""
Planning Task API models.
"""

from .common import *

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

# Create response models using shared templates
PlanningTaskResponse = create_data_response_model(PlanningTaskResponseData)
PlanningTaskListResponse = create_list_response_model(PlanningTaskResponseData)
