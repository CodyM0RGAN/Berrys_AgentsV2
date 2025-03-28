"""
Project Planning Workflow implementation.

This module implements the workflow for project planning,
coordinating between multiple services to create comprehensive project plans.
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from ...models.api import (
    WorkflowRequest, WorkflowType, ServiceType
)
from ...exceptions import (
    ServiceNotFoundError, WorkflowError, ServiceConnectionError
)
from ..discovery.service import ServiceDiscovery
from ..communication.client import ServiceClient


class ProjectPlanningWorkflow:
    """
    Project Planning Workflow implementation.
    
    This workflow coordinates the planning of projects,
    involving the Planning System, Agent Orchestrator, and Project Coordinator services.
    """
    
    def __init__(
        self,
        service_discovery: ServiceDiscovery,
        service_client: ServiceClient,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the project planning workflow.
        
        Args:
            service_discovery: Service discovery instance
            service_client: Service client instance
            logger: Logger instance (optional)
        """
        self.service_discovery = service_discovery
        self.service_client = service_client
        self.logger = logger or logging.getLogger("workflow.project_planning")
    
    async def execute(self, request: WorkflowRequest) -> Dict[str, Any]:
        """
        Execute the project planning workflow.
        
        This workflow coordinates:
        1. Getting project details from Project Coordinator
        2. Generating strategic plan with Planning System
        3. Generating tactical plan with task breakdown
        4. Creating required agents with Agent Orchestrator
        5. Assigning tasks to agents
        6. Updating project with planning results
        
        Args:
            request: Workflow request data
            
        Returns:
            Workflow result
            
        Raises:
            WorkflowError: If the workflow execution fails
        """
        project_id = request.data.get("project_id")
        
        if not project_id:
            raise WorkflowError("Project ID is required")
        
        self.logger.info(f"Starting project planning workflow for project {project_id}")
        
        try:
            # Step 1: Get project details
            project = await self._get_project_details(project_id)
            self.logger.info(f"Retrieved project details for {project_id}")
            
            # Step 2: Generate strategic plan
            strategic_plan = await self._generate_strategic_plan(project)
            self.logger.info(f"Generated strategic plan for project {project_id}")
            
            # Step 3: Generate tactical plan
            tactical_plan = await self._generate_tactical_plan(project, strategic_plan)
            self.logger.info(f"Generated tactical plan with {len(tactical_plan.get('tasks', []))} tasks")
            
            # Step 4: Create required agents
            agents = await self._create_required_agents(project, tactical_plan)
            self.logger.info(f"Created {len(agents)} agents for project {project_id}")
            
            # Step 5: Assign tasks to agents
            assignments = await self._assign_tasks(tactical_plan, agents)
            self.logger.info(f"Assigned {len(assignments)} tasks to agents")
            
            # Step 6: Update project with planning results
            result = await self._update_project(project_id, {
                "strategic_plan": strategic_plan,
                "tactical_plan": tactical_plan,
                "agents": agents,
                "task_assignments": assignments
            })
            
            self.logger.info(f"Project planning completed for project {project_id}")
            
            return {
                "project_id": project_id,
                "strategic_plan": strategic_plan,
                "tactical_plan": tactical_plan,
                "agents": agents,
                "task_assignments": assignments
            }
            
        except ServiceNotFoundError as e:
            self.logger.error(f"Service not found: {str(e)}")
            raise WorkflowError(f"Service not found: {str(e)}")
        except ServiceConnectionError as e:
            self.logger.error(f"Service connection error: {str(e)}")
            raise WorkflowError(f"Service connection error: {str(e)}")
        except Exception as e:
            self.logger.exception(f"Error in project planning workflow: {str(e)}")
            raise WorkflowError(f"Workflow error: {str(e)}")
    
    async def _get_project_details(self, project_id: str) -> Dict[str, Any]:
        """
        Get project details from Project Coordinator.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project details
        """
        # Get Project Coordinator service
        coordinator_service = await self.service_discovery.get_service_by_type(ServiceType.PROJECT_COORDINATOR)
        
        # Get project details
        response = await self.service_client.get(
            service=coordinator_service,
            endpoint=f"/projects/{project_id}"
        )
        
        if not response:
            raise WorkflowError(f"Project {project_id} not found")
        
        return response
    
    async def _generate_strategic_plan(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate strategic plan with Planning System.
        
        Args:
            project: Project details
            
        Returns:
            Strategic plan
        """
        # Get Planning System service
        planning_service = await self.service_discovery.get_service_by_type(ServiceType.PLANNING_SYSTEM)
        
        # Generate strategic plan
        response = await self.service_client.post(
            service=planning_service,
            endpoint="/plans/strategic",
            data={
                "project_id": project["id"],
                "project_details": project,
                "options": {
                    "include_resource_allocation": True,
                    "include_timeline": True,
                    "optimization_target": "balanced"  # Can be "time", "cost", "quality", "balanced"
                }
            }
        )
        
        if not response or "plan" not in response:
            raise WorkflowError("Failed to generate strategic plan")
        
        return response["plan"]
    
    async def _generate_tactical_plan(
        self, 
        project: Dict[str, Any], 
        strategic_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate tactical plan with Planning System.
        
        Args:
            project: Project details
            strategic_plan: Strategic plan
            
        Returns:
            Tactical plan
        """
        # Get Planning System service
        planning_service = await self.service_discovery.get_service_by_type(ServiceType.PLANNING_SYSTEM)
        
        # Generate tactical plan
        response = await self.service_client.post(
            service=planning_service,
            endpoint="/plans/tactical",
            data={
                "project_id": project["id"],
                "strategic_plan": strategic_plan,
                "options": {
                    "detail_level": "high",
                    "include_dependencies": True,
                    "include_resource_requirements": True
                }
            }
        )
        
        if not response or "plan" not in response:
            raise WorkflowError("Failed to generate tactical plan")
        
        return response["plan"]
    
    async def _create_required_agents(
        self, 
        project: Dict[str, Any], 
        tactical_plan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Create required agents with Agent Orchestrator.
        
        Args:
            project: Project details
            tactical_plan: Tactical plan
            
        Returns:
            List of created agents
        """
        # Get Agent Orchestrator service
        orchestrator_service = await self.service_discovery.get_service_by_type(ServiceType.AGENT_ORCHESTRATOR)
        
        # Determine required agents based on the tactical plan
        required_agent_types = set()
        for task in tactical_plan.get("tasks", []):
            if "required_agent_type" in task:
                required_agent_types.add(task["required_agent_type"])
        
        # Create agents for each required type
        agents = []
        for agent_type in required_agent_types:
            response = await self.service_client.post(
                service=orchestrator_service,
                endpoint="/agents",
                data={
                    "project_id": project["id"],
                    "name": f"{agent_type.capitalize()} Agent for {project['name']}",
                    "type": agent_type,
                    "configuration": {
                        "project_context": project["description"],
                        "specialization": agent_type
                    }
                }
            )
            
            if response and "id" in response:
                agents.append(response)
        
        return agents
    
    async def _assign_tasks(
        self, 
        tactical_plan: Dict[str, Any], 
        agents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Assign tasks to agents.
        
        Args:
            tactical_plan: Tactical plan
            agents: List of created agents
            
        Returns:
            List of task assignments
        """
        # Create a map of agent types to agent IDs
        agent_map = {}
        for agent in agents:
            agent_type = agent["type"]
            if agent_type not in agent_map:
                agent_map[agent_type] = []
            agent_map[agent_type].append(agent["id"])
        
        # Assign tasks to agents
        assignments = []
        for task in tactical_plan.get("tasks", []):
            if "required_agent_type" in task:
                agent_type = task["required_agent_type"]
                if agent_type in agent_map and agent_map[agent_type]:
                    # Simple round-robin assignment within agent type
                    agent_id = agent_map[agent_type][0]
                    agent_map[agent_type].append(agent_map[agent_type].pop(0))
                    
                    assignments.append({
                        "task_id": task["id"],
                        "agent_id": agent_id,
                        "assigned_at": datetime.now().isoformat(),
                        "status": "ASSIGNED"
                    })
        
        return assignments
    
    async def _update_project(
        self, 
        project_id: str, 
        planning_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update project with planning results.
        
        Args:
            project_id: Project ID
            planning_results: Planning results
            
        Returns:
            Updated project
        """
        # Get Project Coordinator service
        coordinator_service = await self.service_discovery.get_service_by_type(ServiceType.PROJECT_COORDINATOR)
        
        # Update project
        response = await self.service_client.put(
            service=coordinator_service,
            endpoint=f"/projects/{project_id}/planning",
            data=planning_results
        )
        
        if not response:
            raise WorkflowError(f"Failed to update project {project_id}")
        
        return response
