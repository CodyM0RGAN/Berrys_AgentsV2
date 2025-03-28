"""
Optimization API models.
"""

from .common import *

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
OptimizationResultResponse = create_data_response_model(OptimizationResultData)

# Aliases for backward compatibility
OptimizationResult = OptimizationResultResponse
