"""
Common imports and utilities for API models.
"""

from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator, model_validator

# Import shared components
from shared.models.src.base import StandardEntityModel
from shared.models.src.api.responses import (
    create_data_response_model, 
    create_list_response_model,
    ListRequestParams,
    PaginatedResponse
)

# Import shared enums
from shared.models.src.enums import (
    TaskStatus, 
    DependencyType, 
    ResourceType, 
    TaskPriority, 
    ProjectStatus,
    OptimizationTarget
)

# Use ProjectStatus values for now, but this should be replaced with a proper PlanStatus enum
PlanStatus = ProjectStatus

# Pagination
class PaginationParams(ListRequestParams):
    """Parameters for pagination"""
    pass
