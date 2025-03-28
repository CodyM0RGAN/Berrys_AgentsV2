"""
Planning Methodology API models.
"""

from .common import *

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

# Create response models using shared templates
PlanningMethodologyResponse = create_data_response_model(PlanningMethodologyResponseData)
PlanningMethodologyListResponse = create_list_response_model(PlanningMethodologyResponseData)
