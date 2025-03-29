from sqlalchemy import Column, String, ForeignKey, JSON, DateTime, Table, Text, Boolean, Integer, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import List, Optional, Dict, Any

from shared.models.src.base import StandardModel, enum_column
from shared.models.src.enums import AgentStatus, AgentType
from shared.utils.src.database import UUID, generate_uuid

# Import service-specific enums
from .enums import ExecutionState, AgentStateDetail


class AgentModel(StandardModel):
    """
    SQLAlchemy model for agents.
    """
    __tablename__ = "agent"  # Changed to singular
    
    # Basic information
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    type = enum_column(AgentType, nullable=False)
    status = enum_column(AgentStatus, nullable=False, default=AgentStatus.INACTIVE)
    state_detail = Column(String(20), nullable=True)  # Added for detailed state
    
    # Project association
    project_id = Column(UUID, nullable=False, index=True)
    
    # Template association (optional)
    template_id = Column(String, nullable=True)
    
    # Configuration and prompt
    configuration = Column(JSON, nullable=True)
    prompt_template = Column(Text, nullable=True)
    
    # Additional timestamps (created_at and updated_at are inherited from StandardModel)
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    state_history = relationship("AgentStateModel", back_populates="agent", cascade="all, delete-orphan")
    communications_sent = relationship(
        "AgentCommunicationModel", 
        foreign_keys="AgentCommunicationModel.from_agent_id",
        back_populates="from_agent",
        cascade="all, delete-orphan"
    )
    communications_received = relationship(
        "AgentCommunicationModel", 
        foreign_keys="AgentCommunicationModel.to_agent_id",
        back_populates="to_agent",
        cascade="all, delete-orphan"
    )
    executions = relationship("AgentExecutionModel", back_populates="agent", cascade="all, delete-orphan")
    
    # Enum validation
    __enum_columns__ = {
        'type': AgentType,
        'status': AgentStatus,
        'state_detail': AgentStateDetail
    }
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}', type='{self.type}', status='{self.status}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "status": self.status,
            "state_detail": self.state_detail,
            "project_id": str(self.project_id),
            "template_id": self.template_id,
            "configuration": self.configuration or {},
            "prompt_template": self.prompt_template,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
        }


