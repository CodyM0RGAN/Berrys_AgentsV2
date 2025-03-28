"""
Event emitter component for the Execution service.

This module handles publishing execution-related events.
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID

from shared.utils.src.messaging import EventBus

from ...models.internal import AgentExecutionModel
from ...models.api import ExecutionState

logger = logging.getLogger(__name__)

class ExecutionEventEmitter:
    """
    Handles publishing execution-related events.
    """
    def __init__(self, event_bus: EventBus):
        """
        Initialize the event emitter.
        
        Args:
            event_bus: Event bus for publishing events
        """
        self.event_bus = event_bus
        
    async def emit_state_changed(
        self,
        execution: AgentExecutionModel,
        previous_state: ExecutionState,
        reason: Optional[str] = None
    ) -> None:
        """
        Emit state changed event.
        
        Args:
            execution: Execution model
            previous_state: Previous state
            reason: Reason for state change
        """
        try:
            event_payload = {
                "execution_id": str(execution.id),
                "agent_id": str(execution.agent_id),
                "task_id": str(execution.task_id),
                "previous_state": previous_state.value,
                "new_state": execution.state.value,
                "reason": reason or "State changed",
            }
            
            await self.event_bus.publish_event("agent.execution.state_changed", event_payload)
            logger.debug(f"Published state change event for execution {execution.id}: {previous_state.value} -> {execution.state.value}")
        except Exception as e:
            logger.error(f"Error publishing state change event for execution {execution.id}: {str(e)}")
            # We don't re-raise the exception since event publishing shouldn't break the flow
        
    async def emit_progress_updated(self, execution: AgentExecutionModel) -> None:
        """
        Emit progress updated event.
        
        Args:
            execution: Execution model
        """
        try:
            event_payload = {
                "execution_id": str(execution.id),
                "agent_id": str(execution.agent_id),
                "task_id": str(execution.task_id),
                "progress_percentage": execution.progress_percentage,
                "status_message": execution.status_message,
            }
            
            # Add steps information if available in context
            if execution.context and "steps" in execution.context:
                steps = execution.context["steps"]
                if steps.get("completed_steps"):
                    event_payload["completed_steps"] = steps["completed_steps"]
                if steps.get("current_step"):
                    event_payload["current_step"] = steps["current_step"]
                if steps.get("remaining_steps"):
                    event_payload["remaining_steps"] = steps["remaining_steps"]
            
            await self.event_bus.publish_event("agent.execution.progress", event_payload)
            logger.debug(f"Published progress update event for execution {execution.id}: {execution.progress_percentage}%")
        except Exception as e:
            logger.error(f"Error publishing progress update event for execution {execution.id}: {str(e)}")
            # We don't re-raise the exception since event publishing shouldn't break the flow
        
    async def emit_execution_completed(self, execution: AgentExecutionModel) -> None:
        """
        Emit execution completed event.
        
        Args:
            execution: Execution model
        """
        try:
            # Only emit for terminal states
            if execution.state not in [
                ExecutionState.COMPLETED,
                ExecutionState.FAILED,
                ExecutionState.CANCELLED
            ]:
                logger.warning(f"Attempted to emit completion event for non-terminal state: {execution.state}")
                return
                
            event_payload = {
                "execution_id": str(execution.id),
                "agent_id": str(execution.agent_id),
                "task_id": str(execution.task_id),
                "state": execution.state.value,
                "result": execution.result,
                "error_message": execution.error_message,
            }
            
            # Add metadata if available in context
            if execution.context and "metadata" in execution.context:
                event_payload["metadata"] = execution.context["metadata"]
            
            await self.event_bus.publish_event("agent.execution.completed", event_payload)
            logger.debug(f"Published execution completed event for execution {execution.id} with state {execution.state.value}")
        except Exception as e:
            logger.error(f"Error publishing execution completed event for execution {execution.id}: {str(e)}")
            # We don't re-raise the exception since event publishing shouldn't break the flow
            
    async def emit_execution_deleted(self, execution_data: Dict[str, Any]) -> None:
        """
        Emit execution deleted event.
        
        Args:
            execution_data: Data about the deleted execution
        """
        try:
            await self.event_bus.publish_event("agent.execution.deleted", execution_data)
            logger.debug(f"Published execution deleted event for execution {execution_data.get('execution_id')}")
        except Exception as e:
            logger.error(f"Error publishing execution deleted event: {str(e)}")
            # We don't re-raise the exception since event publishing shouldn't break the flow
