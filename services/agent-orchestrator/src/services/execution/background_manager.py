"""
Background task manager component for the Execution service.

This module handles managing background tasks for executions.
"""

import logging
import asyncio
from typing import Dict, Optional, Callable, Coroutine, Any
from uuid import UUID

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    """
    Manages background tasks for executions.
    """
    def __init__(self):
        """
        Initialize the background task manager.
        """
        self._running_tasks: Dict[UUID, asyncio.Task] = {}
    
    def start_task(
        self,
        execution_id: UUID,
        coro: Coroutine
    ) -> asyncio.Task:
        """
        Start a background task.
        
        Args:
            execution_id: Execution ID
            coro: Coroutine to run as background task
            
        Returns:
            asyncio.Task: Created task
        """
        # Create task
        task = asyncio.create_task(coro)
        
        # Store in running tasks
        self._running_tasks[execution_id] = task
        
        # Add done callback to clean up task
        task.add_done_callback(lambda _: self._cleanup_task(execution_id))
        
        logger.debug(f"Started background task for execution {execution_id}")
        return task
    
    async def cancel_task(self, execution_id: UUID) -> None:
        """
        Cancel a background task.
        
        Args:
            execution_id: Execution ID
        """
        task = self.get_task(execution_id)
        
        if task and not task.done():
            # Cancel task
            logger.info(f"Cancelling background task for execution {execution_id}")
            task.cancel()
            
            try:
                # Wait for task to be cancelled
                await task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Error cancelling task for execution {execution_id}: {str(e)}")
            finally:
                # Make sure task is removed
                self.clear_task(execution_id)
    
    def get_task(self, execution_id: UUID) -> Optional[asyncio.Task]:
        """
        Get a background task.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Optional[asyncio.Task]: Task if found, None otherwise
        """
        return self._running_tasks.get(execution_id)
    
    def clear_task(self, execution_id: UUID) -> None:
        """
        Clear a background task reference.
        
        Args:
            execution_id: Execution ID
        """
        if execution_id in self._running_tasks:
            del self._running_tasks[execution_id]
            logger.debug(f"Cleared background task for execution {execution_id}")
    
    def _cleanup_task(self, execution_id: UUID) -> None:
        """
        Clean up task when it's done.
        
        Args:
            execution_id: Execution ID
        """
        task = self._running_tasks.get(execution_id)
        
        if task:
            # Check for exception
            if task.done() and not task.cancelled():
                exception = task.exception()
                if exception:
                    logger.error(f"Task for execution {execution_id} failed with exception: {str(exception)}")
            
            # Remove task
            self.clear_task(execution_id)
    
    async def cancel_all_tasks(self) -> None:
        """
        Cancel all running tasks.
        
        This is useful for cleanup during shutdown.
        """
        # Make a copy of the keys since we'll be modifying the dictionary
        execution_ids = list(self._running_tasks.keys())
        
        # Cancel all tasks
        for execution_id in execution_ids:
            await self.cancel_task(execution_id)
        
        logger.info(f"Cancelled all background tasks ({len(execution_ids)} tasks)")