class AgentTemplateModel(StandardModel):
    """
    SQLAlchemy model for agent templates.
    """
    __tablename__ = "agent_template_legacy"  # Renamed to avoid conflict with AgentTemplateEngineModel
    
    # Primary key (string ID for easier reference)
    id = Column(String(50), primary_key=True)
    
    # Basic information
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    agent_type = enum_column(AgentType, nullable=False)
    
    # Configuration schema and defaults
    configuration_schema = Column(JSON, nullable=False, default={})
    default_configuration = Column(JSON, nullable=False, default={})
    prompt_template = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<AgentTemplate(id='{self.id}', name='{self.name}', agent_type='{self.agent_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type,
            "configuration_schema": self.configuration_schema or {},
            "default_configuration": self.default_configuration or {},
            "prompt_template": self.prompt_template,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AgentStateModel(StandardModel):
    """
    SQLAlchemy model for agent state history.
    """
    __tablename__ = "agent_state_history"
    
    # Agent association
    agent_id = Column(UUID, ForeignKey("agent.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # State information
    previous_status = enum_column(AgentStatus, nullable=True)
    new_status = enum_column(AgentStatus, nullable=False)
    previous_state_detail = Column(String(20), nullable=True)
    new_state_detail = Column(String(20), nullable=True)
    reason = Column(String, nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    agent = relationship("AgentModel", back_populates="state_history")
    
    def __repr__(self):
        return f"<AgentState(agent_id={self.agent_id}, previous_status='{self.previous_status}', new_status='{self.new_status}')>"


class AgentCommunicationModel(StandardModel):
    """
    SQLAlchemy model for agent communications.
    """
    __tablename__ = "agent_communication"  # Changed to singular
    
    # Agent associations
    from_agent_id = Column(UUID, ForeignKey("agent.id", ondelete="CASCADE"), nullable=False, index=True)
    to_agent_id = Column(UUID, ForeignKey("agent.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Communication information
    type = Column(String(50), nullable=False)
    content = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False, default="sent")
    
    # Additional timestamps (created_at is inherited from StandardModel)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    from_agent = relationship("AgentModel", foreign_keys=[from_agent_id], back_populates="communications_sent")
    to_agent = relationship("AgentModel", foreign_keys=[to_agent_id], back_populates="communications_received")
    
    def __repr__(self):
        return f"<AgentCommunication(id={self.id}, from='{self.from_agent_id}', to='{self.to_agent_id}', type='{self.type}')>"


class AgentCheckpointModel(StandardModel):
    """
    SQLAlchemy model for agent state checkpoints.
    """
    __tablename__ = "agent_checkpoint"  # Changed to singular
    
    # Agent association
    agent_id = Column(UUID, ForeignKey("agent.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    
    # Checkpoint information
    state_data = Column(JSON, nullable=False)
    sequence_number = Column(Integer, nullable=False, default=0)
    is_recoverable = Column(Boolean, nullable=False, default=True)
    
    def __repr__(self):
        return f"<AgentCheckpoint(agent_id={self.agent_id}, sequence={self.sequence_number})>"


class AgentExecutionModel(StandardModel):
    """
    SQLAlchemy model for agent executions.
    """
    __tablename__ = "agent_execution"  # Changed to singular
    
    # Agent and task associations
    agent_id = Column(UUID, ForeignKey("agent.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(UUID, nullable=False, index=True)
    
    # Execution information
    state = enum_column(ExecutionState, nullable=False, default=ExecutionState.QUEUED)
    parameters = Column(JSON, nullable=True)
    context = Column(JSON, nullable=True)
    progress_percentage = Column(Float, nullable=False, default=0.0)
    status_message = Column(String, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    
    # Additional timestamps (created_at and updated_at are inherited from StandardModel)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    agent = relationship("AgentModel", back_populates="executions")
    state_history = relationship("ExecutionStateModel", back_populates="execution", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AgentExecution(id={self.id}, agent_id={self.agent_id}, task_id={self.task_id}, state='{self.state}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "task_id": str(self.task_id),
            "state": self.state,
            "progress_percentage": self.progress_percentage,
            "status_message": self.status_message,
            "parameters": self.parameters,
            "context": self.context,
            "result": self.result,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ExecutionStateModel(StandardModel):
    """
    SQLAlchemy model for execution state history.
    """
    __tablename__ = "execution_state_history"
    
    # Execution association
    execution_id = Column(UUID, ForeignKey("agent_execution.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # State information
    previous_state = enum_column(ExecutionState, nullable=True)
    new_state = enum_column(ExecutionState, nullable=False)
    reason = Column(String, nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    execution = relationship("AgentExecutionModel", back_populates="state_history")
    
    def __repr__(self):
        return f"<ExecutionState(execution_id={self.execution_id}, previous='{self.previous_state}', new='{self.new_state}')>"


class HumanInteractionModel(StandardModel):
    """
    SQLAlchemy model for human interactions.
    """
    __tablename__ = "human_interaction"  # Changed to singular
    
    # Agent and execution associations
    agent_id = Column(UUID, ForeignKey("agent.id", ondelete="CASCADE"), nullable=False, index=True)
    execution_id = Column(UUID, ForeignKey("agent_execution.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Interaction information
    type = Column(String(50), nullable=False, index=True)  # approval_request, feedback, notification
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, completed, delivered, etc.
    content = Column(JSON, nullable=False)  # Depends on interaction type
    response = Column(JSON, nullable=True)  # Optional response data
    interaction_metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Additional timestamps (created_at and updated_at are inherited from StandardModel)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    agent = relationship("AgentModel", foreign_keys=[agent_id])
    execution = relationship("AgentExecutionModel", foreign_keys=[execution_id])
    
    def __repr__(self):
        return f"<HumanInteraction(id={self.id}, agent_id={self.agent_id}, type='{self.type}', status='{self.status}')>"
