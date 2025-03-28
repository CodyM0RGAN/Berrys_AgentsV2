"""
Planning System API client for interacting with the Planning System service.
"""
import logging
from typing import Any, Dict, List, Optional, Union, Awaitable

from shared.utils.src.clients.base import BaseAPIClient

# Set up logger
logger = logging.getLogger(__name__)

class PlanningSystemClient(BaseAPIClient):
    """Client for interacting with the Planning System API."""
    
    async def create_plan(
        self, 
        project_id: Union[str, int],
        name: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new plan for a project.
        
        Args:
            project_id: Project ID
            name: Plan name
            description: Plan description
            metadata: Additional metadata
            
        Returns:
            Created plan details
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def create_plan_operation():
            data = {
                'project_id': project_id,
                'name': name,
                'description': description
            }
            
            if metadata:
                data['metadata'] = metadata
            
            return self.post('/plans', data=data)

        try:
            return await retry_with_backoff(
                operation=create_plan_operation,
                policy=retry_policy,
                operation_name="create_plan"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to create plan after multiple retries: {e}")
            raise
    
    async def update_plan(
        self,
        plan_id: Union[str, int],
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing plan.
        
        Args:
            plan_id: Plan ID
            name: New name
            description: New description
            status: New status
            metadata: Updated metadata
            
        Returns:
            Updated plan details
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def update_plan_operation():
            data = {}
            
            if name:
                data['name'] = name
            
            if description:
                data['description'] = description
            
            if status:
                data['status'] = status
            
            if metadata:
                data['metadata'] = metadata
            
            return self.put(f'/plans/{plan_id}', data=data)

        try:
            return await retry_with_backoff(
                operation=update_plan_operation,
                policy=retry_policy,
                operation_name="update_plan"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to update plan after multiple retries: {e}")
            raise
    
    async def delete_plan(self, plan_id: Union[str, int]) -> Dict[str, Any]:
        """
        Delete a plan.
        
        Args:
            plan_id: Plan ID
            
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

        async def delete_plan_operation():
            return self.delete(f'/plans/{plan_id}')

        try:
            return await retry_with_backoff(
                operation=delete_plan_operation,
                policy=retry_policy,
                operation_name="delete_plan"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to delete plan after multiple retries: {e}")
            raise
    
    def get_plan(self, plan_id: Union[str, int]) -> Dict[str, Any]:
        """
        Get details for a specific plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            Plan details
        """
        return self.get(f'/plans/{plan_id}')
    
    def get_plans(
        self,
        project_id: Optional[Union[str, int]] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Get a list of plans.
        
        Args:
            project_id: Filter by project ID
            status: Filter by status
            page: Page number
            per_page: Items per page
            
        Returns:
            Dict containing plans and pagination info
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        
        if project_id:
            params['project_id'] = project_id
        
        if status:
            params['status'] = status
        
        return self.get('/plans', params=params)
    
    async def create_task(
        self,
        plan_id: Union[str, int],
        name: str,
        description: str,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
        assigned_to: Optional[Union[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new task for a plan.
        
        Args:
            plan_id: Plan ID
            name: Task name
            description: Task description
            priority: Task priority
            due_date: Due date (ISO format)
            assigned_to: Agent ID to assign the task to
            metadata: Additional metadata
            
        Returns:
            Created task details
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def create_task_operation():
            data = {
                'plan_id': plan_id,
                'name': name,
                'description': description
            }
            
            if priority:
                data['priority'] = priority
            
            if due_date:
                data['due_date'] = due_date
            
            if assigned_to:
                data['assigned_to'] = assigned_to
            
            if metadata:
                data['metadata'] = metadata
            
            return self.post('/tasks', data=data)

        try:
            return await retry_with_backoff(
                operation=create_task_operation,
                policy=retry_policy,
                operation_name="create_task"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to create task after multiple retries: {e}")
            raise
    
    async def update_task(
        self,
        task_id: Union[str, int],
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
        assigned_to: Optional[Union[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing task.
        
        Args:
            task_id: Task ID
            name: New name
            description: New description
            status: New status
            priority: New priority
            due_date: New due date (ISO format)
            assigned_to: New agent ID to assign the task to
            metadata: Updated metadata
            
        Returns:
            Updated task details
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def update_task_operation():
            data = {}
            
            if name:
                data['name'] = name
            
            if description:
                data['description'] = description
            
            if status:
                data['status'] = status
            
            if priority:
                data['priority'] = priority
            
            if due_date:
                data['due_date'] = due_date
            
            if assigned_to:
                data['assigned_to'] = assigned_to
            
            if metadata:
                data['metadata'] = metadata
            
            return self.put(f'/tasks/{task_id}', data=data)

        try:
            return await retry_with_backoff(
                operation=update_task_operation,
                policy=retry_policy,
                operation_name="update_task"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to update task after multiple retries: {e}")
            raise
    
    async def delete_task(self, task_id: Union[str, int]) -> Dict[str, Any]:
        """
        Delete a task.
        
        Args:
            task_id: Task ID
            
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

        async def delete_task_operation():
            return self.delete(f'/tasks/{task_id}')

        try:
            return await retry_with_backoff(
                operation=delete_task_operation,
                policy=retry_policy,
                operation_name="delete_task"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to delete task after multiple retries: {e}")
            raise
    
    def get_task(self, task_id: Union[str, int]) -> Dict[str, Any]:
        """
        Get details for a specific task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task details
        """
        return self.get(f'/tasks/{task_id}')
    
    def get_tasks(
        self,
        plan_id: Optional[Union[str, int]] = None,
        status: Optional[str] = None,
        assigned_to: Optional[Union[str, int]] = None,
        priority: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Get a list of tasks.
        
        Args:
            plan_id: Filter by plan ID
            status: Filter by status
            assigned_to: Filter by assigned agent ID
            priority: Filter by priority
            page: Page number
            per_page: Items per page
            
        Returns:
            Dict containing tasks and pagination info
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        
        if plan_id:
            params['plan_id'] = plan_id
        
        if status:
            params['status'] = status
        
        if assigned_to:
            params['assigned_to'] = assigned_to
        
        if priority:
            params['priority'] = priority
        
        return self.get('/tasks', params=params)
    
    async def generate_plan(
        self,
        project_id: Union[str, int],
        description: str,
        constraints: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a plan for a project using AI.
        
        Args:
            project_id: Project ID
            description: Project description or planning prompt
            constraints: List of constraints to consider
            metadata: Additional metadata
            
        Returns:
            Generated plan details
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def generate_plan_operation():
            data = {
                'project_id': project_id,
                'description': description
            }
            
            if constraints:
                data['constraints'] = constraints
            
            if metadata:
                data['metadata'] = metadata
            
            return self.post('/generate/plan', data=data)

        try:
            return await retry_with_backoff(
                operation=generate_plan_operation,
                policy=retry_policy,
                operation_name="generate_plan"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to generate plan after multiple retries: {e}")
            raise
    
    async def generate_tasks(
        self,
        plan_id: Union[str, int],
        description: Optional[str] = None,
        constraints: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate tasks for a plan using AI.
        
        Args:
            plan_id: Plan ID
            description: Additional context for task generation
            constraints: List of constraints to consider
            metadata: Additional metadata
            
        Returns:
            Generated tasks details
        """
        from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
        from shared.utils.src.exceptions import ServiceUnavailableError

        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def generate_tasks_operation():
            data = {
                'plan_id': plan_id
            }
            
            if description:
                data['description'] = description
            
            if constraints:
                data['constraints'] = constraints
            
            if metadata:
                data['metadata'] = metadata
            
            return self.post('/generate/tasks', data=data)

        try:
            return await retry_with_backoff(
                operation=generate_tasks_operation,
                policy=retry_policy,
                operation_name="generate_tasks"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to generate tasks after multiple retries: {e}")
            raise
