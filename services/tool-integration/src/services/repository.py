"""
Tool Integration Repository module.

This module defines the repository layer for interacting with the database,
providing data access operations for tools, integrations, and executions.
"""

import logging
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import true, false

from ..models.internal import (
    Tool as ToolModel,
    ToolIntegration as ToolIntegrationModel,
    ToolExecution as ToolExecutionModel,
    ToolExecutionLog as ToolExecutionLogModel,
    ToolEvaluation as ToolEvaluationModel,
    ToolDiscoveryRequest as ToolDiscoveryRequestModel,
    MCPServerConfig as MCPServerConfigModel,
    ApiIntegrationConfig as ApiIntegrationConfigModel,
    Base
)
from shared.models.src.tool import ToolStatus, ToolSource, IntegrationType

logger = logging.getLogger(__name__)

class ToolRepository:
    """Repository for tool data access operations."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize with database session.
        
        Args:
            db: SQLAlchemy async session
        """
        self.db = db
    
    # Tool operations
    async def create_tool(self, tool_data: Dict[str, Any]) -> ToolModel:
        """
        Create a new tool in the database.
        
        Args:
            tool_data: Tool data
            
        Returns:
            ToolModel: Created tool
        """
        tool = ToolModel(**tool_data)
        self.db.add(tool)
        await self.db.flush()
        return tool
    
    async def get_tool(self, tool_id: UUID) -> Optional[ToolModel]:
        """
        Get a tool by ID.
        
        Args:
            tool_id: Tool ID
            
        Returns:
            Optional[ToolModel]: Tool if found, None otherwise
        """
        result = await self.db.execute(
            select(ToolModel).where(ToolModel.id == tool_id)
        )
        return result.scalars().first()
    
    async def get_tool_by_name(self, name: str) -> Optional[ToolModel]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Optional[ToolModel]: Tool if found, None otherwise
        """
        result = await self.db.execute(
            select(ToolModel).where(ToolModel.name == name)
        )
        return result.scalars().first()
    
    async def update_tool(self, tool_id: UUID, tool_data: Dict[str, Any]) -> Optional[ToolModel]:
        """
        Update an existing tool.
        
        Args:
            tool_id: Tool ID
            tool_data: Tool data to update
            
        Returns:
            Optional[ToolModel]: Updated tool if found, None otherwise
        """
        await self.db.execute(
            update(ToolModel)
            .where(ToolModel.id == tool_id)
            .values(**tool_data, updated_at=datetime.utcnow())
        )
        return await self.get_tool(tool_id)
    
    async def delete_tool(self, tool_id: UUID) -> bool:
        """
        Delete a tool.
        
        Args:
            tool_id: Tool ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        result = await self.db.execute(
            delete(ToolModel).where(ToolModel.id == tool_id)
        )
        return result.rowcount > 0
    
    async def list_tools(
        self,
        capability: Optional[str] = None,
        source: Optional[Union[str, ToolSource]] = None,
        status: Optional[Union[str, ToolStatus]] = None,
        integration_type: Optional[Union[str, IntegrationType]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[ToolModel], int]:
        """
        List tools with filtering and pagination.
        
        Args:
            capability: Optional capability filter
            source: Optional source filter
            status: Optional status filter
            integration_type: Optional integration type filter
            page: Page number
            page_size: Page size
            
        Returns:
            Tuple[List[ToolModel], int]: List of tools and total count
        """
        query = select(ToolModel)
        
        # Apply filters
        if capability:
            query = query.where(ToolModel.capability.ilike(f"%{capability}%"))
        if source:
            query = query.where(ToolModel.source == source)
        if status:
            query = query.where(ToolModel.status == status)
        if integration_type:
            query = query.where(ToolModel.integration_type == integration_type)
        
        # Count total (without pagination)
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Apply pagination
        query = query.order_by(ToolModel.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        return result.scalars().all(), total
    
    async def search_tools_by_capability(
        self,
        capability: str,
        min_score: float = 0.5,
        limit: int = 10
    ) -> List[ToolModel]:
        """
        Search for tools matching a capability.
        
        Args:
            capability: Capability to search for
            min_score: Minimum match score
            limit: Maximum number of results
            
        Returns:
            List[ToolModel]: Matching tools
        """
        # Simple implementation with ILIKE for now
        # In a real implementation, this would use a vector similarity search
        query = select(ToolModel).where(
            ToolModel.capability.ilike(f"%{capability}%")
        ).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    # Tool integration operations
    async def create_integration(self, integration_data: Dict[str, Any]) -> ToolIntegrationModel:
        """
        Create a new tool integration.
        
        Args:
            integration_data: Integration data
            
        Returns:
            ToolIntegrationModel: Created integration
        """
        integration = ToolIntegrationModel(**integration_data)
        self.db.add(integration)
        await self.db.flush()
        return integration
    
    async def get_integration(self, tool_id: UUID, agent_id: UUID) -> Optional[ToolIntegrationModel]:
        """
        Get a tool integration.
        
        Args:
            tool_id: Tool ID
            agent_id: Agent ID
            
        Returns:
            Optional[ToolIntegrationModel]: Integration if found, None otherwise
        """
        result = await self.db.execute(
            select(ToolIntegrationModel).where(
                and_(
                    ToolIntegrationModel.tool_id == tool_id,
                    ToolIntegrationModel.agent_id == agent_id
                )
            )
        )
        return result.scalars().first()
    
    async def update_integration(
        self,
        tool_id: UUID,
        agent_id: UUID,
        integration_data: Dict[str, Any]
    ) -> Optional[ToolIntegrationModel]:
        """
        Update a tool integration.
        
        Args:
            tool_id: Tool ID
            agent_id: Agent ID
            integration_data: Integration data to update
            
        Returns:
            Optional[ToolIntegrationModel]: Updated integration if found, None otherwise
        """
        await self.db.execute(
            update(ToolIntegrationModel)
            .where(
                and_(
                    ToolIntegrationModel.tool_id == tool_id,
                    ToolIntegrationModel.agent_id == agent_id
                )
            )
            .values(**integration_data, updated_at=datetime.utcnow())
        )
        return await self.get_integration(tool_id, agent_id)
    
    async def delete_integration(self, tool_id: UUID, agent_id: UUID) -> bool:
        """
        Delete a tool integration.
        
        Args:
            tool_id: Tool ID
            agent_id: Agent ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        result = await self.db.execute(
            delete(ToolIntegrationModel).where(
                and_(
                    ToolIntegrationModel.tool_id == tool_id,
                    ToolIntegrationModel.agent_id == agent_id
                )
            )
        )
        return result.rowcount > 0
    
    async def list_agent_tools(
        self,
        agent_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[ToolIntegrationModel], int]:
        """
        List tools integrated with an agent.
        
        Args:
            agent_id: Agent ID
            status: Optional integration status filter
            page: Page number
            page_size: Page size
            
        Returns:
            Tuple[List[ToolIntegrationModel], int]: List of integrations and total count
        """
        query = select(ToolIntegrationModel).where(ToolIntegrationModel.agent_id == agent_id)
        
        # Apply filters
        if status:
            query = query.where(ToolIntegrationModel.status == status)
        
        # Count total (without pagination)
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Apply pagination
        query = query.order_by(ToolIntegrationModel.integrated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        return result.scalars().all(), total
    
    async def list_all_integrations(
        self,
        tool_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[ToolIntegrationModel], int]:
        """
        List all tool integrations with filtering and pagination.
        
        Args:
            tool_id: Optional tool ID filter
            agent_id: Optional agent ID filter
            status: Optional integration status filter
            page: Page number
            page_size: Page size
            
        Returns:
            Tuple[List[ToolIntegrationModel], int]: List of integrations and total count
        """
        query = select(ToolIntegrationModel)
        
        # Apply filters
        filters = []
        if tool_id:
            filters.append(ToolIntegrationModel.tool_id == tool_id)
        if agent_id:
            filters.append(ToolIntegrationModel.agent_id == agent_id)
        if status:
            filters.append(ToolIntegrationModel.status == status)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Count total (without pagination)
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Apply pagination
        query = query.order_by(ToolIntegrationModel.integrated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        return result.scalars().all(), total
    
    async def update_integration_usage(self, tool_id: UUID, agent_id: UUID) -> bool:
        """
        Update integration usage statistics.
        
        Args:
            tool_id: Tool ID
            agent_id: Agent ID
            
        Returns:
            bool: True if updated, False if not found
        """
        result = await self.db.execute(
            update(ToolIntegrationModel)
            .where(
                and_(
                    ToolIntegrationModel.tool_id == tool_id,
                    ToolIntegrationModel.agent_id == agent_id
                )
            )
            .values(
                last_used_at=datetime.utcnow(),
                usage_count=ToolIntegrationModel.usage_count + 1
            )
        )
        return result.rowcount > 0
    
    # Tool execution operations
    async def create_execution(self, execution_data: Dict[str, Any]) -> ToolExecutionModel:
        """
        Create a new tool execution record.
        
        Args:
            execution_data: Execution data
            
        Returns:
            ToolExecutionModel: Created execution record
        """
        execution = ToolExecutionModel(**execution_data)
        self.db.add(execution)
        await self.db.flush()
        return execution
    
    async def get_execution(self, execution_id: UUID) -> Optional[ToolExecutionModel]:
        """
        Get a tool execution record.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Optional[ToolExecutionModel]: Execution record if found, None otherwise
        """
        result = await self.db.execute(
            select(ToolExecutionModel).where(ToolExecutionModel.id == execution_id)
        )
        return result.scalars().first()
    
    async def update_execution(
        self,
        execution_id: UUID,
        execution_data: Dict[str, Any]
    ) -> Optional[ToolExecutionModel]:
        """
        Update a tool execution record.
        
        Args:
            execution_id: Execution ID
            execution_data: Execution data to update
            
        Returns:
            Optional[ToolExecutionModel]: Updated execution record if found, None otherwise
        """
        await self.db.execute(
            update(ToolExecutionModel)
            .where(ToolExecutionModel.id == execution_id)
            .values(**execution_data, updated_at=datetime.utcnow())
        )
        return await self.get_execution(execution_id)
    
    async def list_executions(
        self,
        tool_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None,
        status: Optional[str] = None,
        mode: Optional[str] = None,
        success: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[ToolExecutionModel], int]:
        """
        List tool executions with filtering and pagination.
        
        Args:
            tool_id: Optional tool ID filter
            agent_id: Optional agent ID filter
            status: Optional execution status filter
            mode: Optional execution mode filter
            success: Optional execution success filter
            page: Page number
            page_size: Page size
            
        Returns:
            Tuple[List[ToolExecutionModel], int]: List of executions and total count
        """
        query = select(ToolExecutionModel)
        
        # Apply filters
        filters = []
        if tool_id:
            filters.append(ToolExecutionModel.tool_id == tool_id)
        if agent_id:
            filters.append(ToolExecutionModel.agent_id == agent_id)
        if status:
            filters.append(ToolExecutionModel.status == status)
        if mode:
            filters.append(ToolExecutionModel.mode == mode)
        if success is not None:
            if success:
                filters.append(ToolExecutionModel.success == true())
            else:
                filters.append(ToolExecutionModel.success == false())
        
        if filters:
            query = query.where(and_(*filters))
        
        # Count total (without pagination)
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Apply pagination
        query = query.order_by(ToolExecutionModel.started_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        return result.scalars().all(), total
    
    async def create_execution_log(self, log_data: Dict[str, Any]) -> ToolExecutionLogModel:
        """
        Create a new execution log entry.
        
        Args:
            log_data: Log data
            
        Returns:
            ToolExecutionLogModel: Created log entry
        """
        log = ToolExecutionLogModel(**log_data)
        self.db.add(log)
        await self.db.flush()
        return log
    
    async def get_execution_logs(
        self,
        execution_id: UUID,
        limit: int = 100
    ) -> List[ToolExecutionLogModel]:
        """
        Get logs for a specific execution.
        
        Args:
            execution_id: Execution ID
            limit: Maximum number of log entries
            
        Returns:
            List[ToolExecutionLogModel]: Log entries
        """
        result = await self.db.execute(
            select(ToolExecutionLogModel)
            .where(ToolExecutionLogModel.execution_id == execution_id)
            .order_by(ToolExecutionLogModel.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    # Tool evaluation operations
    async def create_evaluation(self, evaluation_data: Dict[str, Any]) -> ToolEvaluationModel:
        """
        Create a new tool evaluation record.
        
        Args:
            evaluation_data: Evaluation data
            
        Returns:
            ToolEvaluationModel: Created evaluation record
        """
        evaluation = ToolEvaluationModel(**evaluation_data)
        self.db.add(evaluation)
        await self.db.flush()
        return evaluation
    
    async def get_evaluation(self, evaluation_id: UUID) -> Optional[ToolEvaluationModel]:
        """
        Get a tool evaluation record.
        
        Args:
            evaluation_id: Evaluation ID
            
        Returns:
            Optional[ToolEvaluationModel]: Evaluation record if found, None otherwise
        """
        result = await self.db.execute(
            select(ToolEvaluationModel).where(ToolEvaluationModel.id == evaluation_id)
        )
        return result.scalars().first()
    
    async def get_tool_evaluations(
        self,
        tool_id: UUID,
        limit: int = 10
    ) -> List[ToolEvaluationModel]:
        """
        Get evaluations for a specific tool.
        
        Args:
            tool_id: Tool ID
            limit: Maximum number of evaluations
            
        Returns:
            List[ToolEvaluationModel]: Evaluation records
        """
        result = await self.db.execute(
            select(ToolEvaluationModel)
            .where(ToolEvaluationModel.tool_id == tool_id)
            .order_by(ToolEvaluationModel.evaluation_timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def list_evaluations(
        self,
        tool_id: Optional[UUID] = None,
        evaluation_type: Optional[str] = None,
        min_score: Optional[float] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[ToolEvaluationModel], int]:
        """
        List tool evaluations with filtering and pagination.
        
        Args:
            tool_id: Optional tool ID filter
            evaluation_type: Optional evaluation type filter
            min_score: Optional minimum score filter
            page: Page number
            page_size: Page size
            
        Returns:
            Tuple[List[ToolEvaluationModel], int]: List of evaluations and total count
        """
        query = select(ToolEvaluationModel)
        
        # Apply filters
        filters = []
        if tool_id:
            filters.append(ToolEvaluationModel.tool_id == tool_id)
        if min_score is not None:
            filters.append(ToolEvaluationModel.overall_score >= min_score)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Count total (without pagination)
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Apply pagination
        query = query.order_by(ToolEvaluationModel.evaluation_timestamp.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        return result.scalars().all(), total
    
    # Discovery request operations
    async def create_discovery_request(
        self,
        discovery_data: Dict[str, Any]
    ) -> ToolDiscoveryRequestModel:
        """
        Create a new tool discovery request.
        
        Args:
            discovery_data: Discovery request data
            
        Returns:
            ToolDiscoveryRequestModel: Created discovery request
        """
        discovery = ToolDiscoveryRequestModel(**discovery_data)
        self.db.add(discovery)
        await self.db.flush()
        return discovery
    
    async def get_discovery_request(
        self,
        discovery_id: UUID
    ) -> Optional[ToolDiscoveryRequestModel]:
        """
        Get a tool discovery request.
        
        Args:
            discovery_id: Discovery request ID
            
        Returns:
            Optional[ToolDiscoveryRequestModel]: Discovery request if found, None otherwise
        """
        result = await self.db.execute(
            select(ToolDiscoveryRequestModel).where(
                ToolDiscoveryRequestModel.id == discovery_id
            )
        )
        return result.scalars().first()
    
    async def update_discovery_request(
        self,
        discovery_id: UUID,
        discovery_data: Dict[str, Any]
    ) -> Optional[ToolDiscoveryRequestModel]:
        """
        Update a tool discovery request.
        
        Args:
            discovery_id: Discovery request ID
            discovery_data: Discovery request data to update
            
        Returns:
            Optional[ToolDiscoveryRequestModel]: Updated discovery request if found, None otherwise
        """
        await self.db.execute(
            update(ToolDiscoveryRequestModel)
            .where(ToolDiscoveryRequestModel.id == discovery_id)
            .values(**discovery_data, updated_at=datetime.utcnow())
        )
        return await self.get_discovery_request(discovery_id)
    
    async def list_discovery_requests(
        self,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[ToolDiscoveryRequestModel], int]:
        """
        List tool discovery requests with filtering and pagination.
        
        Args:
            project_id: Optional project ID filter
            status: Optional status filter
            page: Page number
            page_size: Page size
            
        Returns:
            Tuple[List[ToolDiscoveryRequestModel], int]: List of discovery requests and total count
        """
        query = select(ToolDiscoveryRequestModel)
        
        # Apply filters
        filters = []
        if project_id:
            filters.append(ToolDiscoveryRequestModel.project_id == project_id)
        if status:
            filters.append(ToolDiscoveryRequestModel.status == status)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Count total (without pagination)
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Apply pagination
        query = query.order_by(ToolDiscoveryRequestModel.initiated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        return result.scalars().all(), total
    
    # MCP server config operations
    async def get_mcp_server_config(
        self,
        server_name: str
    ) -> Optional[MCPServerConfigModel]:
        """
        Get an MCP server configuration.
        
        Args:
            server_name: MCP server name
            
        Returns:
            Optional[MCPServerConfigModel]: MCP server configuration if found, None otherwise
        """
        result = await self.db.execute(
            select(MCPServerConfigModel).where(
                MCPServerConfigModel.name == server_name
            )
        )
        return result.scalars().first()
    
    async def list_mcp_server_configs(
        self,
        enabled_only: bool = False
    ) -> List[MCPServerConfigModel]:
        """
        List MCP server configurations.
        
        Args:
            enabled_only: If True, only return enabled configurations
            
        Returns:
            List[MCPServerConfigModel]: List of MCP server configurations
        """
        query = select(MCPServerConfigModel)
        
        if enabled_only:
            query = query.where(MCPServerConfigModel.enabled == true())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_mcp_server_config(
        self,
        server_name: str,
        config_data: Dict[str, Any]
    ) -> Optional[MCPServerConfigModel]:
        """
        Update an MCP server configuration.
        
        Args:
            server_name: MCP server name
            config_data: Configuration data to update
            
        Returns:
            Optional[MCPServerConfigModel]: Updated configuration if found, None otherwise
        """
        await self.db.execute(
            update(MCPServerConfigModel)
            .where(MCPServerConfigModel.name == server_name)
            .values(**config_data, updated_at=datetime.utcnow())
        )
        return await self.get_mcp_server_config(server_name)
