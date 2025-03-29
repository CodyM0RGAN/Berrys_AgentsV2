"""
Synchronous adapters for async API clients.

This module provides synchronous wrappers around the asynchronous methods
in the API clients, making them usable in synchronous Flask applications.
"""
import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

from shared.utils.src.clients.agent_orchestrator import AgentOrchestratorClient
from shared.utils.src.clients.model_orchestration import ModelOrchestrationClient
from shared.utils.src.clients.project_coordinator import ProjectCoordinatorClient
from shared.utils.src.clients.planning_system import PlanningSystemClient
from shared.utils.src.clients.service_integration import ServiceIntegrationClient
from shared.utils.src.clients.tool_integration import ToolIntegrationClient

# Set up logger
logger = logging.getLogger(__name__)

# Type variable for method return types
T = TypeVar('T')

def sync_wrapper(async_func: Callable[..., T]) -> Callable[..., T]:
    """
    Wrap an async function to make it synchronous.
    
    Args:
        async_func: Async function to wrap
        
    Returns:
        Synchronous wrapper function
    """
    @wraps(async_func)
    def sync_func(*args: Any, **kwargs: Any) -> T:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If there is no event loop in the current thread, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        except Exception as e:
            logger.error(f"Error in synchronous wrapper for {async_func.__name__}: {str(e)}")
            raise
    
    return sync_func

# Enhanced Project Coordinator Client with sync methods
class SyncProjectCoordinatorClient(ProjectCoordinatorClient):
    """Synchronous wrapper for ProjectCoordinatorClient."""
    
    def __init__(self, base_url: str, timeout: Optional[int] = None):
        """Initialize SyncProjectCoordinatorClient."""
        super().__init__(base_url, timeout)
        
        # Wrap async methods with sync wrappers
        self.create_project_sync = sync_wrapper(self.create_project)
        self.update_project_sync = sync_wrapper(self.update_project)
        self.delete_project_sync = sync_wrapper(self.delete_project)
        self.assign_agent_to_project_sync = sync_wrapper(self.assign_agent_to_project)
        self.remove_agent_from_project_sync = sync_wrapper(self.remove_agent_from_project)
        self.send_chat_message_sync = sync_wrapper(self.send_chat_message)

# Enhanced Agent Orchestrator Client with sync methods
class SyncAgentOrchestratorClient(AgentOrchestratorClient):
    """Synchronous wrapper for AgentOrchestratorClient."""
    
    def __init__(self, base_url: str, timeout: Optional[int] = None):
        """Initialize SyncAgentOrchestratorClient."""
        super().__init__(base_url, timeout)
        
        # Wrap async methods with sync wrappers
        self.create_agent_sync = sync_wrapper(self.create_agent)
        self.update_agent_sync = sync_wrapper(self.update_agent)
        self.delete_agent_sync = sync_wrapper(self.delete_agent)
        self.assign_task_sync = sync_wrapper(self.assign_task)

# Enhanced Model Orchestration Client with sync methods
class SyncModelOrchestrationClient(ModelOrchestrationClient):
    """Synchronous wrapper for ModelOrchestrationClient."""
    
    def __init__(self, base_url: str, timeout: Optional[int] = None):
        """Initialize SyncModelOrchestrationClient."""
        super().__init__(base_url, timeout)
        
        # Wrap async methods with sync wrappers
        self.generate_text_sync = sync_wrapper(self.generate_text)
        self.generate_chat_completion_sync = sync_wrapper(self.generate_chat_completion)
        self.generate_embeddings_sync = sync_wrapper(self.generate_embeddings)

# Enhanced Planning System Client with sync methods
class SyncPlanningSystemClient(PlanningSystemClient):
    """Synchronous wrapper for PlanningSystemClient."""
    
    def __init__(self, base_url: str, timeout: Optional[int] = None):
        """Initialize SyncPlanningSystemClient."""
        super().__init__(base_url, timeout)
        
        # Wrap async methods with sync wrappers
        self.create_plan_sync = sync_wrapper(self.create_plan)
        self.update_plan_sync = sync_wrapper(self.update_plan)
        self.delete_plan_sync = sync_wrapper(self.delete_plan)
        self.create_task_sync = sync_wrapper(self.create_task)
        self.update_task_sync = sync_wrapper(self.update_task)
        self.delete_task_sync = sync_wrapper(self.delete_task)
        self.generate_plan_sync = sync_wrapper(self.generate_plan)
        self.generate_tasks_sync = sync_wrapper(self.generate_tasks)

# Enhanced Service Integration Client with sync methods
class SyncServiceIntegrationClient(ServiceIntegrationClient):
    """Synchronous wrapper for ServiceIntegrationClient."""
    
    def __init__(self, base_url: str, timeout: Optional[int] = None):
        """Initialize SyncServiceIntegrationClient."""
        super().__init__(base_url, timeout)
        
        # Wrap async methods with sync wrappers
        self.register_service_sync = sync_wrapper(self.register_service)
        self.update_service_sync = sync_wrapper(self.update_service)
        self.deregister_service_sync = sync_wrapper(self.deregister_service)
        self.create_integration_sync = sync_wrapper(self.create_integration)
        self.update_integration_sync = sync_wrapper(self.update_integration)
        self.delete_integration_sync = sync_wrapper(self.delete_integration)
        self.execute_integration_sync = sync_wrapper(self.execute_integration)
        self.get_service_health_sync = sync_wrapper(self.get_service_health)

# Enhanced Tool Integration Client with sync methods
class SyncToolIntegrationClient(ToolIntegrationClient):
    """Synchronous wrapper for ToolIntegrationClient."""
    
    def __init__(self, base_url: str, timeout: Optional[int] = None):
        """Initialize SyncToolIntegrationClient."""
        super().__init__(base_url, timeout)
        
        # Wrap async methods with sync wrappers
        self.register_tool_sync = sync_wrapper(self.register_tool)
        self.update_tool_sync = sync_wrapper(self.update_tool)
        self.deregister_tool_sync = sync_wrapper(self.deregister_tool)
        self.create_tool_instance_sync = sync_wrapper(self.create_tool_instance)
        self.update_tool_instance_sync = sync_wrapper(self.update_tool_instance)
        self.delete_tool_instance_sync = sync_wrapper(self.delete_tool_instance)
        self.execute_tool_sync = sync_wrapper(self.execute_tool)
        self.get_tool_schema_sync = sync_wrapper(self.get_tool_schema)
        self.validate_tool_config_sync = sync_wrapper(self.validate_tool_config)
