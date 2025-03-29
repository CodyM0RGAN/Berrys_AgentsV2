from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator, root_validator


class ResourceStatus(str, Enum):
    """
    Enum for resource status.
    """
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class ResourceType(str, Enum):
    """
    Enum for resource type.
    """
    TYPE_A = "TYPE_A"
    TYPE_B = "TYPE_B"
    TYPE_C = "TYPE_C"


class UserInfo(BaseModel):
    """
    User information model.
    """
    id: str
    username: str
    email: Optional[str] = None
    is_admin: bool = False
    roles: List[str] = Field(default_factory=list)


class ResourceBase(BaseModel):
    """
    Base model for Resource with common attributes.
    """
    name: str
    description: Optional[str] = None
    type: ResourceType
    status: ResourceStatus = ResourceStatus.DRAFT
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('name must not be empty')
        return v.strip()


class ResourceCreate(ResourceBase):
    """
    Model for creating a new Resource.
    """
    owner_id: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Example Resource",
                "description": "This is an example resource",
                "type": "TYPE_A",
                "metadata": {
                    "key1": "value1",
                    "key2": "value2"
                }
            }
        }


class ResourceUpdate(BaseModel):
    """
    Model for updating an existing Resource.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[ResourceType] = None
    status: Optional[ResourceStatus] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('name must not be empty')
        return v.strip() if v is not None else v
    
    @root_validator
    def check_at_least_one_field(cls, values):
        if not any(values.values()):
            raise ValueError('at least one field must be provided')
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Resource",
                "status": "ACTIVE"
            }
        }


class ResourceInDB(ResourceBase):
    """
    Model for Resource as stored in the database.
    """
    id: UUID = Field(default_factory=uuid4)
    owner_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class Resource(ResourceInDB):
    """
    Complete Resource model with all attributes.
    """
    pass


class ResourceList(BaseModel):
    """
    Model for a list of resources with pagination.
    """
    items: List[Resource]
    total: int
    page: int
    page_size: int
    
    @property
    def pages(self) -> int:
        """
        Calculate total number of pages.
        
        Returns:
            int: Total number of pages
        """
        return (self.total + self.page_size - 1) // self.page_size


class ErrorResponse(BaseModel):
    """
    Model for error responses.
    """
    detail: str
    code: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "Resource not found",
                "code": "resource_not_found"
            }
        }
