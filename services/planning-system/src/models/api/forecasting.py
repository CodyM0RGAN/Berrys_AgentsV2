"""
Forecasting API models.
"""

from .common import *

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

# Create response models using shared templates
TimelineForecastResponse = create_data_response_model(TimelineForecastData)
BottleneckAnalysisResponse = create_data_response_model(BottleneckAnalysisData)

# Aliases for backward compatibility
TimelineForecast = TimelineForecastResponse
BottleneckAnalysis = BottleneckAnalysisResponse
