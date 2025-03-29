"""
Example usage of cross-service validation utilities.

This file demonstrates how to use the cross-service validation utilities
to validate requests and responses that cross service boundaries.
"""

import asyncio
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from shared.models.src.enums import ProjectStatus
from shared.utils.src.cross_service_validation import (
    create_validators_from_model,
    validate_cross_service_request,
    validate_service_response,
    validate_project_id,
    validate_agent_id,
)


# Example Pydantic models for request and response validation
class ProjectCreateRequest(BaseModel):
    """Request model for creating a project."""
    
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    status: ProjectStatus = Field(default=ProjectStatus.PLANNING)
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class ProjectResponse(BaseModel):
    """Response model for project data."""
    
    id: str
    name: str
    description: str
    status: ProjectStatus
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = None


class AgentAssignmentRequest(BaseModel):
    """Request model for assigning an agent to a project."""
    
    project_id: str
    agent_id: str
    role: str = Field(..., min_length=3, max_length=50)


# Example client class with cross-service validation
class ProjectCoordinatorClient:
    """Client for interacting with the Project Coordinator service."""
    
    def __init__(self, base_url: str):
        """Initialize the client with the base URL."""
        self.base_url = base_url
    
    @validate_cross_service_request(
        target_service="project-coordinator",
        request_model=ProjectCreateRequest
    )
    async def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new project.
        
        Args:
            project_data: Project data to create
            
        Returns:
            Created project details
        """
        # In a real implementation, this would make an HTTP request
        # to the Project Coordinator service
        print(f"Creating project with data: {project_data}")
        
        # Simulate a response from the service
        return {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": project_data["name"],
            "description": project_data["description"],
            "status": project_data["status"].value if isinstance(project_data["status"], ProjectStatus) else project_data["status"],
            "created_at": "2025-03-27T12:00:00Z",
            "updated_at": "2025-03-27T12:00:00Z",
            "metadata": project_data.get("metadata")
        }
    
    @validate_service_response(
        source_service="project-coordinator",
        response_model=ProjectResponse
    )
    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get project details.
        
        Args:
            project_id: ID of the project to get
            
        Returns:
            Project details
        """
        # Validate the project_id
        validate_project_id(project_id)
        
        # In a real implementation, this would make an HTTP request
        # to the Project Coordinator service
        print(f"Getting project with ID: {project_id}")
        
        # Simulate a response from the service
        return {
            "id": project_id,
            "name": "Example Project",
            "description": "This is an example project",
            "status": ProjectStatus.PLANNING.value,
            "created_at": "2025-03-27T12:00:00Z",
            "updated_at": "2025-03-27T12:00:00Z",
            "metadata": {"key": "value"}
        }
    
    @validate_cross_service_request(
        target_service="project-coordinator",
        field_validators={
            "project_id": validate_project_id,
            "agent_id": validate_agent_id,
            "role": lambda value: value if isinstance(value, str) and 3 <= len(value) <= 50 else None
        }
    )
    async def assign_agent_to_project(
        self, project_id: str, agent_id: str, role: str
    ) -> Dict[str, Any]:
        """
        Assign an agent to a project.
        
        Args:
            project_id: ID of the project
            agent_id: ID of the agent to assign
            role: Role of the agent in the project
            
        Returns:
            Assignment details
        """
        # In a real implementation, this would make an HTTP request
        # to the Project Coordinator service
        print(f"Assigning agent {agent_id} to project {project_id} with role {role}")
        
        # Simulate a response from the service
        return {
            "project_id": project_id,
            "agent_id": agent_id,
            "role": role,
            "assigned_at": "2025-03-27T12:00:00Z"
        }


# Example usage with custom validators
class AgentOrchestratorClient:
    """Client for interacting with the Agent Orchestrator service."""
    
    def __init__(self, base_url: str):
        """Initialize the client with the base URL."""
        self.base_url = base_url
    
    @validate_cross_service_request(
        target_service="agent-orchestrator",
        request_model=AgentAssignmentRequest
    )
    async def assign_agent(self, assignment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assign an agent to a project.
        
        Args:
            assignment_data: Assignment data
            
        Returns:
            Assignment details
        """
        # In a real implementation, this would make an HTTP request
        # to the Agent Orchestrator service
        print(f"Assigning agent with data: {assignment_data}")
        
        # Simulate a response from the service
        return {
            "project_id": assignment_data["project_id"],
            "agent_id": assignment_data["agent_id"],
            "role": assignment_data["role"],
            "assigned_at": "2025-03-27T12:00:00Z"
        }


# Example usage with validators created from a model
def example_with_model_validators():
    """Example of using validators created from a model."""
    # Create validators from the ProjectCreateRequest model
    validators = create_validators_from_model(ProjectCreateRequest)
    
    # Use the validators to validate a dictionary
    project_data = {
        "name": "Example Project",
        "description": "This is an example project",
        "status": ProjectStatus.PLANNING,
        "metadata": {"key": "value"}
    }
    
    # Validate each field
    for field_name, validator in validators.items():
        if field_name in project_data:
            try:
                # Apply the validator
                validator(project_data[field_name])
                print(f"Field {field_name} is valid")
            except Exception as e:
                print(f"Field {field_name} is invalid: {str(e)}")


async def main():
    """Run the example."""
    # Create clients
    project_client = ProjectCoordinatorClient(base_url="http://localhost:8000/api")
    agent_client = AgentOrchestratorClient(base_url="http://localhost:8001/api")
    
    # Example 1: Create a project with valid data
    try:
        project = await project_client.create_project({
            "name": "Example Project",
            "description": "This is an example project",
            "status": ProjectStatus.PLANNING,
            "metadata": {"key": "value"}
        })
        print(f"Created project: {project}")
    except Exception as e:
        print(f"Failed to create project: {str(e)}")
    
    # Example 2: Create a project with invalid data
    try:
        project = await project_client.create_project({
            "name": "Ex",  # Too short
            "description": "Too short",  # Too short
            "status": "INVALID_STATUS",  # Invalid status
        })
        print(f"Created project: {project}")
    except Exception as e:
        print(f"Failed to create project: {str(e)}")
    
    # Example 3: Get a project
    try:
        project = await project_client.get_project("123e4567-e89b-12d3-a456-426614174000")
        print(f"Got project: {project}")
    except Exception as e:
        print(f"Failed to get project: {str(e)}")
    
    # Example 4: Assign an agent to a project
    try:
        assignment = await project_client.assign_agent_to_project(
            project_id="123e4567-e89b-12d3-a456-426614174000",
            agent_id="123e4567-e89b-12d3-a456-426614174001",
            role="Developer"
        )
        print(f"Assigned agent: {assignment}")
    except Exception as e:
        print(f"Failed to assign agent: {str(e)}")
    
    # Example 5: Assign an agent with a model
    try:
        assignment = await agent_client.assign_agent({
            "project_id": "123e4567-e89b-12d3-a456-426614174000",
            "agent_id": "123e4567-e89b-12d3-a456-426614174001",
            "role": "Developer"
        })
        print(f"Assigned agent: {assignment}")
    except Exception as e:
        print(f"Failed to assign agent: {str(e)}")
    
    # Example 6: Use validators created from a model
    example_with_model_validators()


if __name__ == "__main__":
    asyncio.run(main())
