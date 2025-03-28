"""
Main service module for the Execution service.

This module provides the facade service that coordinates all execution components.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from shared.utils.src.messaging import EventBus, CommandBus

from ...config import AgentOrchestratorConfig
from ...exceptions import (
    AgentNotFoundError,
    ExecutionNotFoundError,
    InvalidExecutionStateError,
    ConcurrentModificationError,
    DatabaseError,
    ModelOrchestrationError,
    HumanInteractionError,
)
from ...models.api import (
    ExecutionState,
    ExecutionStatusChangeRequest,
    ExecutionProgressUpdate,
    ExecutionResultRequest,
    ExecutionResponse,
)
from ...models.internal import (
    AgentModel,
    AgentExecutionModel,
    ExecutionStateModel,
)

from .repository import ExecutionRepository
from .state_manager import ExecutionStateManager
from .task_runner import ExecutionTaskRunner
from .progress_tracker import ProgressTracker
from .background_manager import BackgroundTaskManager
from .event_emitter import ExecutionEventEmitter
from ...services.human_interaction_service import HumanInteractionService

logger = logging.getLogger(__name__)

class ExecutionService:
    """
    Service for managing task executions.
    
    This is a facade service that coordinates between specialized components
    for different aspects of execution management.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        command_bus: CommandBus,
        settings: AgentOrchestratorConfig,
        human_interaction_service: Optional[HumanInteractionService] = None,
    ):
        """
        Initialize the execution service.
        
        Args:
            db: Database session
            event_bus: Event bus
            command_bus: Command bus
            settings: Application settings
            human_interaction_service: Optional human interaction service for approval flows
        """
        # Initialize components
        self.repository = ExecutionRepository(db)
        self.event_emitter = ExecutionEventEmitter(event_bus)
        self.state_manager = ExecutionStateManager(self.repository, self.event_emitter)
        self.progress_tracker = ProgressTracker(self.repository, self.event_emitter)
        self.background_manager = BackgroundTaskManager()
        self.task_runner = ExecutionTaskRunner(
            self.repository,
            self.state_manager,
            self.progress_tracker,
            command_bus,
            human_interaction_service
        )
        
        # Store dependencies
        self.db = db
        self.event_bus = event_bus
        self.command_bus = command_bus
        self.settings = settings
    
    async def get_execution(self, execution_id: UUID) -> Optional[AgentExecutionModel]:
        """
        Get an execution by ID.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Optional[AgentExecutionModel]: Execution if found, None otherwise
            
        Raises:
            DatabaseError: If database operation fails
        """
        return await self.repository.get_by_id(execution_id)
    
    async def list_executions(
        self,
        agent_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        state: Optional[ExecutionState] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[AgentExecutionModel], int]:
        """
        List executions with filtering and pagination.
        
        Args:
            agent_id: Filter by agent ID
            task_id: Filter by task ID
            state: Filter by state
            page: Page number
            page_size: Page size
            
        Returns:
            Tuple[List[AgentExecutionModel], int]: List of executions and total count
            
        Raises:
            DatabaseError: If database operation fails
        """
        filters = {}
        if agent_id:
            filters["agent_id"] = agent_id
        if task_id:
            filters["task_id"] = task_id
        if state:
            filters["state"] = state
            
        pagination = {
            "page": page,
            "page_size": page_size
        }
        
        return await self.repository.list_executions(filters, pagination)
    
    async def delete_execution(self, execution_id: UUID) -> None:
        """
        Delete an execution.
        
        Args:
            execution_id: Execution ID
            
        Raises:
            ExecutionNotFoundError: If execution not found
            DatabaseError: If database operation fails
        """
        # Get execution first to ensure it exists and to get data for event
        execution = await self.repository.get_by_id(execution_id)
        
        if not execution:
            raise ExecutionNotFoundError(execution_id)
        
        # Store execution data for event
        execution_data = {
            "execution_id": str(execution.id),
            "agent_id": str(execution.agent_id),
            "task_id": str(execution.task_id),
            "state": execution.state.value if execution.state else None,
        }
        
        # Cancel any running task
        await self.background_manager.cancel_task(execution_id)
        
        # Delete from repository
        success = await self.repository.delete_execution(execution_id)
        
        if not success:
            # This should not happen since we already checked existence, but just in case
            raise ExecutionNotFoundError(execution_id)
        
        # Emit deletion event
        await self.event_emitter.emit_execution_deleted(execution_data)
    
    async def change_execution_state(
        self,
        execution_id: UUID,
        status_change: ExecutionStatusChangeRequest,
    ) -> AgentExecutionModel:
        """
        Change an execution's state.
        
        Args:
            execution_id: Execution ID
            status_change: Status change request
            
        Returns:
            AgentExecutionModel: Updated execution model
            
        Raises:
            ExecutionNotFoundError: If execution not found
            InvalidExecutionStateError: If state transition is invalid
            ConcurrentModificationError: If execution was modified concurrently
            DatabaseError: If database operation fails
        """
        return await self.state_manager.change_state(execution_id, status_change)
    
    async def get_execution_state_history(
        self,
        execution_id: UUID,
        limit: int = 10,
    ) -> List[ExecutionStateModel]:
        """
        Get an execution's state history.
        
        Args:
            execution_id: Execution ID
            limit: Maximum number of history entries to return
            
        Returns:
            List[ExecutionStateModel]: Execution state history
            
        Raises:
            ExecutionNotFoundError: If execution not found
            DatabaseError: If database operation fails
        """
        # Check if execution exists
        execution = await self.repository.get_by_id(execution_id)
        
        if not execution:
            raise ExecutionNotFoundError(execution_id)
        
        # Get state history
        return await self.repository.get_state_history(execution_id, limit)
    
    async def update_progress(
        self,
        execution_id: UUID,
        progress_update: ExecutionProgressUpdate,
    ) -> AgentExecutionModel:
        """
        Update execution progress.
        
        Args:
            execution_id: Execution ID
            progress_update: Progress update
            
        Returns:
            AgentExecutionModel: Updated execution model
            
        Raises:
            ExecutionNotFoundError: If execution not found
            InvalidExecutionStateError: If execution is not in a state that allows progress updates
            DatabaseError: If database operation fails
        """
        return await self.progress_tracker.update_progress(execution_id, progress_update)
    
    async def submit_result(
        self,
        execution_id: UUID,
        result_request: ExecutionResultRequest,
    ) -> AgentExecutionModel:
        """
        Submit execution result.
        
        Args:
            execution_id: Execution ID
            result_request: Result request
            
        Returns:
            AgentExecutionModel: Updated execution model
            
        Raises:
            ExecutionNotFoundError: If execution not found
            InvalidExecutionStateError: If execution is not in a state that allows submitting results
            DatabaseError: If database operation fails
        """
        # Get the execution to check its state and update result
        execution = await self.repository.get_by_id(execution_id)
        
        if not execution:
            raise ExecutionNotFoundError(execution_id)
        
        # Validate the execution is in a state that allows submitting results
        if execution.state not in [ExecutionState.RUNNING, ExecutionState.PAUSED]:
            raise InvalidExecutionStateError(
                current_state=execution.state.value,
                target_state=execution.state.value,
                message=f"Cannot submit results for execution in {execution.state.value} state. Must be in RUNNING or PAUSED state."
            )
        
        # Update result
        await self.repository.update_result(
            execution_id=execution_id,
            result=result_request.result,
            error_message=None if result_request.status == "success" else result_request.result.get("error", "Execution failed")
        )
        
        # Update context with metadata if provided
        if result_request.metadata:
            execution = await self.repository.get_by_id(execution_id)
            context = execution.context or {}
            context["metadata"] = result_request.metadata
            
            # Update context directly since this doesn't have its own repository method
            execution.context = context
            await self.db.commit()
        
        # Change state based on status
        new_state = ExecutionState.COMPLETED if result_request.status == "success" else ExecutionState.FAILED
        
        status_change = ExecutionStatusChangeRequest(
            target_state=new_state,
            reason=f"Execution {result_request.status}",
        )
        
        # Change state (which will also save and emit events)
        return await self.state_manager.change_state(execution_id, status_change)
    
    async def start_execution(
        self,
        execution_id: UUID,
    ) -> AgentExecutionModel:
        """
        Start an execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            AgentExecutionModel: Updated execution model
            
        Raises:
            ExecutionNotFoundError: If execution not found
            InvalidExecutionStateError: If execution is not in a valid state to start
            DatabaseError: If database operation fails
        """
        # First move to PREPARING state
        status_change = ExecutionStatusChangeRequest(
            target_state=ExecutionState.PREPARING,
            reason="Preparing execution",
        )
        
        execution = await self.state_manager.change_state(execution_id, status_change)
        
        # Set initial progress
        await self.progress_tracker.set_initial_progress(execution_id)
        
        # Create and start background task
        execution_task_coro = self._handle_execution_task(execution_id)
        self.background_manager.start_task(execution_id, execution_task_coro)
        
        return execution
    
    async def pause_execution(
        self,
        execution_id: UUID,
        reason: Optional[str] = None,
    ) -> AgentExecutionModel:
        """
        Pause an execution.
        
        Args:
            execution_id: Execution ID
            reason: Reason for pausing
            
        Returns:
            AgentExecutionModel: Updated execution model
            
        Raises:
            ExecutionNotFoundError: If execution not found
            InvalidExecutionStateError: If execution is not in a valid state to pause
            DatabaseError: If database operation fails
        """
        status_change = ExecutionStatusChangeRequest(
            target_state=ExecutionState.PAUSED,
            reason=reason or "Execution paused",
        )
        
        return await self.state_manager.change_state(execution_id, status_change)
    
    async def resume_execution(
        self,
        execution_id: UUID,
    ) -> AgentExecutionModel:
        """
        Resume a paused execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            AgentExecutionModel: Updated execution model
            
        Raises:
            ExecutionNotFoundError: If execution not found
            InvalidExecutionStateError: If execution is not in a valid state to resume
            DatabaseError: If database operation fails
        """
        status_change = ExecutionStatusChangeRequest(
            target_state=ExecutionState.RUNNING,
            reason="Execution resumed",
        )
        
        return await self.state_manager.change_state(execution_id, status_change)
    
    async def complete_execution(
        self,
        execution_id: UUID,
        result: Dict[str, Any],
    ) -> AgentExecutionModel:
        """
        Complete an execution successfully.
        
        Args:
            execution_id: Execution ID
            result: Execution result
            
        Returns:
            AgentExecutionModel: Updated execution model
            
        Raises:
            ExecutionNotFoundError: If execution not found
            InvalidExecutionStateError: If execution is not in a valid state to complete
            DatabaseError: If database operation fails
        """
        result_request = ExecutionResultRequest(
            status="success",
            result=result,
        )
        
        return await self.submit_result(execution_id, result_request)
    
    async def fail_execution(
        self,
        execution_id: UUID,
        error_message: str,
    ) -> AgentExecutionModel:
        """
        Mark an execution as failed.
        
        Args:
            execution_id: Execution ID
            error_message: Error message
            
        Returns:
            AgentExecutionModel: Updated execution model
            
        Raises:
            ExecutionNotFoundError: If execution not found
            InvalidExecutionStateError: If execution is not in a valid state to fail
            DatabaseError: If database operation fails
        """
        result_request = ExecutionResultRequest(
            status="failure",
            result={"error": error_message},
        )
        
        return await self.submit_result(execution_id, result_request)
    
    async def cancel_execution(
        self,
        execution_id: UUID,
        reason: Optional[str] = None,
    ) -> AgentExecutionModel:
        """
        Cancel an execution.
        
        Args:
            execution_id: Execution ID
            reason: Reason for cancellation
            
        Returns:
            AgentExecutionModel: Updated execution model
            
        Raises:
            ExecutionNotFoundError: If execution not found
            DatabaseError: If database operation fails
        """
        # Cancel background task first
        await self.background_manager.cancel_task(execution_id)
        
        # Then update state
        status_change = ExecutionStatusChangeRequest(
            target_state=ExecutionState.CANCELLED,
            reason=reason or "Execution cancelled",
        )
        
        return await self.state_manager.change_state(execution_id, status_change)
    
    async def retry_execution(
        self,
        execution_id: UUID,
    ) -> AgentExecutionModel:
        """
        Retry a failed execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            AgentExecutionModel: Updated execution model
            
        Raises:
            ExecutionNotFoundError: If execution not found
            InvalidExecutionStateError: If execution is not in FAILED state
            DatabaseError: If database operation fails
        """
        # Get execution to check state and update retry count
        execution = await self.repository.get_by_id(execution_id)
        
        if not execution:
            raise ExecutionNotFoundError(execution_id)
        
        # Validate execution is in FAILED state
        if execution.state != ExecutionState.FAILED:
            raise InvalidExecutionStateError(
                current_state=execution.state.value,
                target_state=ExecutionState.QUEUED.value,
                message=f"Cannot retry execution in {execution.state.value} state. Must be in FAILED state."
            )
        
        # Increment retry count and clear error
        execution.retry_count = (execution.retry_count or 0) + 1
        execution.error_message = None
        await self.db.commit()
        
        # Reset to QUEUED state
        status_change = ExecutionStatusChangeRequest(
            target_state=ExecutionState.QUEUED,
            reason=f"Retrying execution (attempt {execution.retry_count})",
        )
        
        # Change state
        updated_execution = await self.state_manager.change_state(execution_id, status_change)
        
        # Start execution
        return await self.start_execution(execution_id)
    
    async def _handle_execution_task(self, execution_id: UUID) -> None:
        """
        Handle execution task in background.
        
        Args:
            execution_id: Execution ID
        """
        try:
            logger.info(f"Starting execution task for {execution_id}")
            
            # First update to RUNNING state
            status_change = ExecutionStatusChangeRequest(
                target_state=ExecutionState.RUNNING,
                reason="Execution started",
            )
            
            updated_execution = await self.state_manager.change_state(execution_id, status_change)
            
            # Execute task using task runner
            await self.task_runner.execute_task(updated_execution)
            
            # Task runner will handle state transitions and progress updates
            
        except asyncio.CancelledError:
            logger.info(f"Execution task cancelled for {execution_id}")
            raise
            
        except Exception as e:
            logger.error(f"Error in execution task for {execution_id}: {str(e)}")
            
            try:
                # Mark as failed if not already in a terminal state
                execution = await self.repository.get_by_id(execution_id)
                
                if execution and execution.state == ExecutionState.RUNNING:
                    await self.fail_execution(
                        execution_id=execution_id,
                        error_message=f"Execution failed: {str(e)}",
                    )
            except Exception as inner_e:
                logger.error(f"Error marking execution {execution_id} as failed: {str(inner_e)}")
