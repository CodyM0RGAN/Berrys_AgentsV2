"""
Agent model for the web dashboard application.

This module defines the Agent model for agent management.
"""

from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from shared.models.src.agent import (
    Agent as SharedAgentModel,
    AgentType,
    AgentStatus,
    AgentSummary,
    AgentWithTools,
    AgentWithPerformance
)

from app.models.base import BaseModel

class Agent(BaseModel):
    """
    Agent model for agent management.
    
    Attributes:
        id: The agent's unique identifier (UUID)
        name: The agent's name
        type: The agent's type (RESEARCHER, PLANNER, DEVELOPER, etc.)
        configuration: The agent's configuration
        prompt_template: The agent's prompt template
        status: The agent's status (CREATED, INITIALIZING, READY, etc.)
        project_id: The ID of the project this agent belongs to
    """
    __tablename__ = 'agent'  # Singular table name per SQLAlchemy guide
    
    # Override id from BaseModel to add docstring
    id = Column(BaseModel.id.type, primary_key=True, default=BaseModel.id.default.arg)
    
    # Agent attributes
    name = Column(String(100), nullable=False, index=True)
    type = Column(String(20), nullable=False, index=True)
    configuration = Column(JSON, nullable=True)
    prompt_template = Column(String(10000), nullable=True)
    status = Column(String(20), nullable=False, default='CREATED', index=True)
    
    # Relationships
    project_id = Column(UUID(as_uuid=True), ForeignKey('project.id'), nullable=False, index=True)
    project = relationship("Project", back_populates="agents")
    
    # Task relationship
    tasks = relationship("Task", back_populates="agent", cascade="all, delete-orphan")
    
    # Tool relationships
    agent_tools = relationship("AgentTool", back_populates="agent")
    tools = relationship("Tool", secondary="agent_tool", viewonly=True)
    
    def __init__(self, name, type, project_id, configuration=None, prompt_template=None, status='CREATED'):
        """
        Initialize a new Agent.
        
        Args:
            name: The agent's name
            type: The agent's type
            project_id: The ID of the project this agent belongs to
            configuration: The agent's configuration (optional)
            prompt_template: The agent's prompt template (optional)
            status: The agent's status (default: 'CREATED')
        """
        self.name = name
        self.type = type
        self.project_id = project_id
        self.configuration = configuration or {}
        self.prompt_template = prompt_template
        self.status = status
    
    def to_api_model(self) -> SharedAgentModel:
        """
        Convert to shared API model.
        
        Returns:
            A SharedAgentModel instance with this agent's data
        """
        return SharedAgentModel(
            id=self.id,
            name=self.name,
            type=AgentType(self.type),
            configuration=self.configuration,
            prompt_template=self.prompt_template,
            status=AgentStatus(self.status),
            project_id=self.project_id,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    def to_summary(self) -> AgentSummary:
        """
        Convert to agent summary model.
        
        Returns:
            An AgentSummary instance with this agent's data
        """
        return AgentSummary(
            id=self.id,
            name=self.name,
            type=AgentType(self.type),
            status=AgentStatus(self.status),
            project_id=self.project_id
        )
    
    def to_tools_model(self) -> AgentWithTools:
        """
        Convert to agent with tools model.
        
        Returns:
            An AgentWithTools instance with this agent's data and tools
        """
        # Convert each tool to a dictionary representation
        tools = []
        for agent_tool in self.agent_tools:
            tool = agent_tool.tool
            tools.append({
                "id": str(tool.id),
                "name": tool.name,
                "capability": tool.capability,
                "source": tool.source,
                "status": tool.status,
                "configuration": agent_tool.configuration
            })
        
        return AgentWithTools(
            id=self.id,
            name=self.name,
            type=AgentType(self.type),
            configuration=self.configuration,
            prompt_template=self.prompt_template,
            status=AgentStatus(self.status),
            project_id=self.project_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            tools=tools
        )
    
    def to_performance_model(self) -> AgentWithPerformance:
        """
        Convert to agent with performance model.
        
        Returns:
            An AgentWithPerformance instance with this agent's data and performance metrics
        """
        # Calculate performance metrics using the Task model
        task_count = len(self.tasks)
        completed_tasks = [task for task in self.tasks if task.status == 'COMPLETED']
        completed_task_count = len(completed_tasks)
        
        # Calculate success rate
        success_rate = 0.0
        if task_count > 0:
            success_rate = (completed_task_count / task_count) * 100.0
        
        # Calculate average completion time
        average_completion_time = None
        if completed_task_count > 0:
            completion_times = []
            for task in completed_tasks:
                if task.completed_at and task.created_at:
                    completion_time = (task.completed_at - task.created_at).total_seconds()
                    completion_times.append(completion_time)
            
            if completion_times:
                average_completion_time = sum(completion_times) / len(completion_times)
        
        # Additional performance metrics
        performance_metrics = {
            'failed_task_count': sum(1 for task in self.tasks if task.status == 'FAILED'),
            'blocked_task_count': sum(1 for task in self.tasks if task.status == 'BLOCKED'),
            'in_progress_task_count': sum(1 for task in self.tasks if task.status == 'IN_PROGRESS')
        }
        
        return AgentWithPerformance(
            id=self.id,
            name=self.name,
            type=AgentType(self.type),
            configuration=self.configuration,
            prompt_template=self.prompt_template,
            status=AgentStatus(self.status),
            project_id=self.project_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            task_count=task_count,
            completed_task_count=completed_task_count,
            success_rate=success_rate,
            average_completion_time=average_completion_time,
            performance_metrics=performance_metrics
        )
    
    @classmethod
    def from_api_model(cls, api_model: SharedAgentModel) -> 'Agent':
        """
        Create from shared API model.
        
        Args:
            api_model: The SharedAgentModel to convert
            
        Returns:
            A new Agent instance
        """
        return cls(
            name=api_model.name,
            type=api_model.type.value if api_model.type else 'CUSTOM',
            project_id=api_model.project_id,
            configuration=api_model.configuration,
            prompt_template=api_model.prompt_template,
            status=api_model.status.value if api_model.status else 'CREATED'
        )
    
    def __repr__(self):
        """
        Get a string representation of the Agent.
        
        Returns:
            A string representation of the Agent
        """
        return f'<Agent {self.name} ({self.type}, {self.status})>'
