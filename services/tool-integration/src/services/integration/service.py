"""
Tool Integration Service module.

This module defines the main integration service for integrating tools with agents,
providing a unified interface for tool integration and execution.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ...models.internal import Tool as ToolModel
from ...exceptions import (
    ToolIntegrationError,
    ToolExecutionError,
    ToolExecutionTimeoutError,
    SecurityViolationError,
    ToolSchemaValidationError,
)
from ..repository import ToolRepository
from ..security import SecurityScanner
from .adapter import (
    IntegrationAdapter,
    IntegrationAdapterFactory,
    ExecutionResult,
)
from .validation import ParameterValidator, ValidationResult

logger = logging.getLogger(__name__)


class ToolIntegrationService:
    """Service for integrating tools with agents and executing tools."""
    
    def __init__(
        self,
        repository: ToolRepository,
        event_bus: Any,
        integration_factory: IntegrationAdapterFactory,
        security_scanner: SecurityScanner,
        tool_execution_timeout: int = 30,
        max_tool_memory_mb: int = 500,
        max_tool_execution_time_sec: int = 60,
        sandboxed_execution: bool = True,
    ):
        """
        Initialize the tool integration service.
        
        Args:
            repository: Tool repository
            event_bus: Event bus for publishing events
            integration_factory: Integration adapter factory
            security_scanner: Security scanner service
            tool_execution_timeout: Default timeout for tool execution in seconds
            max_tool_memory_mb: Maximum memory usage for tools in MB
            max_tool_execution_time_sec: Maximum execution time for tools in seconds
            sandboxed_execution: Whether to run tools in a sandbox
        """
        self.repository = repository
        self.event_bus = event_bus
        self.integration_factory = integration_factory
        self.security_scanner = security_scanner
        
        # Execution settings
        self.tool_execution_timeout = tool_execution_timeout
        self.max_tool_memory_mb = max_tool_memory_mb
        self.max_tool_execution_time_sec = max_tool_execution_time_sec
        self.sandboxed_execution = sandboxed_execution
        
        # Parameter validator
        self.validator = ParameterValidator()
        
        # Cache of integration adapters
        self._adapter_cache: Dict[str, IntegrationAdapter] = {}
        
        logger.info("Tool integration service initialized")
    
    async def integrate_tool(
        self,
        tool: ToolModel,
        agent_id: str,
        configuration: Dict[str, Any],
        permissions: List[str],
    ) -> Dict[str, Any]:
        """
        Integrate a tool with an agent.
        
        Args:
            tool: Tool to integrate
            agent_id: Agent ID
            configuration: Integration configuration
            permissions: Permissions for the integration
            
        Returns:
            Dict[str, Any]: Integration details
            
        Raises:
            ToolIntegrationError: If integration fails
            SecurityViolationError: If integration configuration violates security policies
        """
        logger.info(f"Integrating tool {tool.id} with agent {agent_id}")
        
        # Check security
        security_check = await self.security_scanner.check_integration_security(
            tool, configuration, permissions
        )
        
        if not security_check.approved:
            logger.error(f"Integration denied due to security concerns: {security_check.reason}")
            raise SecurityViolationError(
                security_check.reason or "Integration denied due to security concerns",
                security_check.violation_type or "SECURITY_POLICY_VIOLATION",
                security_check.details,
            )
        
        try:
            # Create integration adapter to validate configuration
            adapter = await self.integration_factory.create_adapter(tool, configuration)
            
            # Create integration record
            integration_data = {
                "tool_id": tool.id,
                "agent_id": agent_id,
                "configuration": configuration,
                "permissions": permissions,
                "status": "ACTIVE",
                "integrated_at": datetime.utcnow(),
            }
            
            # Store integration in database
            integration = await self.repository.create_integration(integration_data)
            
            # Publish integration event
            await self._publish_integration_event(integration)
            
            return integration
        except Exception as e:
            logger.error(f"Error integrating tool: {str(e)}")
            if isinstance(e, (ToolIntegrationError, SecurityViolationError)):
                raise
            raise ToolIntegrationError(f"Failed to integrate tool: {str(e)}")
    
    async def execute_tool(
        self,
        tool_id: str,
        agent_id: str,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None,
        mode: str = "SYNCHRONOUS",
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute a tool.
        
        Args:
            tool_id: Tool ID
            agent_id: Agent ID
            parameters: Execution parameters
            timeout: Optional execution timeout in seconds
            mode: Execution mode (SYNCHRONOUS or ASYNCHRONOUS)
            context: Optional execution context
            
        Returns:
            ExecutionResult: Result of the execution
            
        Raises:
            ToolExecutionError: If execution fails
            ToolExecutionTimeoutError: If execution times out
            ToolSchemaValidationError: If parameters are invalid
            SecurityViolationError: If execution violates security policies
        """
        logger.info(f"Executing tool {tool_id} for agent {agent_id}")
        
        # Get the tool
        tool = await self.repository.get_tool(tool_id)
        if not tool:
            raise ToolExecutionError(f"Tool not found: {tool_id}")
        
        # Get the integration
        integration = await self.repository.get_integration(tool_id, agent_id)
        if not integration:
            raise ToolExecutionError(
                f"Integration not found for tool {tool_id} and agent {agent_id}"
            )
        
        # Check security before execution
        if self.security_scanner.enabled:
            security_check = await self.security_scanner.validate_execution_parameters(
                tool, parameters, context
            )
            
            if not security_check.approved:
                logger.error(f"Execution denied due to security concerns: {security_check.reason}")
                raise SecurityViolationError(
                    security_check.reason or "Execution denied due to security concerns",
                    security_check.violation_type or "SECURITY_POLICY_VIOLATION",
                    security_check.details,
                )
        
        # Create execution record
        execution_id = str(uuid.uuid4())
        execution_data = {
            "id": execution_id,
            "tool_id": tool_id,
            "agent_id": agent_id,
            "parameters": parameters,
            "mode": mode,
            "status": "RUNNING",
            "started_at": datetime.utcnow(),
            "context": context or {},
        }
        
        # Store execution in database
        await self.repository.create_execution(execution_data)
        
        # Update usage statistics
        await self.repository.update_integration_usage(tool_id, agent_id)
        
        try:
            # Get or create adapter
            adapter = await self._get_adapter(tool, integration.configuration)
            
            # Execute the tool
            execution_result = await adapter.execute(
                parameters,
                timeout=timeout or self.tool_execution_timeout,
                context=context,
            )
            
            # Update execution record with results
            await self._update_execution_record(
                execution_id,
                execution_result,
                "COMPLETED" if execution_result.success else "FAILED",
            )
            
            # Create log entry
            await self._create_execution_log(
                execution_id,
                "INFO" if execution_result.success else "ERROR",
                f"Tool execution {'succeeded' if execution_result.success else 'failed'}",
                {
                    "result": execution_result.result,
                    "error": execution_result.error,
                    "execution_time_ms": execution_result.execution_time_ms,
                },
            )
            
            # Publish execution event
            await self._publish_execution_event(execution_id, execution_result)
            
            return execution_result
        except ToolExecutionTimeoutError as e:
            logger.error(f"Tool execution timed out: {str(e)}")
            
            # Update execution record for timeout
            await self._update_execution_record(
                execution_id,
                ExecutionResult(success=False, error=str(e)),
                "TIMEOUT",
            )
            
            # Create log entry for timeout
            await self._create_execution_log(
                execution_id,
                "ERROR",
                f"Tool execution timed out after {timeout or self.tool_execution_timeout} seconds",
                {"error": str(e)},
            )
            
            raise
        except Exception as e:
            logger.error(f"Error executing tool: {str(e)}")
            
            # Update execution record for error
            await self._update_execution_record(
                execution_id,
                ExecutionResult(success=False, error=str(e)),
                "FAILED",
            )
            
            # Create log entry for error
            await self._create_execution_log(
                execution_id,
                "ERROR",
                f"Tool execution failed: {str(e)}",
                {"error": str(e)},
            )
            
            if isinstance(e, (ToolExecutionError, SecurityViolationError, ToolSchemaValidationError)):
                raise
            
            raise ToolExecutionError(
                f"Tool execution failed: {str(e)}",
                execution_id=execution_id,
            )
    
    async def validate_parameters(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate parameters for a tool.
        
        Args:
            tool_id: Tool ID
            parameters: Parameters to validate
            
        Returns:
            ValidationResult: Validation result
            
        Raises:
            ToolExecutionError: If tool not found
        """
        logger.info(f"Validating parameters for tool {tool_id}")
        
        # Get the tool
        tool = await self.repository.get_tool(tool_id)
        if not tool:
            raise ToolExecutionError(f"Tool not found: {tool_id}")
        
        # Validate parameters
        if tool.schema:
            return self.validator.validate(tool.schema, parameters)
        else:
            logger.warning(f"Tool {tool_id} has no schema for validation")
            return ValidationResult(valid=True)
    
    async def get_adapter(
        self,
        tool_id: str,
        configuration: Dict[str, Any],
    ) -> IntegrationAdapter:
        """
        Get an integration adapter for a tool.
        
        Args:
            tool_id: Tool ID
            configuration: Adapter configuration
            
        Returns:
            IntegrationAdapter: Integration adapter
            
        Raises:
            ToolExecutionError: If tool not found
            ToolIntegrationError: If adapter creation fails
        """
        logger.info(f"Getting adapter for tool {tool_id}")
        
        # Get the tool
        tool = await self.repository.get_tool(tool_id)
        if not tool:
            raise ToolExecutionError(f"Tool not found: {tool_id}")
        
        return await self._get_adapter(tool, configuration)
    
    async def _get_adapter(
        self,
        tool: ToolModel,
        configuration: Dict[str, Any],
    ) -> IntegrationAdapter:
        """
        Get or create an integration adapter for a tool.
        
        Args:
            tool: Tool model
            configuration: Adapter configuration
            
        Returns:
            IntegrationAdapter: Integration adapter
        """
        # Generate cache key
        cache_key = f"{tool.id}:{hash(frozenset(configuration.items()))}"
        
        # Check cache
        if cache_key in self._adapter_cache:
            return self._adapter_cache[cache_key]
        
        # Create adapter
        adapter = await self.integration_factory.create_adapter(tool, configuration)
        
        # Cache adapter
        self._adapter_cache[cache_key] = adapter
        
        return adapter
    
    async def _update_execution_record(
        self,
        execution_id: str,
        execution_result: ExecutionResult,
        status: str,
    ) -> None:
        """
        Update execution record with results.
        
        Args:
            execution_id: Execution ID
            execution_result: Execution result
            status: Execution status
        """
        logger.info(f"Updating execution record {execution_id}: {status}")
        
        # Update execution record
        update_data = {
            "status": status,
            "completed_at": datetime.utcnow(),
            "success": execution_result.success,
            "error": execution_result.error,
            "result": execution_result.result,
            "execution_time_ms": execution_result.execution_time_ms,
        }
        
        try:
            await self.repository.update_execution(execution_id, update_data)
        except Exception as e:
            logger.error(f"Error updating execution record: {str(e)}")
    
    async def _create_execution_log(
        self,
        execution_id: str,
        level: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Create execution log entry.
        
        Args:
            execution_id: Execution ID
            level: Log level
            message: Log message
            data: Optional log data
        """
        logger.info(f"Creating execution log for {execution_id}: {message}")
        
        # Create log entry
        log_data = {
            "execution_id": execution_id,
            "timestamp": datetime.utcnow(),
            "level": level,
            "message": message,
            "data": data or {},
        }
        
        try:
            await self.repository.create_execution_log(log_data)
        except Exception as e:
            logger.error(f"Error creating execution log: {str(e)}")
    
    async def _publish_integration_event(self, integration: Dict[str, Any]) -> None:
        """
        Publish integration event.
        
        Args:
            integration: Integration details
        """
        if self.event_bus:
            await self.event_bus.publish(
                "tool_integrated",
                {
                    "tool_id": str(integration["tool_id"]),
                    "agent_id": str(integration["agent_id"]),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
    
    async def _publish_execution_event(
        self,
        execution_id: str,
        execution_result: ExecutionResult,
    ) -> None:
        """
        Publish execution event.
        
        Args:
            execution_id: Execution ID
            execution_result: Execution result
        """
        if self.event_bus:
            await self.event_bus.publish(
                "tool_executed",
                {
                    "execution_id": execution_id,
                    "success": execution_result.success,
                    "execution_time_ms": execution_result.execution_time_ms,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
