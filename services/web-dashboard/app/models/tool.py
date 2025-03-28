"""
Tool model for the web dashboard application.

This module defines the Tool model for tool management.
"""

from sqlalchemy import Column, String, ForeignKey, JSON, Table, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from shared.models.src.tool import (
    Tool as SharedToolModel,
    ToolSource,
    ToolStatus,
    IntegrationType,
    ToolSummary
)

from app.models.base import BaseModel

# Agent-Tool association class
class AgentTool(BaseModel):
    """
    Junction table for Agent-Tool relationship.
    
    Attributes:
        agent_id: The ID of the agent
        tool_id: The ID of the tool
        configuration: Tool configuration specific to the agent
    """
    __tablename__ = 'agent_tool'
    
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agent.id'), primary_key=True)
    tool_id = Column(UUID(as_uuid=True), ForeignKey('tool.id'), primary_key=True)
    configuration = Column(JSON, nullable=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="agent_tools")
    tool = relationship("Tool", back_populates="agent_tools")
    
    def __init__(self, agent_id, tool_id, configuration=None):
        """
        Initialize a new AgentTool.
        
        Args:
            agent_id: The ID of the agent
            tool_id: The ID of the tool
            configuration: Tool configuration specific to the agent (optional)
        """
        self.agent_id = agent_id
        self.tool_id = tool_id
        self.configuration = configuration or {}

class Tool(BaseModel):
    """
    Tool model for tool management.
    
    Attributes:
        id: The tool's unique identifier (UUID)
        name: The tool's name
        version: The tool's version
        schema: JSON schema defining the tool's interface
        source: Where the tool came from (BUILT_IN, DISCOVERED, etc.)
        registered_at: When the tool was registered
        tool_metadata: Additional tool metadata (renamed from 'metadata' to avoid SQLAlchemy conflicts)
        status: The tool's status (DISCOVERED, APPROVED, etc.)
    """
    __tablename__ = 'tool'  # Singular table name per SQLAlchemy guide
    
    # Override id from BaseModel to add docstring
    id = Column(BaseModel.id.type, primary_key=True, default=BaseModel.id.default.arg)
    
    # Tool attributes
    name = Column(String(100), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    tool_schema = Column(JSON, nullable=True)
    source = Column(String(20), nullable=False, index=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    tool_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' which is reserved in SQLAlchemy
    status = Column(String(20), nullable=False, default='DISCOVERED', index=True)
    capability = Column(String(100), nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    documentation_url = Column(String(500), nullable=True)
    integration_type = Column(String(20), nullable=True)
    
    # Relationships
    agent_tools = relationship("AgentTool", back_populates="tool")
    agents = relationship("Agent", secondary="agent_tool", viewonly=True)
    
    def __init__(self, name, version, capability, source, tool_schema=None, metadata=None, 
                 status='DISCOVERED', description=None, documentation_url=None, integration_type=None):
        """
        Initialize a new Tool.
        
        Args:
            name: The tool's name
            version: The tool's version
            capability: The tool's capability
            source: The tool's source
            tool_schema: JSON schema defining the tool's interface (optional)
            metadata: Additional tool metadata (optional, stored in tool_metadata field)
            status: The tool's status (default: 'DISCOVERED')
            description: The tool's description (optional)
            documentation_url: URL to the tool's documentation (optional)
            integration_type: The tool's integration type (optional)
        """
        self.name = name
        self.version = version
        self.capability = capability
        self.source = source
        self.tool_schema = tool_schema or {}
        self.tool_metadata = metadata or {}  # Assign to tool_metadata field
        self.status = status
        self.description = description
        self.documentation_url = documentation_url
        self.integration_type = integration_type
        self.registered_at = datetime.utcnow()
    
    def to_api_model(self) -> SharedToolModel:
        """
        Convert to shared API model.
        
        Returns:
            A SharedToolModel instance with this tool's data
        """
        return SharedToolModel(
            id=self.id,
            name=self.name,
            description=self.description,
            capability=self.capability,
            source=ToolSource(self.source),
            documentation_url=self.documentation_url,
            tool_schema=self.tool_schema,
            metadata=self.tool_metadata,  # Map to 'metadata' in API for backward compatibility
            integration_type=IntegrationType(self.integration_type) if self.integration_type else None,
            status=ToolStatus(self.status),
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    def to_summary(self) -> ToolSummary:
        """
        Convert to tool summary model.
        
        Returns:
            A ToolSummary instance with this tool's data
        """
        return ToolSummary(
            id=self.id,
            name=self.name,
            capability=self.capability,
            source=ToolSource(self.source),
            status=ToolStatus(self.status)
        )
    
    @classmethod
    def from_api_model(cls, api_model: SharedToolModel) -> 'Tool':
        """
        Create from shared API model.
        
        Args:
            api_model: The SharedToolModel to convert
            
        Returns:
            A new Tool instance
        """
        return cls(
            name=api_model.name,
            version="1.0",  # Default version if not provided
            capability=api_model.capability,
            source=api_model.source.value if api_model.source else 'CUSTOM',
            tool_schema=api_model.tool_schema,
            metadata=api_model.metadata,  # Pass metadata to constructor
            status=api_model.status.value if api_model.status else 'DISCOVERED',
            description=api_model.description,
            documentation_url=api_model.documentation_url,
            integration_type=api_model.integration_type.value if api_model.integration_type else None
        )
    
    def __repr__(self):
        """
        Get a string representation of the Tool.
        
        Returns:
            A string representation of the Tool
        """
        return f'<Tool {self.name} ({self.capability}, {self.status})>'
