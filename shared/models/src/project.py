from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


class ProjectBase(BaseModel):
    """Base model for Project with common attributes."""
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.DRAFT # Setting the default status to DRAFT to avoid database constraint violations
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ProjectCreate(ProjectBase):
    """Model for creating a new Project."""
    owner_id: Optional[UUID] = None


class ProjectUpdate(BaseModel):
    """Model for updating an existing Project."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class ProjectInDB(ProjectBase):
    """Model for Project as stored in the database."""
    id: UUID = Field(default_factory=uuid4)
    owner_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "protected_namespaces": ()
    }


class Project(ProjectInDB):
    """Complete Project model with all attributes."""
    pass


class ProjectSummary(BaseModel):
    """Simplified Project model for list views."""
    id: UUID
    name: str
    status: ProjectStatus
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "protected_namespaces": ()
    }


class ProjectWithStats(Project):
    """Project model with additional statistics."""
    agent_count: int = 0
    task_count: int = 0
    completed_task_count: int = 0
    progress_percentage: float = 0.0
