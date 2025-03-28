"""
Integration Adapter module.

This module defines the interface and concrete implementations of tool integration adapters,
providing functionality for integrating and executing different types of tools.
"""

import logging
import abc
import asyncio
import json
import os
from typing import Dict, Any, List, Optional, Type, Protocol, Union
from dataclasses import dataclass
import aiohttp
import subprocess
from pathlib import Path

from ...models.internal import Tool as ToolModel
from ...exceptions import (
    ToolIntegrationError,
    MCPIntegrationError,
    ToolExecutionError,
    ToolExecutionTimeoutError,
    SecurityViolationError,
)
from .validation import ParameterValidator, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of a tool execution."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    logs: Optional[List[str]] = None
    execution_time_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class IntegrationAdapter(abc.ABC):
    """Base class for tool integration adapters."""
    
    def __init__(
        self,
        tool: ToolModel,
        configuration: Dict[str, Any],
        validator: Optional[ParameterValidator] = None,
    ):
        """
        Initialize the integration adapter.
        
        Args:
            tool: Tool model
            configuration: Adapter configuration
            validator: Optional parameter validator
        """
        self.tool = tool
        self.configuration = configuration
        self.validator = validator or ParameterValidator()
        
        # Default timeout and resource limits
        self.timeout_seconds = configuration.get("timeout_seconds", 30)
        self.max_memory_mb = configuration.get("max_memory_mb", 500)
        self.max_cpu_percent = configuration.get("max_cpu_percent", 80)
    
    @abc.abstractmethod
    async def setup(self) -> None:
        """
        Set up the integration adapter.
        
        Raises:
            ToolIntegrationError: If setup fails
        """
        pass
    
    @abc.abstractmethod
    async def execute(
        self,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute the tool with the given parameters.
        
        Args:
            parameters: Execution parameters
            timeout: Optional execution timeout in seconds
            context: Optional execution context
            
        Returns:
            ExecutionResult: Result of the execution
            
        Raises:
            ToolExecutionError: If execution fails
            ToolExecutionTimeoutError: If execution times out
        """
        pass
    
    @abc.abstractmethod
    async def validate_parameters(
        self,
        parameters: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate parameters for the tool.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            ValidationResult: Validation result
        """
        pass
    
    async def _validate_parameters(
        self,
        parameters: Dict[str, Any],
    ) -> ValidationResult:
        """
        Helper method to validate parameters using the schema.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            ValidationResult: Validation result
        """
        if not self.tool.schema:
            return ValidationResult(valid=True)
        
        return self.validator.validate(self.tool.schema, parameters)


class MCPIntegrationAdapter(IntegrationAdapter):
    """Adapter for MCP tools."""
    
    def __init__(
        self,
        tool: ToolModel,
        configuration: Dict[str, Any],
        validator: Optional[ParameterValidator] = None,
        connection_timeout: int = 5,
        request_timeout: int = 30,
    ):
        """
        Initialize the MCP integration adapter.
        
        Args:
            tool: Tool model
            configuration: Adapter configuration
            validator: Optional parameter validator
            connection_timeout: Connection timeout in seconds
            request_timeout: Request timeout in seconds
        """
        super().__init__(tool, configuration, validator)
        
        # MCP-specific configuration
        self.server_name = configuration.get("server_name")
        self.tool_name = configuration.get("tool_name", tool.name)
        
        if not self.server_name:
            raise MCPIntegrationError("MCP server name is required")
        
        self.connection_timeout = connection_timeout
        self.request_timeout = request_timeout
        
        # MCP client session
        self._session = None
    
    async def setup(self) -> None:
        """
        Set up the MCP integration adapter.
        
        Raises:
            MCPIntegrationError: If setup fails
        """
        logger.info(f"Setting up MCP integration adapter for {self.tool.name}")
        
        try:
            # Create HTTP session
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(
                    connect=self.connection_timeout,
                    total=self.request_timeout,
                )
            )
            
            # Verify MCP server connection
            # In a real implementation, this would connect to the MCP server
            
            logger.info(f"MCP integration adapter setup complete for {self.tool.name}")
        except Exception as e:
            if self._session:
                await self._session.close()
                self._session = None
            
            logger.error(f"Error setting up MCP integration adapter: {str(e)}")
            raise MCPIntegrationError(
                f"Failed to set up MCP integration: {str(e)}",
                server_name=self.server_name,
                details={"tool_name": self.tool_name},
            )
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute an MCP tool.
        
        Args:
            parameters: Execution parameters
            timeout: Optional execution timeout in seconds
            context: Optional execution context
            
        Returns:
            ExecutionResult: Result of the execution
            
        Raises:
            ToolExecutionError: If execution fails
            ToolExecutionTimeoutError: If execution times out
        """
        logger.info(f"Executing MCP tool {self.tool_name} on server {self.server_name}")
        
        # Validate parameters
        validation_result = await self.validate_parameters(parameters)
        if not validation_result.valid:
            return ExecutionResult(
                success=False,
                error=f"Parameter validation failed: {validation_result.errors}",
                logs=["Parameter validation failed"],
            )
        
        try:
            # In a real implementation, this would call the MCP server
            # For now, simulate execution
            
            # Simulate execution time
            effective_timeout = timeout or self.timeout_seconds
            execution_start = asyncio.get_event_loop().time()
            
            await asyncio.sleep(0.1)  # Simulate execution time
            
            execution_time = (asyncio.get_event_loop().time() - execution_start) * 1000
            
            # Simulate successful execution
            return ExecutionResult(
                success=True,
                result={"output": f"Executed MCP tool {self.tool_name} with parameters {parameters}"},
                logs=[f"Executed MCP tool {self.tool_name}"],
                execution_time_ms=int(execution_time),
                metadata={"server_name": self.server_name, "tool_name": self.tool_name},
            )
        except asyncio.TimeoutError:
            logger.error(f"MCP tool execution timed out: {self.tool_name}")
            raise ToolExecutionTimeoutError(
                timeout or self.timeout_seconds,
                str(self.tool.id),
                f"MCP tool execution timed out after {timeout or self.timeout_seconds} seconds",
            )
        except Exception as e:
            logger.error(f"Error executing MCP tool: {str(e)}")
            raise ToolExecutionError(
                f"MCP tool execution failed: {str(e)}",
                execution_id=None,
                details={"server_name": self.server_name, "tool_name": self.tool_name},
            )
    
    async def validate_parameters(
        self,
        parameters: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate parameters for an MCP tool.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            ValidationResult: Validation result
        """
        return await self._validate_parameters(parameters)


