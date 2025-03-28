"""
Dependency Type Info API models.
"""

from .common import *

class DependencyTypeInfo(BaseModel):
    """Dependency type information model"""
    type: DependencyType = Field(..., description="Dependency type")
    description: str = Field(..., description="Human-readable description")
    scheduling_rule: str = Field(..., description="Scheduling rule description")
    is_default: bool = Field(False, description="Whether this is the default dependency type")
    allows_negative_lag: bool = Field(False, description="Whether negative lag is allowed")
    visualization_style: str = Field("solid_arrow", description="Visualization style for UI rendering")
