"""
Tool Registry module.

This module defines the tool registry service for managing tools,
providing functionality for registration, lookup, and status management.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime

from ..models.internal import Tool as ToolModel
from shared.models.src.tool import ToolStatus, ToolSource, IntegrationType
from ..exceptions import ToolNotFoundError, ToolRegistrationError, ToolValidationError
from .repository import ToolRepository

logger = logging.getLogger(__name__)

class ToolRegistry:
    """Service for managing the tool registry."""
    
    def __init__(
        self,
        repository: ToolRepository,
        event_bus: Any,
        cache_ttl: int = 600,
    ):
        """
        Initialize the tool registry.
        
        Args:
            repository: Tool repository
            event_bus: Event bus for publishing events
            cache_ttl: Tool registry cache TTL in seconds
        """
        self.repository = repository
        self.event_bus = event_bus
        self.cache_ttl = cache_ttl
    
    async def register_tool(self, tool_data: Dict[str, Any]) -> ToolModel:
        """
        Register a new tool.
        
        Args:
            tool_data: Tool data
            
        Returns:
            ToolModel: Registered tool
            
        Raises:
            ToolRegistrationError: If registration fails
            ToolValidationError: If tool data is invalid
        """
        logger.info(f"Registering tool: {tool_data.get('name')}")
        
        # Check if tool with same name already exists
        existing_tool = await self.repository.get_tool_by_name(tool_data.get("name"))
        if existing_tool:
            logger.error(f"Tool with name '{tool_data.get('name')}' already exists")
            raise ToolRegistrationError(
                f"Tool with name '{tool_data.get('name')}' already exists"
            )
        
        # Validate capability is provided
        if not tool_data.get("capability"):
            logger.error("Tool capability is required")
            raise ToolValidationError("Tool capability is required", ["capability is required"])
        
        try:
            # Create the tool
            tool = await self.repository.create_tool(tool_data)
            
            # Publish tool registered event
            await self._publish_tool_registered_event(tool)
            
            return tool
        except Exception as e:
            logger.error(f"Error registering tool: {str(e)}")
            raise ToolRegistrationError(f"Error registering tool: {str(e)}")
    
    async def register_many(self, tools_data: List[Dict[str, Any]]) -> List[ToolModel]:
        """
        Register multiple tools.
        
        Args:
            tools_data: List of tool data dictionaries
            
        Returns:
            List[ToolModel]: List of registered tools
        """
        logger.info(f"Registering {len(tools_data)} tools")
        
        registered_tools = []
        failed_tools = []
        
        for tool_data in tools_data:
            try:
                tool = await self.register_tool(tool_data)
                registered_tools.append(tool)
            except (ToolRegistrationError, ToolValidationError) as e:
                logger.warning(f"Failed to register tool {tool_data.get('name')}: {str(e)}")
                failed_tools.append({
                    "data": tool_data,
                    "error": str(e)
                })
        
        logger.info(f"Registered {len(registered_tools)} tools, {len(failed_tools)} failed")
        
        # If all tools failed, raise an error
        if not registered_tools and failed_tools:
            raise ToolRegistrationError(
                f"Failed to register any tools: {', '.join(f['error'] for f in failed_tools)}"
            )
        
        return registered_tools
    
    async def get_tool(self, tool_id: UUID) -> ToolModel:
        """
        Get a tool by ID.
        
        Args:
            tool_id: Tool ID
            
        Returns:
            ToolModel: Tool
            
        Raises:
            ToolNotFoundError: If tool not found
        """
        tool = await self.repository.get_tool(tool_id)
        if not tool:
            logger.error(f"Tool not found: {tool_id}")
            raise ToolNotFoundError(str(tool_id))
        return tool
    
    async def update_tool(self, tool_id: UUID, tool_data: Dict[str, Any]) -> ToolModel:
        """
        Update a tool.
        
        Args:
            tool_id: Tool ID
            tool_data: Tool data to update
            
        Returns:
            ToolModel: Updated tool
            
        Raises:
            ToolNotFoundError: If tool not found
            ToolValidationError: If update data is invalid
        """
        logger.info(f"Updating tool: {tool_id}")
        
        # Get the tool to ensure it exists
        await self.get_tool(tool_id)
        
        try:
            # Update the tool
            updated_tool = await self.repository.update_tool(tool_id, tool_data)
            if not updated_tool:
                logger.error(f"Tool not found after update: {tool_id}")
                raise ToolNotFoundError(str(tool_id))
            
            # Publish tool updated event
            await self._publish_tool_updated_event(updated_tool)
            
            return updated_tool
        except Exception as e:
            if isinstance(e, ToolNotFoundError):
                raise
            logger.error(f"Error updating tool: {str(e)}")
            raise ToolValidationError(f"Error updating tool: {str(e)}", [str(e)])
    
    async def delete_tool(self, tool_id: UUID) -> None:
        """
        Delete a tool.
        
        Args:
            tool_id: Tool ID
            
        Raises:
            ToolNotFoundError: If tool not found
        """
        logger.info(f"Deleting tool: {tool_id}")
        
        # Get the tool to ensure it exists and for event publishing
        tool = await self.get_tool(tool_id)
        
        # Delete the tool
        deleted = await self.repository.delete_tool(tool_id)
        if not deleted:
            logger.error(f"Tool not found during deletion: {tool_id}")
            raise ToolNotFoundError(str(tool_id))
        
        # Publish tool deleted event
        await self._publish_tool_deleted_event(tool)
    
    async def list_tools(
        self,
        capability: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[str] = None,
        integration_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ToolModel], int]:
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
        logger.info(f"Listing tools (capability={capability}, source={source}, status={status})")
        
        return await self.repository.list_tools(
            capability=capability,
            source=source,
            status=status,
            integration_type=integration_type,
            page=page,
            page_size=page_size
        )
    
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
        logger.info(f"Searching for tools with capability: {capability}")
        
        return await self.repository.search_tools_by_capability(
            capability=capability,
            min_score=min_score,
            limit=limit
        )
    
    async def approve_tool(self, tool_id: UUID) -> ToolModel:
        """
        Approve a tool for use.
        
        Args:
            tool_id: Tool ID
            
        Returns:
            ToolModel: Approved tool
            
        Raises:
            ToolNotFoundError: If tool not found
        """
        logger.info(f"Approving tool: {tool_id}")
        
        # Get the tool to ensure it exists
        await self.get_tool(tool_id)
        
        # Update the tool status
        return await self.repository.update_tool(tool_id, {
            "status": ToolStatus.APPROVED
        })
    
    async def deprecate_tool(self, tool_id: UUID) -> ToolModel:
        """
        Deprecate a tool.
        
        Args:
            tool_id: Tool ID
            
        Returns:
            ToolModel: Deprecated tool
            
        Raises:
            ToolNotFoundError: If tool not found
        """
        logger.info(f"Deprecating tool: {tool_id}")
        
        # Get the tool to ensure it exists
        await self.get_tool(tool_id)
        
        # Update the tool status
        return await self.repository.update_tool(tool_id, {
            "status": ToolStatus.DEPRECATED
        })
    
    async def register_integration(self, integration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a tool integration for an agent.
        
        Args:
            integration_data: Integration data
            
        Returns:
            Dict[str, Any]: Integration details
            
        Raises:
            ToolNotFoundError: If tool not found
        """
        tool_id = integration_data.get("tool_id")
        agent_id = integration_data.get("agent_id")
        
        logger.info(f"Registering integration for tool {tool_id} with agent {agent_id}")
        
        # Get the tool to ensure it exists
        await self.get_tool(tool_id)
        
        # Check if integration already exists
        existing_integration = await self.repository.get_integration(tool_id, agent_id)
        if existing_integration:
            logger.info(f"Integration already exists, updating: {tool_id}, {agent_id}")
            
            # Update the integration
            integration = await self.repository.update_integration(
                tool_id, agent_id, integration_data
            )
        else:
            # Create the integration
            integration = await self.repository.create_integration(integration_data)
        
        # Publish integration event
        await self._publish_tool_integrated_event(integration)
        
        return integration
    
    async def update_evaluation(self, tool_id: UUID, evaluation_result: Dict[str, Any]) -> ToolModel:
        """
        Update tool with evaluation results.
        
        Args:
            tool_id: Tool ID
            evaluation_result: Evaluation results
            
        Returns:
            ToolModel: Updated tool
            
        Raises:
            ToolNotFoundError: If tool not found
        """
        logger.info(f"Updating tool evaluation: {tool_id}")
        
        # Get the tool to ensure it exists
        await self.get_tool(tool_id)
        
        # Extract scores and other metrics from evaluation
        update_data = {
            "last_evaluated_at": datetime.utcnow()
        }
        
        if "score" in evaluation_result:
            update_data["overall_score"] = evaluation_result["score"]
        
        for key in ["security_score", "performance_score", "compatibility_score"]:
            if key in evaluation_result:
                update_data[key] = evaluation_result[key]
        
        # Update the tool
        return await self.repository.update_tool(tool_id, update_data)
    
    # Event publishing methods
    async def _publish_tool_registered_event(self, tool: ToolModel) -> None:
        """Publish tool registered event."""
        if self.event_bus:
            await self.event_bus.publish(
                "tool_registered",
                {
                    "tool_id": str(tool.id),
                    "name": tool.name,
                    "capability": tool.capability,
                    "source": tool.source,
                    "integration_type": tool.integration_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    async def _publish_tool_updated_event(self, tool: ToolModel) -> None:
        """Publish tool updated event."""
        if self.event_bus:
            await self.event_bus.publish(
                "tool_updated",
                {
                    "tool_id": str(tool.id),
                    "name": tool.name,
                    "status": tool.status,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    async def _publish_tool_deleted_event(self, tool: ToolModel) -> None:
        """Publish tool deleted event."""
        if self.event_bus:
            await self.event_bus.publish(
                "tool_deleted",
                {
                    "tool_id": str(tool.id),
                    "name": tool.name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    async def _publish_tool_integrated_event(self, integration: Dict[str, Any]) -> None:
        """Publish tool integrated event."""
        if self.event_bus:
            await self.event_bus.publish(
                "tool_integrated",
                {
                    "tool_id": str(integration["tool_id"]),
                    "agent_id": str(integration["agent_id"]),
                    "status": integration["status"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
