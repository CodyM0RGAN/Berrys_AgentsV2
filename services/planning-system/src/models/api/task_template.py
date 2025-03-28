"""
Task Template API models.
"""

from .common import *

# Task Template models
class TaskTemplateBase(BaseModel):
    """Base properties for a task template"""
    name: str = Field(..., description="Template name")
    description: str = Field("", description="Template description")
    category: str = Field(..., description="Template category")
    tags: List[str] = Field([], description="Template tags")
    estimated_duration: float = Field(..., gt=0, description="Estimated duration in hours")
    estimated_effort: float = Field(..., gt=0, description="Estimated effort in person-hours")
    required_skills: Dict[str, float] = Field({}, description="Required skills with proficiency level (0.0-1.0)")
    constraints: Dict[str, Any] = Field({}, description="Task constraints")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Task priority")
    acceptance_criteria: List[str] = Field([], description="Acceptance criteria")

class TaskTemplateCreate(TaskTemplateBase):
    """Properties to create a task template"""
    pass

class TaskTemplateUpdate(BaseModel):
    """Properties to update a task template"""
    name: Optional[str] = Field(None, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: Optional[str] = Field(None, description="Template category")
    tags: Optional[List[str]] = Field(None, description="Template tags")
    estimated_duration: Optional[float] = Field(None, gt=0, description="Estimated duration in hours")
    estimated_effort: Optional[float] = Field(None, gt=0, description="Estimated effort in person-hours")
    required_skills: Optional[Dict[str, float]] = Field(None, description="Required skills with proficiency level (0.0-1.0)")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Task constraints")
    priority: Optional[TaskPriority] = Field(None, description="Task priority")
    acceptance_criteria: Optional[List[str]] = Field(None, description="Acceptance criteria")

class TaskTemplateResponseData(StandardEntityModel, TaskTemplateBase):
    """Task template response model"""
    pass

# Create response models using shared templates
TaskTemplateResponse = create_data_response_model(TaskTemplateResponseData)
TaskTemplateListResponse = create_list_response_model(TaskTemplateResponseData)
