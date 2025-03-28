from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskPriority(int, Enum):
    LOWEST = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    HIGHEST = 5


class DependencyType(str, Enum):
    FINISH_TO_START = "FINISH_TO_START"  # Task can start only when dependency is finished
    START_TO_START = "START_TO_START"    # Task can start only when dependency has started
    FINISH_TO_FINISH = "FINISH_TO_FINISH"  # Task can finish only when dependency is finished
    START_TO_FINISH = "START_TO_FINISH"  # Task can finish only when dependency has started


class TaskBase(BaseModel):
    """Base model for Task with common attributes."""
    name: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    """Model for creating a new Task."""
    project_id: UUID
    agent_id: Optional[UUID] = None


class TaskUpdate(BaseModel):
    """Model for updating an existing Task."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    agent_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None


class TaskDependency(BaseModel):
    """Model for task dependencies."""
    dependent_task_id: UUID
    dependency_task_id: UUID
    dependency_type: DependencyType = DependencyType.FINISH_TO_START


class TaskInDB(TaskBase):
    """Model for Task as stored in the database."""
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    agent_id: Optional[UUID] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Task(TaskInDB):
    """Complete Task model with all attributes."""
    pass


class TaskSummary(BaseModel):
    """Simplified Task model for list views."""
    id: UUID
    name: str
    status: TaskStatus
    priority: TaskPriority
    agent_id: Optional[UUID] = None
    due_date: Optional[datetime] = None

    class Config:
        orm_mode = True


class TaskWithDependencies(Task):
    """Task model with dependencies."""
    dependencies: List[TaskDependency] = Field(default_factory=list)
    dependents: List[TaskDependency] = Field(default_factory=list)


class TaskWithAgent(Task):
    """Task model with agent details."""
    agent_name: Optional[str] = None
    agent_type: Optional[str] = None