class HTTPIntegrationAdapter(IntegrationAdapter):
    """Adapter for HTTP API tools."""
    
    def __init__(
        self,
        tool: ToolModel,
        configuration: Dict[str, Any],
        validator: Optional[ParameterValidator] = None,
    ):
        """
        Initialize the HTTP integration adapter.
        
        Args:
            tool: Tool model
            configuration: Adapter configuration
            validator: Optional parameter validator
        """
        super().__init__(tool, configuration, validator)
        
        # HTTP-specific configuration
        self.base_url = configuration.get("base_url")
        self.headers = configuration.get("headers", {})
        self.auth = configuration.get("auth")
        
        if not self.base_url:
            raise ToolIntegrationError("Base URL is required for HTTP integration")
        
        # HTTP client session
        self._session = None
    
    async def setup(self) -> None:
        """
        Set up the HTTP integration adapter.
        
        Raises:
            ToolIntegrationError: If setup fails
        """
        logger.info(f"Setting up HTTP integration adapter for {self.tool.name}")
        
        try:
            # Create HTTP session with configured timeouts and headers
            self._session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(
                    connect=5,
                    total=self.timeout_seconds,
                )
            )
            
            logger.info(f"HTTP integration adapter setup complete for {self.tool.name}")
        except Exception as e:
            if self._session:
                await self._session.close()
                self._session = None
            
            logger.error(f"Error setting up HTTP integration adapter: {str(e)}")
            raise ToolIntegrationError(f"Failed to set up HTTP integration: {str(e)}")
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute an HTTP API tool.
        
        Args:
            parameters: Execution parameters
            timeout: Optional execution timeout in seconds
            context: Optional execution context
            
        Returns:
            ExecutionResult: Result of the execution
            
        Raises:
            ToolExecutionError: If execution fails
            ToolExecutionTimeoutError: If execution times out
        """
        logger.info(f"Executing HTTP tool {self.tool.name} with URL {self.base_url}")
        
        # Validate parameters
        validation_result = await self.validate_parameters(parameters)
        if not validation_result.valid:
            return ExecutionResult(
                success=False,
                error=f"Parameter validation failed: {validation_result.errors}",
                logs=["Parameter validation failed"],
            )
        
        try:
            # In a real implementation, this would make an HTTP request
            # For now, simulate execution
            
            # Simulate execution time
            effective_timeout = timeout or self.timeout_seconds
            execution_start = asyncio.get_event_loop().time()
            
            await asyncio.sleep(0.1)  # Simulate execution time
            
            execution_time = (asyncio.get_event_loop().time() - execution_start) * 1000
            
            # Simulate successful execution
            return ExecutionResult(
                success=True,
                result={"data": f"Response from {self.base_url} with parameters {parameters}"},
                logs=[f"Made HTTP request to {self.base_url}"],
                execution_time_ms=int(execution_time),
                metadata={"url": self.base_url},
            )
        except asyncio.TimeoutError:
            logger.error(f"HTTP tool execution timed out: {self.tool.name}")
            raise ToolExecutionTimeoutError(
                timeout or self.timeout_seconds,
                str(self.tool.id),
                f"HTTP tool execution timed out after {timeout or self.timeout_seconds} seconds",
            )
        except Exception as e:
            logger.error(f"Error executing HTTP tool: {str(e)}")
            raise ToolExecutionError(
                f"HTTP tool execution failed: {str(e)}",
                execution_id=None,
                details={"url": self.base_url},
            )
    
    async def validate_parameters(
        self,
        parameters: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate parameters for an HTTP API tool.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            ValidationResult: Validation result
        """
        return await self._validate_parameters(parameters)


