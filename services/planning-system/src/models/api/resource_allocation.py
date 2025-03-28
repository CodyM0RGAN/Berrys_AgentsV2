"""
Resource Allocation API models.
"""

from .common import *

# Resource Allocation models
class ResourceAllocationBase(BaseModel):
    """Base properties for resource allocation"""
    allocation_percentage: float = Field(..., ge=0, le=100, description="Allocation percentage")
    assigned_hours: float = Field(..., ge=0, description="Assigned hours")
    start_date: datetime = Field(..., description="Start date of allocation")
    end_date: datetime = Field(..., description="End date of allocation")
    
    @validator("end_date")
    def validate_dates(cls, v, values):
        """Ensure end_date is after start_date"""
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("End date must be after start date")
        return v
    
class ResourceAllocationCreate(ResourceAllocationBase):
    """Properties to create a resource allocation"""
    task_id: UUID = Field(..., description="Task ID")
    resource_id: UUID = Field(..., description="Resource ID")

class ResourceAllocationUpdate(BaseModel):
    """Properties to update a resource allocation"""
    allocation_percentage: Optional[float] = Field(None, ge=0, le=100, description="Allocation percentage")
    assigned_hours: Optional[float] = Field(None, ge=0, description="Assigned hours")
    start_date: Optional[datetime] = Field(None, description="Start date of allocation")
    end_date: Optional[datetime] = Field(None, description="End date of allocation")
    
    @model_validator(mode='after')
    def validate_dates(self):
        """Ensure end_date is after start_date if both are provided"""
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")
        return self

class ResourceAllocationResponseData(StandardEntityModel, ResourceAllocationBase):
    """Resource allocation response model"""
    task_id: UUID = Field(..., description="Task ID")
    resource_id: UUID = Field(..., description="Resource ID")
    task_name: str = Field(..., description="Task name")
    resource_name: str = Field(..., description="Resource name")
    is_overallocated: bool = Field(..., description="Whether the resource is overallocated")

# Create response models using shared templates
ResourceAllocationResponse = create_data_response_model(ResourceAllocationResponseData)
ResourceAllocationListResponse = create_list_response_model(ResourceAllocationResponseData)
