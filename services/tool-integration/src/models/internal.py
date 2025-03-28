from sqlalchemy import Column, String, ForeignKey, Text, Boolean, Integer, JSON, DateTime
from sqlalchemy.orm import relationship
from shared.models.src.base import StandardModel, enum_column, Base
from shared.models.src.enums import ToolStatus, ToolCategory, ExecutionStatus
from shared.utils.src.database import UUID
from datetime import datetime

class Tool(StandardModel):
    __tablename__ = 'tool'
    
    id = Column(UUID, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    status = enum_column(ToolStatus, default=ToolStatus.ACTIVE)
    category_id = Column(UUID, ForeignKey('tool_category.id'), nullable=False)
    version_number = Column(String(20), nullable=False)
    configuration = Column(JSON, nullable=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    
    category = relationship("ToolCategory", back_populates="tools")
    executions = relationship("ToolExecution", back_populates="tool")
    
    def __repr__(self):
        return f"<Tool(id={self.id}, name='{self.name}', status={self.status})>"

class ToolCategory(StandardModel):
    __tablename__ = 'tool_category'
    
    id = Column(UUID, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    type = enum_column(ToolCategory, default=ToolCategory.UTILITY)
    
    tools = relationship("Tool", back_populates="category")
    
    def __repr__(self):
        return f"<ToolCategory(id={self.id}, name='{self.name}', type={self.type})>"

class ToolExecution(StandardModel):
    __tablename__ = 'tool_execution'
    
    id = Column(UUID, primary_key=True)
    tool_id = Column(UUID, ForeignKey('tool.id'), nullable=False)
    agent_id = Column(UUID, nullable=False)
    project_id = Column(UUID, nullable=False)
    status = enum_column(ExecutionStatus, default=ExecutionStatus.PENDING)
    parameters = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_time = Column(Integer, nullable=True)  # in milliseconds
    
    tool = relationship("Tool", back_populates="executions")
    
    def __repr__(self):
        return f"<ToolExecution(id={self.id}, tool_id={self.tool_id}, status={self.status})>"

class ToolIntegration(StandardModel):
    __tablename__ = 'tool_integration'
    
    id = Column(UUID, primary_key=True)
    tool_id = Column(UUID, ForeignKey('tool.id'), nullable=False)
    agent_id = Column(UUID, nullable=False)
    configuration = Column(JSON, nullable=True)
    permissions = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    integrated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)
    
    def __repr__(self):
        return f"<ToolIntegration(id={self.id}, tool_id={self.tool_id}, agent_id={self.agent_id})>"

class ToolExecutionLog(StandardModel):
    __tablename__ = 'tool_execution_log'
    
    id = Column(UUID, primary_key=True)
    execution_id = Column(UUID, ForeignKey('tool_execution.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    level = Column(String(10), nullable=False, default="INFO")
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<ToolExecutionLog(id={self.id}, execution_id={self.execution_id}, level={self.level})>"

class ToolEvaluation(StandardModel):
    __tablename__ = 'tool_evaluation'
    
    id = Column(UUID, primary_key=True)
    tool_id = Column(UUID, ForeignKey('tool.id'), nullable=False)
    evaluation_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    overall_score = Column(Integer, nullable=False)
    security_evaluation = Column(JSON, nullable=True)
    performance_evaluation = Column(JSON, nullable=True)
    compatibility_evaluation = Column(JSON, nullable=True)
    usability_score = Column(Integer, nullable=True)
    reliability_score = Column(Integer, nullable=True)
    recommendation = Column(String(20), nullable=True)
    context = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<ToolEvaluation(id={self.id}, tool_id={self.tool_id}, overall_score={self.overall_score})>"

class ToolDiscoveryRequest(StandardModel):
    __tablename__ = 'tool_discovery_request'
    
    id = Column(UUID, primary_key=True)
    project_id = Column(UUID, nullable=False)
    requirements = Column(JSON, nullable=False)
    context = Column(JSON, nullable=True)
    initiated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")
    discovered_tool_count = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<ToolDiscoveryRequest(id={self.id}, project_id={self.project_id}, status={self.status})>"

class MCPServerConfig(StandardModel):
    __tablename__ = 'mcp_server_config'
    
    id = Column(UUID, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    command = Column(String(255), nullable=False)
    args = Column(JSON, nullable=True)
    env = Column(JSON, nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    auto_approve = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<MCPServerConfig(id={self.id}, name='{self.name}', enabled={self.enabled})>"

class ApiIntegrationConfig(StandardModel):
    __tablename__ = 'api_integration_config'
    
    id = Column(UUID, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    base_url = Column(String(255), nullable=False)
    auth_type = Column(String(20), nullable=False, default="NONE")
    auth_config = Column(JSON, nullable=True)
    headers = Column(JSON, nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    
    def __repr__(self):
        return f"<ApiIntegrationConfig(id={self.id}, name='{self.name}', enabled={self.enabled})>"