class CommandLineIntegrationAdapter(IntegrationAdapter):
    """Adapter for command-line tools."""
    
    def __init__(
        self,
        tool: ToolModel,
        configuration: Dict[str, Any],
        validator: Optional[ParameterValidator] = None,
    ):
        """
        Initialize the command-line integration adapter.
        
        Args:
            tool: Tool model
            configuration: Adapter configuration
            validator: Optional parameter validator
        """
        super().__init__(tool, configuration, validator)
        
        # Command-line specific configuration
        self.command_template = configuration.get("command_template")
        self.working_dir = configuration.get("working_dir")
        self.environment = configuration.get("environment", {})
        
        if not self.command_template:
            raise ToolIntegrationError("Command template is required for command-line integration")
    
    async def setup(self) -> None:
        """
        Set up the command-line integration adapter.
        
        Raises:
            ToolIntegrationError: If setup fails
        """
        logger.info(f"Setting up command-line integration adapter for {self.tool.name}")
        
        try:
            # Verify working directory exists if specified
            if self.working_dir and not os.path.isdir(self.working_dir):
                raise ToolIntegrationError(f"Working directory does not exist: {self.working_dir}")
            
            logger.info(f"Command-line integration adapter setup complete for {self.tool.name}")
        except Exception as e:
            logger.error(f"Error setting up command-line integration adapter: {str(e)}")
            raise ToolIntegrationError(f"Failed to set up command-line integration: {str(e)}")
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute a command-line tool.
        
        Args:
            parameters: Execution parameters
            timeout: Optional execution timeout in seconds
            context: Optional execution context
            
        Returns:
            ExecutionResult: Result of the execution
            
        Raises:
            ToolExecutionError: If execution fails
            ToolExecutionTimeoutError: If execution times out
        """
        logger.info(f"Executing command-line tool {self.tool.name}")
        
        # Validate parameters
        validation_result = await self.validate_parameters(parameters)
        if not validation_result.valid:
            return ExecutionResult(
                success=False,
                error=f"Parameter validation failed: {validation_result.errors}",
                logs=["Parameter validation failed"],
            )
        
        try:
            # Format command with parameters
            formatted_command = self._format_command(parameters)
            
            logger.info(f"Executing command: {formatted_command}")
            
            # In a real implementation, this would execute the command
            # For now, simulate execution
            
            # Simulate execution time
            effective_timeout = timeout or self.timeout_seconds
            execution_start = asyncio.get_event_loop().time()
            
            await asyncio.sleep(0.1)  # Simulate execution time
            
            execution_time = (asyncio.get_event_loop().time() - execution_start) * 1000
            
            # Simulate successful execution
            return ExecutionResult(
                success=True,
                result={"output": f"Output of command: {formatted_command}"},
                logs=[f"Executed command: {formatted_command}"],
                execution_time_ms=int(execution_time),
                metadata={"command": formatted_command},
            )
        except asyncio.TimeoutError:
            logger.error(f"Command-line tool execution timed out: {self.tool.name}")
            raise ToolExecutionTimeoutError(
                timeout or self.timeout_seconds,
                str(self.tool.id),
                f"Command-line tool execution timed out after {timeout or self.timeout_seconds} seconds",
            )
        except Exception as e:
            logger.error(f"Error executing command-line tool: {str(e)}")
            raise ToolExecutionError(
                f"Command-line tool execution failed: {str(e)}",
                execution_id=None,
                details={"command": self.command_template},
            )
    
    async def validate_parameters(
        self,
        parameters: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate parameters for a command-line tool.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            ValidationResult: Validation result
        """
        return await self._validate_parameters(parameters)
    
    def _format_command(self, parameters: Dict[str, Any]) -> str:
        """
        Format the command template with parameters.
        
        Args:
            parameters: Command parameters
            
        Returns:
            str: Formatted command
        """
        # Simple string formatting
        command = self.command_template
        
        # Replace placeholders like {param_name} with parameter values
        for key, value in parameters.items():
            placeholder = "{" + key + "}"
            if placeholder in command:
                if isinstance(value, str):
                    command = command.replace(placeholder, value)
                else:
                    command = command.replace(placeholder, json.dumps(value))
        
        return command


