"""
Project Coordinator API client for interacting with the Project Coordinator service.

This module provides a client for interacting with the Project Coordinator service,
which manages project lifecycle and coordination.
"""
import logging
from typing import Any, Dict, List, Optional, Union

from shared.utils.src.clients.base import BaseAPIClient
from shared.utils.src.retry import retry_with_backoff, RetryPolicy
from shared.utils.src.exceptions import ServiceUnavailableError, MaxRetriesExceededError

# Set up logger
logger = logging.getLogger(__name__)

class ProjectCoordinatorClient(BaseAPIClient):
    """Client for interacting with the Project Coordinator API."""
    
    def get_projects(
        self, 
        search: Optional[str] = None, 
        status: Optional[str] = None,
        sort: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Get a list of projects.
        
        Args:
            search: Search query
            status: Filter by status
            sort: Sort order
            page: Page number
            per_page: Items per page
            
        Returns:
            Dict containing projects and pagination info
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
        
        return self.get('/projects', params=params)
    
    def get_project(self, project_id: Union[str, int]) -> Dict[str, Any]:
        """
        Get details for a specific project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project details
        """
        return self.get(f'/projects/{project_id}')
    
    async def create_project(
        self, 
        name: str, 
        description: str,
        status: str = 'PLANNING',
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new project.
        
        Args:
            name: Project name
            description: Project description
            metadata: Additional metadata

        Returns:
            Created project details
        """
        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def create_project_operation():
            data = {
                'name': name,
                'description': description,
                # Removing the status field to allow the database default to apply and avoid constraint violations
            }

            if metadata:
                data['metadata'] = metadata

            return self.post('/projects', data=data)

        try:
            return await retry_with_backoff(
                operation=create_project_operation,
                policy=retry_policy,
                operation_name="create_project"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to create project after multiple retries: {e}")
            raise

    async def update_project(
        self, 
        project_id: Union[str, int],
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing project.
        
        Args:
            project_id: Project ID
            name: New name
            description: New description
            status: New status
            metadata: Updated metadata
            
        Returns:
            Updated project details
        """
        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def update_project_operation():
            data = {}
            
            if name:
                data['name'] = name
            
            if description:
                data['description'] = description
            
            if status:
                data['status'] = status
            
            if metadata:
                data['metadata'] = metadata
            
            return self.put(f'/projects/{project_id}', data=data)

        try:
            return await retry_with_backoff(
                operation=update_project_operation,
                policy=retry_policy,
                operation_name="update_project"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to update project after multiple retries: {e}")
            raise
    
    async def delete_project(self, project_id: Union[str, int]) -> Dict[str, Any]:
        """
        Delete a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Response data
        """
        retry_policy = RetryPolicy(
            max_retries=2,  # Fewer retries for deletion operations
            base_delay=1.0,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def delete_project_operation():
            return self.delete(f'/projects/{project_id}')

        try:
            return await retry_with_backoff(
                operation=delete_project_operation,
                policy=retry_policy,
                operation_name="delete_project"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to delete project after multiple retries: {e}")
            raise
    
    def get_project_tasks(self, project_id: Union[str, int]) -> List[Dict[str, Any]]:
        """
        Get tasks for a specific project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of tasks
        """
        result = self.get(f'/projects/{project_id}/tasks')
        return result.get('items', [])
    
    def get_project_agents(self, project_id: Union[str, int]) -> List[Dict[str, Any]]:
        """
        Get agents assigned to a specific project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of agents
        """
        result = self.get(f'/projects/{project_id}/agents')
        return result.get('items', [])
    
    def get_project_activities(
        self, 
        project_id: Union[str, int],
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Get activities for a specific project.
        
        Args:
            project_id: Project ID
            page: Page number
            per_page: Items per page
            
        Returns:
            Dict containing activities and pagination info
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        
        return self.get(f'/projects/{project_id}/activities', params=params)
    
    async def assign_agent_to_project(
        self, 
        project_id: Union[str, int],
        agent_id: Union[str, int],
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assign an agent to a project.
        
        Args:
            project_id: Project ID
            agent_id: Agent ID
            role: Agent role in the project
            
        Returns:
            Response data
        """
        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def assign_agent_operation():
            data = {
                'agent_id': agent_id
            }
            
            if role:
                data['role'] = role
            
            return self.post(f'/projects/{project_id}/agents', data=data)

        try:
            return await retry_with_backoff(
                operation=assign_agent_operation,
                policy=retry_policy,
                operation_name="assign_agent_to_project"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to assign agent to project after multiple retries: {e}")
            raise
    
    async def remove_agent_from_project(
        self, 
        project_id: Union[str, int],
        agent_id: Union[str, int]
    ) -> Dict[str, Any]:
        """
        Remove an agent from a project.
        
        Args:
            project_id: Project ID
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

        async def remove_agent_operation():
            return self.delete(f'/projects/{project_id}/agents/{agent_id}')

        try:
            return await retry_with_backoff(
                operation=remove_agent_operation,
                policy=retry_policy,
                operation_name="remove_agent_from_project"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to remove agent from project after multiple retries: {e}")
            raise
    
    async def send_chat_message(
        self,
        message: str,
        session_id: str,
        user_id: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send a chat message to the project coordinator.
        
        Args:
            message: Message content
            session_id: Chat session ID
            user_id: User ID
            history: Chat history
            
        Returns:
            Response data including bot response
        """
        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def send_chat_message_operation():
            data = {
                'message': message,
                'session_id': session_id
            }
            
            if user_id:
                data['user_id'] = user_id
            
            if history:
                data['history'] = history
            
            return self.post('/chat/message', data=data)

        try:
            return await retry_with_backoff(
                operation=send_chat_message_operation,
                policy=retry_policy,
                operation_name="send_chat_message"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to send chat message after multiple retries: {e}")
            raise
