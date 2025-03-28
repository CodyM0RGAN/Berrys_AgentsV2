"""
Tool Integration API client for interacting with the Tool Integration service.
"""
import logging
from typing import Any, Dict, List, Optional, Union, Awaitable

from shared.utils.src.clients.base import BaseAPIClient

# Set up logger
logger = logging.getLogger(__name__)

class ToolIntegrationClient(BaseAPIClient):
    """Client for interacting with the Tool Integration API."""
    
    async def register_tool(
        self,
        name: str,
        tool_type: str,
        description: str,
        capabilities: List[str],
        config_schema: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register a new tool with the Tool Integration system.
        
        Args:
            name: Tool name
            tool_type: Type of tool
            description: Tool description
            capabilities: List of tool capabilities
            config_schema: JSON schema for tool configuration
            metadata: Additional metadata
            
        Returns:
            Registered tool details
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def register_tool_operation():
            data = {
                'name': name,
                'tool_type': tool_type,
                'description': description,
                'capabilities': capabilities,
                'config_schema': config_schema
            }
            
            if metadata:
                data['metadata'] = metadata
            
            return self.post('/tools', data=data)

        try:
            return await retry_with_backoff(
                operation=register_tool_operation,
                policy=retry_policy,
                operation_name="register_tool"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to register tool after multiple retries: {e}")
            raise
    
    async def update_tool(
        self,
        tool_id: Union[str, int],
        name: Optional[str] = None,
        description: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        config_schema: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing tool.
        
        Args:
            tool_id: Tool ID
            name: New name
            description: New description
            capabilities: Updated list of capabilities
            config_schema: Updated JSON schema for tool configuration
            status: New status
            metadata: Updated metadata
            
        Returns:
            Updated tool details
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def update_tool_operation():
            data = {}
            
            if name:
                data['name'] = name
            
            if description:
                data['description'] = description
            
            if capabilities:
                data['capabilities'] = capabilities
            
            if config_schema:
                data['config_schema'] = config_schema
            
            if status:
                data['status'] = status
            
            if metadata:
                data['metadata'] = metadata
            
            return self.put(f'/tools/{tool_id}', data=data)

        try:
            return await retry_with_backoff(
                operation=update_tool_operation,
                policy=retry_policy,
                operation_name="update_tool"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to update tool after multiple retries: {e}")
            raise
    
    async def deregister_tool(self, tool_id: Union[str, int]) -> Dict[str, Any]:
        """
        Deregister a tool.
        
        Args:
            tool_id: Tool ID
            
        Returns:
            Response data
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=2,  # Fewer retries for deletion operations
            base_delay=1.0,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def deregister_tool_operation():
            return self.delete(f'/tools/{tool_id}')

        try:
            return await retry_with_backoff(
                operation=deregister_tool_operation,
                policy=retry_policy,
                operation_name="deregister_tool"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to deregister tool after multiple retries: {e}")
            raise
    
    def get_tool(self, tool_id: Union[str, int]) -> Dict[str, Any]:
        """
        Get details for a specific tool.
        
        Args:
            tool_id: Tool ID
            
        Returns:
            Tool details
        """
        return self.get(f'/tools/{tool_id}')
    
    def get_tools(
        self,
        tool_type: Optional[str] = None,
        capability: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Get a list of tools.
        
        Args:
            tool_type: Filter by tool type
            capability: Filter by capability
            status: Filter by status
            page: Page number
            per_page: Items per page
            
        Returns:
            Dict containing tools and pagination info
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        
        if tool_type:
            params['tool_type'] = tool_type
        
        if capability:
            params['capability'] = capability
        
        if status:
            params['status'] = status
        
        return self.get('/tools', params=params)
    
    async def create_tool_instance(
        self,
        tool_id: Union[str, int],
        name: str,
        config: Dict[str, Any],
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new instance of a tool with specific configuration.
        
        Args:
            tool_id: Tool ID
            name: Instance name
            config: Tool configuration
            description: Instance description
            metadata: Additional metadata
            
        Returns:
            Created tool instance details
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def create_tool_instance_operation():
            data = {
                'tool_id': tool_id,
                'name': name,
                'config': config
            }
            
            if description:
                data['description'] = description
            
            if metadata:
                data['metadata'] = metadata
            
            return self.post('/tool-instances', data=data)

        try:
            return await retry_with_backoff(
                operation=create_tool_instance_operation,
                policy=retry_policy,
                operation_name="create_tool_instance"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to create tool instance after multiple retries: {e}")
            raise
    
    async def update_tool_instance(
        self,
        instance_id: Union[str, int],
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing tool instance.
        
        Args:
            instance_id: Tool instance ID
            name: New name
            config: Updated configuration
            status: New status
            description: New description
            metadata: Updated metadata
            
        Returns:
            Updated tool instance details
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def update_tool_instance_operation():
            data = {}
            
            if name:
                data['name'] = name
            
            if config:
                data['config'] = config
            
            if status:
                data['status'] = status
            
            if description:
                data['description'] = description
            
            if metadata:
                data['metadata'] = metadata
            
            return self.put(f'/tool-instances/{instance_id}', data=data)

        try:
            return await retry_with_backoff(
                operation=update_tool_instance_operation,
                policy=retry_policy,
                operation_name="update_tool_instance"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to update tool instance after multiple retries: {e}")
            raise
    
    async def delete_tool_instance(self, instance_id: Union[str, int]) -> Dict[str, Any]:
        """
        Delete a tool instance.
        
        Args:
            instance_id: Tool instance ID
            
        Returns:
            Response data
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=2,  # Fewer retries for deletion operations
            base_delay=1.0,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def delete_tool_instance_operation():
            return self.delete(f'/tool-instances/{instance_id}')

        try:
            return await retry_with_backoff(
                operation=delete_tool_instance_operation,
                policy=retry_policy,
                operation_name="delete_tool_instance"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to delete tool instance after multiple retries: {e}")
            raise
    
    def get_tool_instance(self, instance_id: Union[str, int]) -> Dict[str, Any]:
        """
        Get details for a specific tool instance.
        
        Args:
            instance_id: Tool instance ID
            
        Returns:
            Tool instance details
        """
        return self.get(f'/tool-instances/{instance_id}')
    
    def get_tool_instances(
        self,
        tool_id: Optional[Union[str, int]] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Get a list of tool instances.
        
        Args:
            tool_id: Filter by tool ID
            status: Filter by status
            page: Page number
            per_page: Items per page
            
        Returns:
            Dict containing tool instances and pagination info
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        
        if tool_id:
            params['tool_id'] = tool_id
        
        if status:
            params['status'] = status
        
        return self.get('/tool-instances', params=params)
    
    async def execute_tool(
        self,
        instance_id: Union[str, int],
        action: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool instance with the provided parameters.
        
        Args:
            instance_id: Tool instance ID
            action: Action to perform
            parameters: Parameters for the action
            context: Additional context for the execution
            
        Returns:
            Tool execution result
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def execute_tool_operation():
            data = {
                'action': action,
                'parameters': parameters
            }
            
            if context:
                data['context'] = context
            
            return self.post(f'/tool-instances/{instance_id}/execute', data=data)

        try:
            return await retry_with_backoff(
                operation=execute_tool_operation,
                policy=retry_policy,
                operation_name="execute_tool"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to execute tool after multiple retries: {e}")
            raise
    
    async def get_tool_schema(self, tool_id: Union[str, int]) -> Dict[str, Any]:
        """
        Get the configuration schema for a specific tool.
        
        Args:
            tool_id: Tool ID
            
        Returns:
            Tool configuration schema
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=2,
            base_delay=0.5,
            max_delay=2.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def get_schema_operation():
            return self.get(f'/tools/{tool_id}/schema')

        try:
            return await retry_with_backoff(
                operation=get_schema_operation,
                policy=retry_policy,
                operation_name="get_tool_schema"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to get tool schema after multiple retries: {e}")
            raise
    
    async def validate_tool_config(
        self,
        tool_id: Union[str, int],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a tool configuration against its schema.
        
        Args:
            tool_id: Tool ID
            config: Tool configuration to validate
            
        Returns:
            Validation result
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=2,
            base_delay=0.5,
            max_delay=2.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def validate_config_operation():
            return self.post(f'/tools/{tool_id}/validate', data={'config': config})

        try:
            return await retry_with_backoff(
                operation=validate_config_operation,
                policy=retry_policy,
                operation_name="validate_tool_config"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to validate tool config after multiple retries: {e}")
            raise
