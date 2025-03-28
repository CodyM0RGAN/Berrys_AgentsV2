from sqlalchemy import Column, String, ForeignKey, JSON, Integer, DateTime, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import BaseModel

# Task dependencies table - defined after model class to avoid circular imports
task_dependency = None


class TaskModel(BaseModel):
    """
    SQLAlchemy model for tasks.
    """
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")
    priority = Column(Integer, nullable=False, default=3)  # 1-5, 5 being highest
    
    # Timing
    start_date = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    project = relationship("ProjectModel", back_populates="tasks")
    
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agent.id", ondelete="SET NULL"), nullable=True)
    agent = relationship("AgentModel", back_populates="tasks")
    
    # Task dependencies - using string references to avoid circular imports
    # The actual secondary table is defined after all models
    dependencies = relationship(
        "TaskModel",
        secondary="task_dependency",
        primaryjoin="TaskModel.id == task_dependency.c.dependent_task_id",
        secondaryjoin="TaskModel.id == task_dependency.c.dependency_task_id",
        backref="dependents"
    )
    
    # Result data
    result = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<Task(id={self.id}, name='{self.name}', status='{self.status}', priority={self.priority})>"


# Define the task dependency table after model class to avoid circular imports
# Import Base directly to avoid using BaseModel.metadata which conflicts with SQLAlchemy's reserved name
from ..database import Base

task_dependency = Table(
    'task_dependencies',
    Base.metadata,  # Use Base.metadata instead of BaseModel.metadata
    Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column('dependent_task_id', UUID(as_uuid=True), ForeignKey('task.id', ondelete="CASCADE"), nullable=False),
    Column('dependency_task_id', UUID(as_uuid=True), ForeignKey('task.id', ondelete="CASCADE"), nullable=False),
    Column('dependency_type', String(20), nullable=False, default="FINISH_TO_START"),
)
