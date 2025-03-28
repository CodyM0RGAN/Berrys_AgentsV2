"""
What-If Analysis API models.
"""

from .common import *
from .forecasting import TimelineForecast

# What-If Scenario models
class WhatIfScenarioBase(BaseModel):
    """Base properties for a what-if scenario"""
    name: str = Field(..., description="Scenario name")
    description: str = Field("", description="Scenario description")
    task_modifications: List[Dict[str, Any]] = Field([], description="Task modifications")
    resource_modifications: List[Dict[str, Any]] = Field([], description="Resource modifications")
    dependency_modifications: List[Dict[str, Any]] = Field([], description="Dependency modifications")

class WhatIfScenarioCreate(WhatIfScenarioBase):
    """Properties to create a what-if scenario"""
    plan_id: UUID = Field(..., description="Strategic plan ID")

class WhatIfScenarioUpdate(BaseModel):
    """Properties to update a what-if scenario"""
    name: Optional[str] = Field(None, description="Scenario name")
    description: Optional[str] = Field(None, description="Scenario description")
    task_modifications: Optional[List[Dict[str, Any]]] = Field(None, description="Task modifications")
    resource_modifications: Optional[List[Dict[str, Any]]] = Field(None, description="Resource modifications")
    dependency_modifications: Optional[List[Dict[str, Any]]] = Field(None, description="Dependency modifications")

class WhatIfScenarioResponseData(StandardEntityModel, WhatIfScenarioBase):
    """What-if scenario response model"""
    plan_id: UUID = Field(..., description="Strategic plan ID")
    last_analyzed_at: Optional[datetime] = Field(None, description="Last analysis timestamp")
    has_analysis_results: bool = Field(False, description="Whether analysis results exist")

class WhatIfAnalysisResult(BaseModel):
    """What-if analysis result model"""
    scenario_id: UUID = Field(..., description="Scenario ID")
    plan_id: UUID = Field(..., description="Strategic plan ID")
    generated_at: datetime = Field(..., description="Generation timestamp")
    baseline_forecast: TimelineForecast = Field(..., description="Baseline forecast")
    scenario_forecast: TimelineForecast = Field(..., description="Scenario forecast")
    comparison: Dict[str, Any] = Field(..., description="Comparison between forecasts")
    scenario_name: str = Field(..., description="Scenario name")
    scenario_description: str = Field("", description="Scenario description")

# Create response models using shared templates
WhatIfScenarioResponse = create_data_response_model(WhatIfScenarioResponseData)
WhatIfScenarioListResponse = create_list_response_model(WhatIfScenarioResponseData)
WhatIfAnalysisResultResponse = create_data_response_model(WhatIfAnalysisResult)
