"""
Resource API models.
"""

from .common import *

# Resource models
class ResourceBase(BaseModel):
    """Base properties for a resource"""
    name: str = Field(..., min_length=1, max_length=200, description="Resource name")
    resource_type: ResourceType = Field(..., description="Type of resource")
    description: Optional[str] = Field(None, description="Resource description")
    skills: Optional[Dict[str, float]] = Field(None, description="Skills with proficiency levels")
    availability: Optional[Dict[str, Any]] = Field(None, description="Availability information")
    capacity_hours: float = Field(40.0, gt=0, description="Capacity in hours per week")
    cost_rate: Optional[float] = Field(None, ge=0, description="Cost rate per hour")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Resource constraints")
    external_id: Optional[str] = Field(None, description="External system identifier")
    
    # Add validator for resource_type to handle string values
    @validator('resource_type', pre=True)
    def validate_resource_type(cls, v):
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in ResourceType:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v

class ResourceCreate(ResourceBase):
    """Properties to create a resource"""
    pass

class ResourceUpdate(BaseModel):
    """Properties to update a resource"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Resource name")
    resource_type: Optional[ResourceType] = Field(None, description="Type of resource")
    description: Optional[str] = Field(None, description="Resource description")
    skills: Optional[Dict[str, float]] = Field(None, description="Skills with proficiency levels")
    availability: Optional[Dict[str, Any]] = Field(None, description="Availability information")
    capacity_hours: Optional[float] = Field(None, gt=0, description="Capacity in hours per week")
    cost_rate: Optional[float] = Field(None, ge=0, description="Cost rate per hour")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Resource constraints")
    external_id: Optional[str] = Field(None, description="External system identifier")
    
    # Add validator for resource_type to handle string values
    @validator('resource_type', pre=True)
    def validate_resource_type(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in ResourceType:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v

class ResourceResponseData(StandardEntityModel, ResourceBase):
    """Resource response model"""
    allocation_count: int = Field(..., description="Number of allocations")
    utilization_percentage: float = Field(..., ge=0, le=100, description="Current utilization percentage")
    is_overallocated: bool = Field(..., description="Whether the resource is overallocated")

# Create response models using shared templates
ResourceResponse = create_data_response_model(ResourceResponseData)
ResourceListResponse = create_list_response_model(ResourceResponseData)
