"""
State manager component for the Execution service.

This module handles execution state transitions and validation.
"""

import logging
from typing import Dict, Any, Optional, Set
from uuid import UUID
from datetime import datetime

from ...models.internal import AgentExecutionModel
from ...models.api import ExecutionState, ExecutionStatusChangeRequest
from ...exceptions import (
    ExecutionNotFoundError,
    InvalidExecutionStateError,
    ConcurrentModificationError,
    DatabaseError
)

from .repository import ExecutionRepository
from .event_emitter import ExecutionEventEmitter

logger = logging.getLogger(__name__)

class ExecutionStateManager:
    """
    Manages execution state transitions ensuring validation rules are followed.
    """
    # Define valid state transitions
    VALID_TRANSITIONS: Dict[ExecutionState, Set[ExecutionState]] = {
        ExecutionState.QUEUED: {ExecutionState.PREPARING, ExecutionState.CANCELLED},
        ExecutionState.PREPARING: {ExecutionState.RUNNING, ExecutionState.FAILED, ExecutionState.CANCELLED},
        ExecutionState.RUNNING: {ExecutionState.PAUSED, ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.CANCELLED},
        ExecutionState.PAUSED: {ExecutionState.RUNNING, ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.CANCELLED},
        ExecutionState.COMPLETED: set(),  # Terminal state
        ExecutionState.FAILED: {ExecutionState.QUEUED},  # Can only transition to QUEUED for retry
        ExecutionState.CANCELLED: set(),  # Terminal state
    }
    
    def __init__(
        self,
        repository: ExecutionRepository,
        event_emitter: ExecutionEventEmitter
    ):
        """
        Initialize the state manager.
        
        Args:
            repository: Repository for data access
            event_emitter: Event emitter for publishing events
        """
        self.repository = repository
        self.event_emitter = event_emitter
    
    def validate_transition(
        self,
        current_state: ExecutionState,
        target_state: ExecutionState
    ) -> bool:
        """
        Validate state transition.
        
        Args:
            current_state: Current state
            target_state: Target state
            
        Returns:
            bool: True if valid, False otherwise
        """
        if current_state == target_state:
            return True  # Always allow transitions to the same state
            
        valid_targets = self.VALID_TRANSITIONS.get(current_state, set())
        return target_state in valid_targets
    
    async def change_state(
        self,
        execution_id: UUID,
        status_change: ExecutionStatusChangeRequest
    ) -> AgentExecutionModel:
        """
        Change execution state.
        
        Args:
            execution_id: Execution ID
            status_change: Status change request
            
        Returns:
            AgentExecutionModel: Updated execution
            
        Raises:
            ExecutionNotFoundError: If execution not found
            InvalidExecutionStateError: If state transition is invalid
            ConcurrentModificationError: If execution was modified concurrently
            DatabaseError: If database operation fails
        """
        # Get the execution
        execution = await self.repository.get_by_id(execution_id)
        
        if not execution:
            raise ExecutionNotFoundError(execution_id)
        
        current_state = execution.state
        target_state = status_change.target_state
        
        # Validate the state transition
        if not self.validate_transition(current_state, target_state):
            raise InvalidExecutionStateError(
                current_state=current_state.value,
                target_state=target_state.value,
            )
        
        # Prepare timestamp updates
        timestamps = {}
        if target_state == ExecutionState.RUNNING and not execution.started_at:
            timestamps["started_at"] = datetime.utcnow()
            
        if target_state in (ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.CANCELLED):
            timestamps["completed_at"] = datetime.utcnow()
        
        # Update execution state with optimistic locking
        updated_execution = await self.repository.update_state(
            execution_id=execution_id,
            state=target_state,
            timestamps=timestamps,
            optimistic_locking_condition=current_state
        )
        
        if not updated_execution:
            raise ConcurrentModificationError(execution_id)
        
        # Create state history entry
        await self.repository.create_state_history(
            execution_id=execution_id,
            previous_state=current_state,
            new_state=target_state,
            reason=status_change.reason
        )
        
        # Emit state change event
        await self.event_emitter.emit_state_changed(
            execution=updated_execution,
            previous_state=current_state,
            reason=status_change.reason
        )
        
        # Handle state-specific side effects
        await self.handle_state_side_effects(
            execution=updated_execution,
            previous_state=current_state,
            new_state=target_state
        )
        
        return updated_execution
    
    async def handle_state_side_effects(
        self,
        execution: AgentExecutionModel,
        previous_state: ExecutionState,
        new_state: ExecutionState
    ) -> None:
        """
        Handle state-specific side effects.
        
        Args:
            execution: Execution model
            previous_state: Previous state
            new_state: New state
        """
        # Handle terminal states
        if new_state in [ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.CANCELLED]:
            await self.event_emitter.emit_execution_completed(execution)
