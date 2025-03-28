"""
Progress tracker component for the Execution service.

This module handles tracking and updating execution progress.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from ...models.internal import AgentExecutionModel
from ...models.api import ExecutionProgressUpdate, ExecutionState
from ...exceptions import (
    ExecutionNotFoundError,
    InvalidExecutionStateError,
    DatabaseError
)

from .repository import ExecutionRepository
from .event_emitter import ExecutionEventEmitter

logger = logging.getLogger(__name__)

class ProgressTracker:
    """
    Tracks and reports execution progress.
    """
    def __init__(
        self,
        repository: ExecutionRepository,
        event_emitter: ExecutionEventEmitter
    ):
        """
        Initialize the progress tracker.
        
        Args:
            repository: Repository for data access
            event_emitter: Event emitter for publishing events
        """
        self.repository = repository
        self.event_emitter = event_emitter
    
    async def update_progress(
        self,
        execution_id: UUID,
        progress_update: ExecutionProgressUpdate
    ) -> AgentExecutionModel:
        """
        Update execution progress.
        
        Args:
            execution_id: Execution ID
            progress_update: Progress update
            
        Returns:
            AgentExecutionModel: Updated execution
            
        Raises:
            ExecutionNotFoundError: If execution not found
            InvalidExecutionStateError: If execution is not in a state that allows progress updates
            DatabaseError: If database operation fails
        """
        # Get the execution to check its state
        execution = await self.repository.get_by_id(execution_id)
        
        if not execution:
            raise ExecutionNotFoundError(execution_id)
        
        # Validate the execution is in a state that allows progress updates
        if execution.state not in [ExecutionState.PREPARING, ExecutionState.RUNNING]:
            raise InvalidExecutionStateError(
                current_state=execution.state.value,
                target_state=execution.state.value,
                message=f"Cannot update progress for execution in {execution.state.value} state. Must be in PREPARING or RUNNING state."
            )
        
        # Prepare context update for steps information
        context_update = None
        if any([
            progress_update.completed_steps is not None,
            progress_update.current_step is not None,
            progress_update.remaining_steps is not None
        ]):
            steps_info = {
                "completed_steps": progress_update.completed_steps or [],
                "current_step": progress_update.current_step,
                "remaining_steps": progress_update.remaining_steps or [],
            }
            context_update = {"steps": steps_info}
        
        # Update execution progress in the repository
        updated_execution = await self.repository.update_progress(
            execution_id=execution_id,
            percentage=progress_update.progress_percentage,
            message=progress_update.status_message,
            context_update=context_update
        )
        
        if not updated_execution:
            raise ExecutionNotFoundError(execution_id)
        
        # Emit progress updated event
        await self.event_emitter.emit_progress_updated(updated_execution)
        
        return updated_execution
    
    async def set_initial_progress(
        self,
        execution_id: UUID,
        message: str = "Initializing"
    ) -> AgentExecutionModel:
        """
        Set initial progress for an execution.
        
        Args:
            execution_id: Execution ID
            message: Status message
            
        Returns:
            AgentExecutionModel: Updated execution
            
        Raises:
            ExecutionNotFoundError: If execution not found
            InvalidExecutionStateError: If execution is not in a state that allows progress updates
            DatabaseError: If database operation fails
        """
        progress_update = ExecutionProgressUpdate(
            progress_percentage=0.0,
            status_message=message,
            completed_steps=[],
            current_step="Initialize",
            remaining_steps=[]
        )
        
        return await self.update_progress(execution_id, progress_update)
    
    async def mark_complete(
        self,
        execution_id: UUID,
        message: str = "Task completed successfully"
    ) -> AgentExecutionModel:
        """
        Mark progress as complete.
        
        Args:
            execution_id: Execution ID
            message: Status message
            
        Returns:
            AgentExecutionModel: Updated execution
            
        Raises:
            ExecutionNotFoundError: If execution not found
            InvalidExecutionStateError: If execution is not in a state that allows progress updates
            DatabaseError: If database operation fails
        """
        # Get current execution to preserve steps
        execution = await self.repository.get_by_id(execution_id)
        
        if not execution:
            raise ExecutionNotFoundError(execution_id)
        
        # Extract completed steps from context
        completed_steps = []
        current_step = None
        if execution.context and "steps" in execution.context:
            steps = execution.context["steps"]
            completed_steps = list(steps.get("completed_steps", []))
            current_step = steps.get("current_step")
            
            # Add current step to completed if it exists
            if current_step and current_step not in completed_steps:
                completed_steps.append(current_step)
        
        # Create progress update
        progress_update = ExecutionProgressUpdate(
            progress_percentage=100.0,
            status_message=message,
            completed_steps=completed_steps,
            current_step=None,
            remaining_steps=[]
        )
        
        return await self.update_progress(execution_id, progress_update)
