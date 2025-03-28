"""
Agent Task Execution Workflow implementation.

This module implements the workflow for executing tasks with agents,
coordinating between multiple services.
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from ...models.api import (
    WorkflowRequest, WorkflowType, AgentExecutionPlan, 
    ServiceType, AgentExecutionStep
)
from ...exceptions import (
    ServiceNotFoundError, WorkflowError, ServiceConnectionError
)
from ..discovery.service import ServiceDiscovery
from ..communication.client import ServiceClient


class AgentTaskExecutionWorkflow:
    """
    Agent Task Execution Workflow implementation.
    
    This workflow coordinates the execution of tasks by agents,
    involving the Planning System, Agent Orchestrator, and Tool Integration services.
    """
    
    def __init__(
        self,
        service_discovery: ServiceDiscovery,
        service_client: ServiceClient,
        logger: Optional[logging.Logger] = None,
        polling_interval: int = 2
    ):
        """
        Initialize the agent task execution workflow.
        
        Args:
            service_discovery: Service discovery instance
            service_client: Service client instance
            logger: Logger instance (optional)
            polling_interval: Interval for polling execution status in seconds
        """
        self.service_discovery = service_discovery
        self.service_client = service_client
        self.logger = logger or logging.getLogger("workflow.agent_task_execution")
        self.polling_interval = polling_interval
    
    async def execute(self, request: WorkflowRequest) -> Dict[str, Any]:
        """
        Execute the agent task execution workflow.
        
        This workflow coordinates:
        1. Getting an execution plan from the Planning System
        2. Starting the execution in the Agent Orchestrator
        3. Monitoring the execution progress
        4. Handling any tool executions with the Tool Integration service
        5. Collecting and returning the results
        
        Args:
            request: Workflow request data
            
        Returns:
            Workflow result
            
        Raises:
            WorkflowError: If the workflow execution fails
        """
        task_id = request.data.get("task_id")
        agent_id = request.data.get("agent_id")
        parameters = request.data.get("parameters", {})
        
        if not task_id or not agent_id:
            raise WorkflowError("Task ID and Agent ID are required")
        
        self.logger.info(f"Starting agent task execution workflow for task {task_id} with agent {agent_id}")
        
        try:
            # Step 1: Get execution plan from Planning System
            execution_plan = await self._get_execution_plan(task_id, agent_id, parameters)
            self.logger.info(f"Received execution plan with {len(execution_plan.steps)} steps")
            
            # Step 2: Start execution in Agent Orchestrator
            execution_id = await self._start_agent_execution(agent_id, task_id, execution_plan, parameters)
            self.logger.info(f"Started execution with ID {execution_id}")
            
            # Step 3: Monitor execution progress
            result = await self._monitor_execution(execution_id)
            self.logger.info(f"Execution completed with status: {result.get('status')}")
            
            return {
                "execution_id": execution_id,
                "task_id": task_id,
                "agent_id": agent_id,
                "status": result.get("status"),
                "result": result.get("result"),
                "steps": result.get("steps", []),
                "metrics": result.get("metrics", {}),
                "execution_time": result.get("execution_time")
            }
            
        except ServiceNotFoundError as e:
            self.logger.error(f"Service not found: {str(e)}")
            raise WorkflowError(f"Service not found: {str(e)}")
        except ServiceConnectionError as e:
            self.logger.error(f"Service connection error: {str(e)}")
            raise WorkflowError(f"Service connection error: {str(e)}")
        except Exception as e:
            self.logger.exception(f"Error in agent task execution workflow: {str(e)}")
            raise WorkflowError(f"Workflow error: {str(e)}")
    
    async def _get_execution_plan(self, task_id: str, agent_id: str, parameters: Dict[str, Any]) -> AgentExecutionPlan:
        """
        Get execution plan from Planning System.
        
        Args:
            task_id: Task ID
            agent_id: Agent ID
            parameters: Task parameters
            
        Returns:
            Execution plan
            
        Raises:
            WorkflowError: If the execution plan cannot be obtained
        """
        try:
            # Get Planning System service
            planning_service = await self.service_discovery.get_service_by_type(ServiceType.PLANNING_SYSTEM)
            
            # Request execution plan
            response = await self.service_client.post(
                service=planning_service,
                endpoint="/plans/execution-plan",
                data={
                    "task_id": task_id,
                    "agent_id": agent_id,
                    "parameters": parameters
                }
            )
            
            # Parse response
            if not response or "plan" not in response:
                raise WorkflowError("Invalid response from Planning System")
            
            return AgentExecutionPlan(**response["plan"])
            
        except Exception as e:
            self.logger.error(f"Error getting execution plan: {str(e)}")
            raise WorkflowError(f"Failed to get execution plan: {str(e)}")
    
    async def _start_agent_execution(
        self, 
        agent_id: str, 
        task_id: str, 
        plan: AgentExecutionPlan,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Start agent execution in Agent Orchestrator.
        
        Args:
            agent_id: Agent ID
            task_id: Task ID
            plan: Execution plan
            parameters: Task parameters
            
        Returns:
            Execution ID
            
        Raises:
            WorkflowError: If the execution cannot be started
        """
        try:
            # Get Agent Orchestrator service
            orchestrator_service = await self.service_discovery.get_service_by_type(ServiceType.AGENT_ORCHESTRATOR)
            
            # Start execution
            response = await self.service_client.post(
                service=orchestrator_service,
                endpoint="/executions",
                data={
                    "agent_id": agent_id,
                    "task_id": task_id,
                    "execution_plan": plan.dict(),
                    "parameters": parameters
                }
            )
            
            # Parse response
            if not response or "execution_id" not in response:
                raise WorkflowError("Invalid response from Agent Orchestrator")
            
            return response["execution_id"]
            
        except Exception as e:
            self.logger.error(f"Error starting agent execution: {str(e)}")
            raise WorkflowError(f"Failed to start agent execution: {str(e)}")
    
    async def _monitor_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        Monitor execution progress.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Execution result
            
        Raises:
            WorkflowError: If the execution monitoring fails
        """
        try:
            # Get Agent Orchestrator service
            orchestrator_service = await self.service_discovery.get_service_by_type(ServiceType.AGENT_ORCHESTRATOR)
            
            # Poll for status until completion
            terminal_statuses = ["COMPLETED", "FAILED", "CANCELED"]
            
            while True:
                # Get execution status
                response = await self.service_client.get(
                    service=orchestrator_service,
                    endpoint=f"/executions/{execution_id}"
                )
                
                # Check if execution is complete
                status = response.get("status")
                if status in terminal_statuses:
                    return response
                
                self.logger.debug(f"Execution status: {status}, waiting...")
                
                # Wait before checking again
                await asyncio.sleep(self.polling_interval)
                
        except Exception as e:
            self.logger.error(f"Error monitoring execution: {str(e)}")
            raise WorkflowError(f"Failed to monitor execution: {str(e)}")
