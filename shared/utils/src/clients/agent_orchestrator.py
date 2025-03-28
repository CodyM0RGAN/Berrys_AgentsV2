"""
Agent Orchestrator API client for interacting with the Agent Orchestrator service.

This module provides a client for interacting with the Agent Orchestrator service,
which manages agent lifecycle and coordination.
"""
import logging
from typing import Any, Dict, List, Optional, Union

from shared.utils.src.clients.base import BaseAPIClient
from shared.utils.src.retry import retry_with_backoff, RetryPolicy
from shared.utils.src.exceptions import ServiceUnavailableError, MaxRetriesExceededError

# Set up logger
logger = logging.getLogger(__name__)

class AgentOrchestratorClient(BaseAPIClient):
    """Client for interacting with the Agent Orchestrator API."""
    
    def get_agents(
        self, 
        search: Optional[str] = None, 
        status: Optional[str] = None,
        sort: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Get a list of agents.
        
        Args:
            search: Search query
            status: Filter by status
            sort: Sort order
            page: Page number
            per_page: Items per page
            
        Returns:
            Dict containing agents and pagination info
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        
        if search:
            params['search'] = search
        
        if status:
            params['status'] = status
        
        if sort:
            params['sort'] = sort
        
        return self.get('agents', params=params)
    
    def get_agent(self, agent_id: Union[str, int]) -> Dict[str, Any]:
        """
        Get details for a specific agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent details
        """
        return self.get(f'agents/{agent_id}')
    
    async def create_agent(
        self, 
        name: str, 
        description: str,
        agent_type: str,
        capabilities: List[str],
        status: str = 'INACTIVE',
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new agent.
        
        Args:
            name: Agent name
            description: Agent description
            agent_type: Type of agent
            capabilities: List of agent capabilities
            status: Initial status
            metadata: Additional metadata
            
        Returns:
            Created agent details
        """
        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def create_agent_operation():
            data = {
                'name': name,
                'description': description,
                'agent_type': agent_type,
                'capabilities': capabilities,
                'status': status
            }
            
            if metadata:
                data['metadata'] = metadata
            
            return self.post('agents', data=data)

        try:
            return await retry_with_backoff(
                operation=create_agent_operation,
                policy=retry_policy,
                operation_name="create_agent"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to create agent after multiple retries: {e}")
            raise
    
    async def update_agent(
        self, 
        agent_id: Union[str, int],
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing agent.
        
        Args:
            agent_id: Agent ID
            name: New name
            description: New description
            status: New status
            metadata: Updated metadata
            
        Returns:
            Updated agent details
        """
        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def update_agent_operation():
            data = {}
            
            if name:
                data['name'] = name
            
            if description:
                data['description'] = description
            
            if status:
                data['status'] = status
            
            if metadata:
                data['metadata'] = metadata
            
            return self.put(f'agents/{agent_id}', data=data)

        try:
            return await retry_with_backoff(
                operation=update_agent_operation,
                policy=retry_policy,
                operation_name="update_agent"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to update agent after multiple retries: {e}")
            raise
    
    async def delete_agent(self, agent_id: Union[str, int]) -> Dict[str, Any]:
        """
        Delete an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Response data
        """
        retry_policy = RetryPolicy(
            max_retries=2,  # Fewer retries for deletion operations
            base_delay=1.0,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def delete_agent_operation():
            return self.delete(f'agents/{agent_id}')

        try:
            return await retry_with_backoff(
                operation=delete_agent_operation,
                policy=retry_policy,
                operation_name="delete_agent"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to delete agent after multiple retries: {e}")
            raise
    
    def get_agent_tasks(
        self, 
        agent_id: Union[str, int],
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Get tasks for a specific agent.
        
        Args:
            agent_id: Agent ID
            status: Filter by status
            page: Page number
            per_page: Items per page
            
        Returns:
            Dict containing tasks and pagination info
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        
        if status:
            params['status'] = status
        
        return self.get(f'agents/{agent_id}/tasks', params=params)
    
    async def assign_task(
        self, 
        agent_id: Union[str, int],
        task_type: str,
        description: str,
        priority: str = 'MEDIUM',
        deadline: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Assign a task to an agent.
        
        Args:
            agent_id: Agent ID
            task_type: Type of task
            description: Task description
            priority: Task priority
            deadline: Task deadline
            metadata: Additional metadata
            
        Returns:
            Created task details
        """
        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def assign_task_operation():
            data = {
                'task_type': task_type,
                'description': description,
                'priority': priority
            }
            
            if deadline:
                data['deadline'] = deadline
            
            if metadata:
                data['metadata'] = metadata
            
            return self.post(f'agents/{agent_id}/tasks', data=data)

        try:
            return await retry_with_backoff(
                operation=assign_task_operation,
                policy=retry_policy,
                operation_name="assign_task"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to assign task after multiple retries: {e}")
            raise
    
    def get_available_agents(
        self, 
        capabilities: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get a list of available agents, optionally filtered by capabilities.
        
        Args:
            capabilities: Required capabilities
            limit: Maximum number of agents to return
            
        Returns:
            List of available agents
        """
        params = {
            'status': 'ACTIVE',
            'per_page': limit
        }
        
        if capabilities:
            params['capabilities'] = ','.join(capabilities)
        
        result = self.get('agents/available', params=params)
        return result.get('items', [])