class IntegrationAdapterFactory:
    """Factory for creating integration adapters."""
    
    def __init__(
        self,
        mcp_connection_timeout: int = 5,
        mcp_request_timeout: int = 30,
        mcp_servers_config_path: Optional[str] = None,
    ):
        """
        Initialize the integration adapter factory.
        
        Args:
            mcp_connection_timeout: Connection timeout for MCP servers in seconds
            mcp_request_timeout: Request timeout for MCP servers in seconds
            mcp_servers_config_path: Path to MCP servers configuration
        """
        self.mcp_connection_timeout = mcp_connection_timeout
        self.mcp_request_timeout = mcp_request_timeout
        self.mcp_servers_config_path = mcp_servers_config_path
        
        # Register adapter types
        self._adapter_types = {
            "MCP": MCPIntegrationAdapter,
            "HTTP": HTTPIntegrationAdapter,
            "COMMAND_LINE": CommandLineIntegrationAdapter,
        }
        
        # Parameter validator singleton
        self._validator = ParameterValidator()
        
        logger.info("Integration adapter factory initialized")
    
    async def create_adapter(
        self,
        tool: ToolModel,
        configuration: Dict[str, Any],
    ) -> IntegrationAdapter:
        """
        Create an integration adapter for a tool.
        
        Args:
            tool: Tool model
            configuration: Adapter configuration
            
        Returns:
            IntegrationAdapter: Integration adapter
            
        Raises:
            ToolIntegrationError: If adapter creation fails
        """
        logger.info(f"Creating integration adapter for tool: {tool.name}")
        
        # Get adapter type
        adapter_type = self._get_adapter_type(tool, configuration)
        
        # Merge tool-specific configuration
        merged_config = self._merge_configuration(tool, configuration)
        
        # Create adapter
        try:
            if adapter_type == "MCP":
                adapter = MCPIntegrationAdapter(
                    tool,
                    merged_config,
                    self._validator,
                    self.mcp_connection_timeout,
                    self.mcp_request_timeout,
                )
            elif adapter_type == "HTTP":
                adapter = HTTPIntegrationAdapter(
                    tool,
                    merged_config,
                    self._validator,
                )
            elif adapter_type == "COMMAND_LINE":
                adapter = CommandLineIntegrationAdapter(
                    tool,
                    merged_config,
                    self._validator,
                )
            else:
                raise ToolIntegrationError(f"Unsupported integration type: {adapter_type}")
            
            # Set up adapter
            await adapter.setup()
            
            return adapter
        except Exception as e:
            logger.error(f"Error creating integration adapter: {str(e)}")
            if isinstance(e, ToolIntegrationError):
                raise
            raise ToolIntegrationError(f"Failed to create integration adapter: {str(e)}")
    
    def _get_adapter_type(
        self,
        tool: ToolModel,
        configuration: Dict[str, Any],
    ) -> str:
        """
        Get the adapter type for a tool.
        
        Args:
            tool: Tool model
            configuration: Adapter configuration
            
        Returns:
            str: Adapter type
            
        Raises:
            ToolIntegrationError: If adapter type cannot be determined
        """
        # Explicit adapter type in configuration takes precedence
        if "adapter_type" in configuration:
            adapter_type = configuration["adapter_type"].upper()
            if adapter_type in self._adapter_types:
                return adapter_type
            else:
                raise ToolIntegrationError(f"Unsupported adapter type: {adapter_type}")
        
        # Determine adapter type from tool properties
        if tool.source == "MCP":
            return "MCP"
        elif tool.integration_type == "HTTP":
            return "HTTP"
        elif tool.integration_type == "COMMAND_LINE":
            return "COMMAND_LINE"
        
        # Default to HTTP
        logger.warning(f"Could not determine adapter type for tool {tool.name}, defaulting to HTTP")
        return "HTTP"
    
    def _merge_configuration(
        self,
        tool: ToolModel,
        configuration: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Merge tool-specific configuration with provided configuration.
        
        Args:
            tool: Tool model
            configuration: Provided configuration
            
        Returns:
            Dict[str, Any]: Merged configuration
        """
        # Start with default configuration
        merged = {"timeout_seconds": 30, "max_memory_mb": 500}
        
        # Add tool-specific configuration if available
        if tool.configuration:
            merged.update(tool.configuration)
        
        # Add provided configuration (overrides defaults and tool-specific)
        merged.update(configuration)
        
        return merged
