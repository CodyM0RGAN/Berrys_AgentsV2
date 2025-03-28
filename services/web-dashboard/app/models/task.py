"""
Task model for the web dashboard application.

This module defines the Task model for task management.
"""

from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, JSON, Integer, DateTime, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from shared.models.src.task import (
    Task as SharedTaskModel,
    TaskStatus,
    TaskPriority,
    TaskSummary,
    TaskWithDependencies,
    TaskWithAgent,
    DependencyType,
    TaskDependency as SharedTaskDependencyModel
)

from app.models.base import BaseModel

# Task dependency association table
task_dependency = Table(
    'task_dependency',
    BaseModel.metadata,
    Column('dependent_task_id', UUID(as_uuid=True), ForeignKey('task.id'), primary_key=True),
    Column('dependency_task_id', UUID(as_uuid=True), ForeignKey('task.id'), primary_key=True),
    Column('dependency_type', String(20), nullable=False, default='FINISH_TO_START')
)

class Task(BaseModel):
    """
    Task model for task management.
    
    Attributes:
        id: The task's unique identifier (UUID)
        name: The task's name
        description: The task's description
        status: The task's status (PENDING, SCHEDULED, IN_PROGRESS, etc.)
        priority: The task's priority (1-5)
        start_date: When the task is scheduled to start
        due_date: When the task is due
        result: The task's result data
        completed_at: When the task was completed
        project_id: The ID of the project this task belongs to
        agent_id: The ID of the agent assigned to this task
    """
    __tablename__ = 'task'  # Singular table name per SQLAlchemy guide
    
    # Override id from BaseModel to add docstring
    id = Column(BaseModel.id.type, primary_key=True, default=BaseModel.id.default.arg)
    
    # Task attributes
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    status = Column(String(20), nullable=False, default='PENDING', index=True)
    priority = Column(Integer, nullable=False, default=3, index=True)
    start_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    project_id = Column(UUID(as_uuid=True), ForeignKey('project.id'), nullable=False, index=True)
    project = relationship("Project", back_populates="tasks")
    
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agent.id'), nullable=True, index=True)
    agent = relationship("Agent", back_populates="tasks")
    
    # Self-referential relationship for task dependencies
    dependencies = relationship(
        "Task",
        secondary=task_dependency,
        primaryjoin="Task.id == task_dependency.c.dependent_task_id",
        secondaryjoin="Task.id == task_dependency.c.dependency_task_id",
        backref="dependents"
    )
    
    def __init__(self, name, project_id, description=None, status='PENDING', priority=3,
                 start_date=None, due_date=None, agent_id=None, result=None):
        """
        Initialize a new Task.
        
        Args:
            name: The task's name
            project_id: The ID of the project this task belongs to
            description: The task's description (optional)
            status: The task's status (default: 'PENDING')
            priority: The task's priority (default: 3)
            start_date: When the task is scheduled to start (optional)
            due_date: When the task is due (optional)
            agent_id: The ID of the agent assigned to this task (optional)
            result: The task's result data (optional)
        """
        self.name = name
        self.project_id = project_id
        self.description = description
        self.status = status
        self.priority = priority
        self.start_date = start_date
        self.due_date = due_date
        self.agent_id = agent_id
        self.result = result or {}
        
        # Set completed_at if status is COMPLETED
        if status == 'COMPLETED':
            self.completed_at = datetime.utcnow()
    
    def to_api_model(self) -> SharedTaskModel:
        """
        Convert to shared API model.
        
        Returns:
            A SharedTaskModel instance with this task's data
        """
        return SharedTaskModel(
            id=self.id,
            name=self.name,
            description=self.description,
            status=TaskStatus(self.status),
            priority=TaskPriority(self.priority),
            start_date=self.start_date,
            due_date=self.due_date,
            result=self.result,
            completed_at=self.completed_at,
            project_id=self.project_id,
            agent_id=self.agent_id,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    def to_summary(self) -> TaskSummary:
        """
        Convert to task summary model.
        
        Returns:
            A TaskSummary instance with this task's data
        """
        return TaskSummary(
            id=self.id,
            name=self.name,
            status=TaskStatus(self.status),
            priority=TaskPriority(self.priority),
            agent_id=self.agent_id,
            due_date=self.due_date
        )
    
    def to_dependencies_model(self) -> TaskWithDependencies:
        """
        Convert to task with dependencies model.
        
        Returns:
            A TaskWithDependencies instance with this task's data and dependencies
        """
        # Get dependency information from the association table
        dependencies = []
        for dependency in self.dependencies:
            # Get dependency type from the association table
            # In a real implementation, we would query the association table
            # For now, we'll use the default value
            dependency_type = DependencyType.FINISH_TO_START
            
            dependencies.append(SharedTaskDependencyModel(
                dependent_task_id=self.id,
                dependency_task_id=dependency.id,
                dependency_type=dependency_type
            ))
        
        dependents = []
        for dependent in self.dependents:
            # Get dependency type from the association table
            # In a real implementation, we would query the association table
            # For now, we'll use the default value
            dependency_type = DependencyType.FINISH_TO_START
            
            dependents.append(SharedTaskDependencyModel(
                dependent_task_id=dependent.id,
                dependency_task_id=self.id,
                dependency_type=dependency_type
            ))
        
        return TaskWithDependencies(
            id=self.id,
            name=self.name,
            description=self.description,
            status=TaskStatus(self.status),
            priority=TaskPriority(self.priority),
            start_date=self.start_date,
            due_date=self.due_date,
            result=self.result,
            completed_at=self.completed_at,
            project_id=self.project_id,
            agent_id=self.agent_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            dependencies=dependencies,
            dependents=dependents
        )
    
    def to_agent_model(self) -> TaskWithAgent:
        """
        Convert to task with agent model.
        
        Returns:
            A TaskWithAgent instance with this task's data and agent details
        """
        agent_name = None
        agent_type = None
        
        if self.agent:
            agent_name = self.agent.name
            agent_type = self.agent.type
        
        return TaskWithAgent(
            id=self.id,
            name=self.name,
            description=self.description,
            status=TaskStatus(self.status),
            priority=TaskPriority(self.priority),
            start_date=self.start_date,
            due_date=self.due_date,
            result=self.result,
            completed_at=self.completed_at,
            project_id=self.project_id,
            agent_id=self.agent_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            agent_name=agent_name,
            agent_type=agent_type
        )
    
    @classmethod
    def from_api_model(cls, api_model: SharedTaskModel) -> 'Task':
        """
        Create from shared API model.
        
        Args:
            api_model: The SharedTaskModel to convert
            
        Returns:
            A new Task instance
        """
        return cls(
            name=api_model.name,
            project_id=api_model.project_id,
            description=api_model.description,
            status=api_model.status.value if api_model.status else 'PENDING',
            priority=api_model.priority.value if api_model.priority else 3,
            start_date=api_model.start_date,
            due_date=api_model.due_date,
            agent_id=api_model.agent_id,
            result=api_model.result
        )
    
    def __repr__(self):
        """
        Get a string representation of the Task.
        
        Returns:
            A string representation of the Task
        """
        return f'<Task {self.name} ({self.status}, priority: {self.priority})>'
