"""
Plan Milestone API models.
"""

from .common import *

# Plan Milestone models
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

# Create response models using shared templates
PlanMilestoneResponse = create_data_response_model(PlanMilestoneResponseData)
PlanMilestoneListResponse = create_list_response_model(PlanMilestoneResponseData)
