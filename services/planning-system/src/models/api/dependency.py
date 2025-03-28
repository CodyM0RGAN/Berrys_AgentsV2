"""
Dependency API models.
"""

from .common import *

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

# Create response models using shared templates
DependencyResponse = create_data_response_model(DependencyResponseData)
DependencyListResponse = create_list_response_model(DependencyResponseData)
