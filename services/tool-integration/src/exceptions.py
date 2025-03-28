"""
Tool Integration Service custom exceptions.

This module defines custom exception classes for the Tool Integration service,
including error codes and HTTP status codes.
"""

from fastapi import status
from typing import Optional, Dict, Any

class ToolIntegrationError(Exception):
    """Base exception for Tool Integration errors"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "TOOL_INTEGRATION_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            error_code: Error code for client identification
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)
    
    def __str__(self) -> str:
        return self.message


class ToolNotFoundError(ToolIntegrationError):
    """Raised when a tool is not found"""
    
    def __init__(
        self,
        tool_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            tool_id: ID of the tool that was not found
            message: Optional custom error message
            details: Additional error details
        """
        default_message = f"Tool with ID {tool_id} not found"
        super().__init__(
            message=message or default_message,
            error_code="TOOL_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"tool_id": tool_id, **(details or {})},
        )


class ToolValidationError(ToolIntegrationError):
    """Raised when tool validation fails"""
    
    def __init__(
        self,
        message: str,
        validation_errors: list,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            validation_errors: List of validation errors
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="TOOL_VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"validation_errors": validation_errors, **(details or {})},
        )


class ToolSchemaValidationError(ToolValidationError):
    """Raised when a tool schema validation fails"""
    
    def __init__(
        self,
        schema_errors: list,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            schema_errors: List of schema validation errors
            message: Optional custom error message
            details: Additional error details
        """
        default_message = "Tool schema validation failed"
        super().__init__(
            message=message or default_message,
            validation_errors=schema_errors,
            details=details,
        )
        self.error_code = "SCHEMA_VALIDATION_ERROR"


class ToolExecutionError(ToolIntegrationError):
    """Raised when tool execution fails"""
    
    def __init__(
        self,
        message: str,
        execution_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            execution_id: Optional ID of the failed execution
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="TOOL_EXECUTION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={**({"execution_id": execution_id} if execution_id else {}), **(details or {})},
        )


class ToolExecutionTimeoutError(ToolExecutionError):
    """Raised when tool execution times out"""
    
    def __init__(
        self,
        timeout_seconds: int,
        tool_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            timeout_seconds: Timeout in seconds
            tool_id: ID of the tool
            message: Optional custom error message
            details: Additional error details
        """
        default_message = f"Tool execution timed out after {timeout_seconds} seconds"
        super().__init__(
            message=message or default_message,
            details={"timeout_seconds": timeout_seconds, "tool_id": tool_id, **(details or {})},
        )
        self.error_code = "EXECUTION_TIMEOUT"


class SecurityViolationError(ToolIntegrationError):
    """Raised when a security violation is detected"""
    
    def __init__(
        self,
        message: str,
        violation_type: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            violation_type: Type of security violation
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="SECURITY_VIOLATION",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"violation_type": violation_type, **(details or {})},
        )


class ToolDiscoveryError(ToolIntegrationError):
    """Raised when tool discovery fails"""
    
    def __init__(
        self,
        message: str,
        source: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            source: Optional tool source where discovery failed
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="TOOL_DISCOVERY_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={**({"source": source} if source else {}), **(details or {})},
        )


class MCPIntegrationError(ToolIntegrationError):
    """Raised when MCP integration fails"""
    
    def __init__(
        self,
        message: str,
        server_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            server_name: Optional MCP server name
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="MCP_INTEGRATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={**({"server_name": server_name} if server_name else {}), **(details or {})},
        )


class MCPToolNotAvailableError(MCPIntegrationError):
    """Raised when an MCP tool is not available"""
    
    def __init__(
        self,
        message: str,
        server_name: Optional[str] = None,
        tool_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            server_name: Optional MCP server name
            tool_name: Optional MCP tool name
            details: Additional error details
        """
        combined_details = {}
        if server_name:
            combined_details["server_name"] = server_name
        if tool_name:
            combined_details["tool_name"] = tool_name
        if details:
            combined_details.update(details)
            
        super().__init__(
            message=message,
            server_name=server_name,
            details=combined_details,
        )
        self.error_code = "MCP_TOOL_NOT_AVAILABLE"
        self.status_code = status.HTTP_404_NOT_FOUND


class ToolRegistrationError(ToolIntegrationError):
    """Raised when tool registration fails"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="TOOL_REGISTRATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class ToolEvaluationError(ToolIntegrationError):
    """Raised when tool evaluation fails"""
    
    def __init__(
        self,
        message: str,
        tool_id: Optional[str] = None,
        evaluation_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            tool_id: Optional tool ID
            evaluation_type: Optional type of evaluation that failed
            details: Additional error details
        """
        combined_details = {}
        if tool_id:
            combined_details["tool_id"] = tool_id
        if evaluation_type:
            combined_details["evaluation_type"] = evaluation_type
        if details:
            combined_details.update(details)
            
        super().__init__(
            message=message,
            error_code="TOOL_EVALUATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=combined_details,
        )
