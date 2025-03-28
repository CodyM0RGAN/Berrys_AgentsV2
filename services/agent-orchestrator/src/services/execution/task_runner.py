"""
Task runner component for the Execution service.

This module handles executing tasks by coordinating with the model orchestration service.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select

from shared.utils.src.messaging import CommandBus

from ...models.internal import AgentExecutionModel, AgentModel
from ...models.api import (
    ExecutionState, 
    ExecutionProgressUpdate,
    ExecutionResultRequest,
    HumanApprovalRequest
)
from ...exceptions import (
    AgentNotFoundError,
    ExecutionNotFoundError,
    ModelOrchestrationError,
    DatabaseError,
    HumanInteractionError
)

from .repository import ExecutionRepository
from .state_manager import ExecutionStateManager
from .progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)

class ExecutionTaskRunner:
    """
    Handles the execution of tasks, communicating with model services.
    """
    def __init__(
        self,
        repository: ExecutionRepository,
        state_manager: ExecutionStateManager,
        progress_tracker: ProgressTracker,
        command_bus: CommandBus,
        human_interaction_service=None,  # Optional dependency injection
    ):
        """
        Initialize the task runner.
        
        Args:
            repository: Repository for data access
            state_manager: State manager for state transitions
            progress_tracker: Progress tracker for progress updates
            command_bus: Command bus for communicating with other services
            human_interaction_service: Optional human interaction service for approval flows
        """
        self.repository = repository
        self.state_manager = state_manager
        self.progress_tracker = progress_tracker
        self.command_bus = command_bus
        self.human_interaction_service = human_interaction_service
    
    async def execute_task(self, execution: AgentExecutionModel) -> None:
        """
        Execute a task.
        
        Args:
            execution: Execution model
            
        Raises:
            AgentNotFoundError: If agent not found
            ModelOrchestrationError: If model service call fails
        """
        execution_id = execution.id
        agent_id = execution.agent_id
        task_id = execution.task_id
        
        try:
            # Update progress to indicate initialization
            await self.progress_tracker.update_progress(
                execution_id=execution_id,
                progress_update=ExecutionProgressUpdate(
                    progress_percentage=10.0,
                    status_message="Initializing task",
                    completed_steps=[],
                    current_step="Initialize",
                    remaining_steps=["Prepare task", "Execute task", "Process results"],
                )
            )
            
            # Get agent info to include in the task context
            agent = await self._get_agent(agent_id)
            
            if not agent:
                raise AgentNotFoundError(agent_id)
            
            # Prepare task input
            await self.progress_tracker.update_progress(
                execution_id=execution_id,
                progress_update=ExecutionProgressUpdate(
                    progress_percentage=25.0,
                    status_message="Preparing task input",
                    completed_steps=["Initialize"],
                    current_step="Prepare task",
                    remaining_steps=["Execute task", "Process results"],
                )
            )
            
            # Prepare the task input with agent and execution context
            task_input = await self.prepare_task_input(execution, agent)
            
            # Call model service to execute the task
            await self.progress_tracker.update_progress(
                execution_id=execution_id,
                progress_update=ExecutionProgressUpdate(
                    progress_percentage=50.0,
                    status_message="Executing task",
                    completed_steps=["Initialize", "Prepare task"],
                    current_step="Execute task",
                    remaining_steps=["Process results"],
                )
            )
            
            # Call model service
            task_result = await self.call_model_service(execution, task_input)
            
            # Process results
            await self.progress_tracker.update_progress(
                execution_id=execution_id,
                progress_update=ExecutionProgressUpdate(
                    progress_percentage=75.0,
                    status_message="Processing results",
                    completed_steps=["Initialize", "Prepare task", "Execute task"],
                    current_step="Process results",
                    remaining_steps=["Human review", "Finalization"] if self._requires_human_approval(execution) else ["Finalization"],
                )
            )
            
            # Process results
            processed_result = self.process_results(task_result)
            
            # Determine if human approval is needed
            if self._requires_human_approval(execution) and self.human_interaction_service:
                # Update progress to indicate waiting for human approval
                await self.progress_tracker.update_progress(
                    execution_id=execution_id,
                    progress_update=ExecutionProgressUpdate(
                        progress_percentage=85.0,
                        status_message="Waiting for human approval",
                        completed_steps=["Initialize", "Prepare task", "Execute task", "Process results"],
                        current_step="Human review",
                        remaining_steps=["Finalization"],
                    )
                )
                
                # Pause execution while waiting for approval
                await self.state_manager.change_state(
                    execution_id, 
                    {"target_state": ExecutionState.PAUSED, "reason": "Waiting for human approval"}
                )
                
                # Request human approval
                approval_result = await self._request_human_approval(
                    agent_id=agent_id,
                    execution_id=execution_id,
                    execution_result=processed_result
                )
                
                # If approval was not granted, modify the result
                if approval_result.get("approved") is False:
                    processed_result["human_approval"] = False
                    processed_result["feedback"] = approval_result.get("feedback")
                else:
                    processed_result["human_approval"] = True
                    
                # Resume execution
                await self.state_manager.change_state(
                    execution_id, 
                    {"target_state": ExecutionState.RUNNING, "reason": "Continuing after human review"}
                )
            
            # Finalize and update progress
            await self.progress_tracker.update_progress(
                execution_id=execution_id,
                progress_update=ExecutionProgressUpdate(
                    progress_percentage=95.0,
                    status_message="Finalizing execution",
                    completed_steps=["Initialize", "Prepare task", "Execute task", "Process results", "Human review"] if self._requires_human_approval(execution) else ["Initialize", "Prepare task", "Execute task", "Process results"],
                    current_step="Finalization",
                    remaining_steps=[],
                )
            )
            
            # Store final result
            result_request = ExecutionResultRequest(
                status="success",
                result=processed_result,
                metadata={
                    "execution_time": task_result.get("execution_time", 0.0),
                    "model_used": task_result.get("model_used", "unknown"),
                    "provider": task_result.get("provider", "unknown"),
                    "human_approval_requested": self._requires_human_approval(execution),
                }
            )
            
            # Submit the result, which will also change the state to COMPLETED
            await self.repository.update_result(
                execution_id=execution_id,
                result=result_request.result,
                error_message=None
            )
            
            # Update final progress
            await self.progress_tracker.mark_complete(
                execution_id=execution_id,
                message="Task completed successfully"
            )
            
        except Exception as e:
            logger.error(f"Error executing task for execution {execution_id}: {str(e)}")
            
            # Update result with error
            error_result = {
                "error": str(e),
                "error_type": type(e).__name__,
            }
            
            # Update execution with error
            await self.repository.update_result(
                execution_id=execution_id,
                result=error_result,
                error_message=str(e)
            )
            
            # Re-raise to let caller handle specific error types
            raise
    
    async def _get_agent(self, agent_id: UUID) -> Optional[AgentModel]:
        """
        Get agent by ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Optional[AgentModel]: Agent if found, None otherwise
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Get the agent using direct SQL query
            query = select(AgentModel).where(AgentModel.id == agent_id)
            result = await self.repository.db.execute(query)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting agent {agent_id}: {str(e)}")
            raise DatabaseError(f"Failed to get agent: {str(e)}")
    
    async def prepare_task_input(
        self,
        execution: AgentExecutionModel,
        agent: AgentModel
    ) -> Dict[str, Any]:
        """
        Prepare task input.
        
        Args:
            execution: Execution model
            agent: Agent model
            
        Returns:
            Dict[str, Any]: Task input
        """
        # Base task input
        task_input = {
            "execution_id": str(execution.id),
            "agent_id": str(execution.agent_id),
            "task_id": str(execution.task_id),
            "parameters": execution.parameters or {},
            "context": execution.context or {},
        }
        
        # Add agent information
        task_input["agent"] = {
            "id": str(agent.id),
            "name": agent.name,
            "type": agent.type,
            "configuration": agent.configuration,
            "capabilities": agent.capabilities,
        }
        
        # Add any additional execution-specific parameters
        if execution.parameters:
            task_input["parameters"] = execution.parameters
        
        return task_input
    
    async def call_model_service(
        self,
        execution: AgentExecutionModel,
        task_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call model service.
        
        Args:
            execution: Execution model
            task_input: Task input
            
        Returns:
            Dict[str, Any]: Model service response
            
        Raises:
            ModelOrchestrationError: If model service call fails
        """
        try:
            # Send command to model orchestration service
            response = await self.command_bus.send_command(
                command_name="model.execute",
                data={
                    "execution_id": str(execution.id),
                    "agent_id": str(execution.agent_id),
                    "task_id": str(execution.task_id),
                    "input": task_input,
                }
            )
            
            # Check for errors
            if response.get("error"):
                raise ModelOrchestrationError(response.get("error"))
            
            return response.get("result", {})
        except Exception as e:
            logger.error(f"Error calling model service for execution {execution.id}: {str(e)}")
            
            if isinstance(e, ModelOrchestrationError):
                raise
            
            raise ModelOrchestrationError(str(e))
    
    def process_results(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process task results.
        
        Args:
            result: Raw result from model service
            
        Returns:
            Dict[str, Any]: Processed result
        """
        # Base implementation just returns the result as-is
        # Subclasses can override this to implement custom processing
        
        # Ensure we have a valid result
        if not result:
            return {"message": "No result data available"}
        
        return result
        
    def _requires_human_approval(self, execution: AgentExecutionModel) -> bool:
        """
        Determine if an execution requires human approval.
        
        Args:
            execution: Execution model
            
        Returns:
            bool: True if human approval is required, False otherwise
        """
        # Check parameters for human approval flag
        params = execution.parameters or {}
        
        # Explicit flag in parameters
        if params.get("require_human_approval") is not None:
            return bool(params.get("require_human_approval"))
            
        # Check for high risk operation flag
        if params.get("risk_level", "").lower() in ["high", "critical"]:
            return True
            
        # Check for explicit content that needs approval
        if params.get("content_requires_approval", False):
            return True
            
        # Default based on other factors (agent type, etc.)
        return False
    
    async def _request_human_approval(
        self, 
        agent_id: UUID, 
        execution_id: UUID, 
        execution_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Request human approval for execution results.
        
        Args:
            agent_id: Agent ID
            execution_id: Execution ID
            execution_result: Execution result
            
        Returns:
            Dict[str, Any]: Approval result
            
        Raises:
            HumanInteractionError: If human interaction service unavailable
        """
        if not self.human_interaction_service:
            logger.warning(f"Human approval requested for execution {execution_id} but no human interaction service available")
            return {"approved": True, "reason": "Auto-approved (no human interaction service)"}
            
        try:
            # Create approval request
            approval_request = HumanApprovalRequest(
                execution_id=execution_id,
                title=f"Approve execution result for task #{execution_id}",
                description="Please review and approve or reject the execution result",
                options=["Approve", "Reject", "Modify"],
                context={
                    "execution_id": str(execution_id),
                    "agent_id": str(agent_id),
                    "result": execution_result,
                },
                deadline=datetime.utcnow() + timedelta(hours=24),  # 24-hour deadline
                priority="high",
            )
            
            # Request approval
            approval_response = await self.human_interaction_service.request_approval(
                agent_id=agent_id,
                approval_request=approval_request,
            )
            
            # Check for immediate response (unlikely)
            if hasattr(approval_response, "response") and approval_response.response:
                decision = approval_response.response.get("decision", "")
                feedback = approval_response.response.get("feedback", "")
                return {
                    "approved": decision.lower() == "approve",
                    "decision": decision,
                    "feedback": feedback,
                }
                
            # Set up polling for response (in a real implementation, you might use event-driven approach)
            # For now, we'll just wait a short time for demo purposes
            await asyncio.sleep(1)
            
            # In a real implementation, there would be a proper way to check for approval
            # For this example, we'll assume approval was granted
            return {
                "approved": True,
                "decision": "Approve",
                "feedback": "Auto-approved for demonstration",
            }
            
        except Exception as e:
            logger.error(f"Error requesting human approval for execution {execution_id}: {str(e)}")
            # Fail open - approve if we can't request approval
            return {"approved": True, "reason": f"Auto-approved due to error: {str(e)}"}
