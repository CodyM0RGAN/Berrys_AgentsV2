# Import models for easier access
from .api import (
    ResourceStatus,
    ResourceType,
    UserInfo,
    ResourceBase,
    ResourceCreate,
    ResourceUpdate,
    ResourceInDB,
    Resource,
    ResourceList,
    ErrorResponse,
)

from .internal import (
    ResourceModel,
    # Uncomment when implemented
    # TagModel,
    # resource_tag_association,
    # ChildResourceModel,
)

__all__ = [
    # API models
    "ResourceStatus",
    "ResourceType",
    "UserInfo",
    "ResourceBase",
    "ResourceCreate",
    "ResourceUpdate",
    "ResourceInDB",
    "Resource",
    "ResourceList",
    "ErrorResponse",
    
    # Internal models
    "ResourceModel",
    # "TagModel",
    # "resource_tag_association",
    # "ChildResourceModel",
]
