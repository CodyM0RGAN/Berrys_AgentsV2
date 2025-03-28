"""
Plan Phase API models.
"""

from .common import *

# Plan Phase models
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

# Create response models using shared templates
PlanPhaseResponse = create_data_response_model(PlanPhaseResponseData)
PlanPhaseListResponse = create_list_response_model(PlanPhaseResponseData)
