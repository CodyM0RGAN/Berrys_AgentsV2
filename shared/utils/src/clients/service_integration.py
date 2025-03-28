"""
Service Integration API client for interacting with the Service Integration service.
"""
import logging
from typing import Any, Dict, List, Optional, Union, Awaitable

from shared.utils.src.clients.base import BaseAPIClient

# Set up logger
logger = logging.getLogger(__name__)

class ServiceIntegrationClient(BaseAPIClient):
    """Client for interacting with the Service Integration API."""
    
    async def register_service(
        self,
        name: str,
        service_type: str,
        base_url: str,
        description: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register a new service with the Service Integration system.
        
        Args:
            name: Service name
            service_type: Type of service
            base_url: Base URL for the service
            description: Service description
            capabilities: List of service capabilities
            metadata: Additional metadata
            
        Returns:
            Registered service details
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def register_service_operation():
            data = {
                'name': name,
                'service_type': service_type,
                'base_url': base_url
            }
            
            if description:
                data['description'] = description
            
            if capabilities:
                data['capabilities'] = capabilities
            
            if metadata:
                data['metadata'] = metadata
            
            return self.post('/services', data=data)

        try:
            return await retry_with_backoff(
                operation=register_service_operation,
                policy=retry_policy,
                operation_name="register_service"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to register service after multiple retries: {e}")
            raise
    
    async def update_service(
        self,
        service_id: Union[str, int],
        name: Optional[str] = None,
        service_type: Optional[str] = None,
        base_url: Optional[str] = None,
        description: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing service.
        
        Args:
            service_id: Service ID
            name: New name
            service_type: New service type
            base_url: New base URL
            description: New description
            capabilities: Updated list of capabilities
            status: New status
            metadata: Updated metadata
            
        Returns:
            Updated service details
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def update_service_operation():
            data = {}
            
            if name:
                data['name'] = name
            
            if service_type:
                data['service_type'] = service_type
            
            if base_url:
                data['base_url'] = base_url
            
            if description:
                data['description'] = description
            
            if capabilities:
                data['capabilities'] = capabilities
            
            if status:
                data['status'] = status
            
            if metadata:
                data['metadata'] = metadata
            
            return self.put(f'/services/{service_id}', data=data)

        try:
            return await retry_with_backoff(
                operation=update_service_operation,
                policy=retry_policy,
                operation_name="update_service"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to update service after multiple retries: {e}")
            raise
    
    async def deregister_service(self, service_id: Union[str, int]) -> Dict[str, Any]:
        """
        Deregister a service.
        
        Args:
            service_id: Service ID
            
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

        async def deregister_service_operation():
            return self.delete(f'/services/{service_id}')

        try:
            return await retry_with_backoff(
                operation=deregister_service_operation,
                policy=retry_policy,
                operation_name="deregister_service"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to deregister service after multiple retries: {e}")
            raise
    
    def get_service(self, service_id: Union[str, int]) -> Dict[str, Any]:
        """
        Get details for a specific service.
        
        Args:
            service_id: Service ID
            
        Returns:
            Service details
        """
        return self.get(f'/services/{service_id}')
    
    def get_services(
        self,
        service_type: Optional[str] = None,
        status: Optional[str] = None,
        capability: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Get a list of services.
        
        Args:
            service_type: Filter by service type
            status: Filter by status
            capability: Filter by capability
            page: Page number
            per_page: Items per page
            
        Returns:
            Dict containing services and pagination info
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        
        if service_type:
            params['service_type'] = service_type
        
        if status:
            params['status'] = status
        
        if capability:
            params['capability'] = capability
        
        return self.get('/services', params=params)
    
    async def create_integration(
        self,
        name: str,
        source_service_id: Union[str, int],
        target_service_id: Union[str, int],
        integration_type: str,
        config: Dict[str, Any],
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new integration between services.
        
        Args:
            name: Integration name
            source_service_id: Source service ID
            target_service_id: Target service ID
            integration_type: Type of integration
            config: Integration configuration
            description: Integration description
            metadata: Additional metadata
            
        Returns:
            Created integration details
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def create_integration_operation():
            data = {
                'name': name,
                'source_service_id': source_service_id,
                'target_service_id': target_service_id,
                'integration_type': integration_type,
                'config': config
            }
            
            if description:
                data['description'] = description
            
            if metadata:
                data['metadata'] = metadata
            
            return self.post('/integrations', data=data)

        try:
            return await retry_with_backoff(
                operation=create_integration_operation,
                policy=retry_policy,
                operation_name="create_integration"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to create integration after multiple retries: {e}")
            raise
    
    async def update_integration(
        self,
        integration_id: Union[str, int],
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing integration.
        
        Args:
            integration_id: Integration ID
            name: New name
            config: Updated configuration
            status: New status
            description: New description
            metadata: Updated metadata
            
        Returns:
            Updated integration details
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def update_integration_operation():
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
            
            return self.put(f'/integrations/{integration_id}', data=data)

        try:
            return await retry_with_backoff(
                operation=update_integration_operation,
                policy=retry_policy,
                operation_name="update_integration"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to update integration after multiple retries: {e}")
            raise
    
    async def delete_integration(self, integration_id: Union[str, int]) -> Dict[str, Any]:
        """
        Delete an integration.
        
        Args:
            integration_id: Integration ID
            
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

        async def delete_integration_operation():
            return self.delete(f'/integrations/{integration_id}')

        try:
            return await retry_with_backoff(
                operation=delete_integration_operation,
                policy=retry_policy,
                operation_name="delete_integration"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to delete integration after multiple retries: {e}")
            raise
    
    def get_integration(self, integration_id: Union[str, int]) -> Dict[str, Any]:
        """
        Get details for a specific integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Integration details
        """
        return self.get(f'/integrations/{integration_id}')
    
    def get_integrations(
        self,
        source_service_id: Optional[Union[str, int]] = None,
        target_service_id: Optional[Union[str, int]] = None,
        integration_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Get a list of integrations.
        
        Args:
            source_service_id: Filter by source service ID
            target_service_id: Filter by target service ID
            integration_type: Filter by integration type
            status: Filter by status
            page: Page number
            per_page: Items per page
            
        Returns:
            Dict containing integrations and pagination info
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        
        if source_service_id:
            params['source_service_id'] = source_service_id
        
        if target_service_id:
            params['target_service_id'] = target_service_id
        
        if integration_type:
            params['integration_type'] = integration_type
        
        if status:
            params['status'] = status
        
        return self.get('/integrations', params=params)
    
    async def execute_integration(
        self,
        integration_id: Union[str, int],
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute an integration with the provided payload.
        
        Args:
            integration_id: Integration ID
            payload: Data to send through the integration
            context: Additional context for the execution
            
        Returns:
            Integration execution result
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def execute_integration_operation():
            data = {
                'payload': payload
            }
            
            if context:
                data['context'] = context
            
            return self.post(f'/integrations/{integration_id}/execute', data=data)

        try:
            return await retry_with_backoff(
                operation=execute_integration_operation,
                policy=retry_policy,
                operation_name="execute_integration"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to execute integration after multiple retries: {e}")
            raise
    
    async def get_service_health(self, service_id: Union[str, int]) -> Dict[str, Any]:
        """
        Get health status for a specific service.
        
        Args:
            service_id: Service ID
            
        Returns:
            Service health details
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=2,
            base_delay=0.5,
            max_delay=2.0,  # Shorter max delay for health checks
            retry_exceptions=[ServiceUnavailableError]
        )

        async def get_health_operation():
            return self.get(f'/services/{service_id}/health')

        try:
            return await retry_with_backoff(
                operation=get_health_operation,
                policy=retry_policy,
                operation_name="get_service_health"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to get service health after multiple retries: {e}")
            raise
