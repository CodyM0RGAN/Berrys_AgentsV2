"""
Strategic Plan API models.
"""

from .common import *

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

# Create response models using shared templates
StrategicPlanResponse = create_data_response_model(StrategicPlanResponseData)
StrategicPlanListResponse = create_list_response_model(StrategicPlanResponseData)
