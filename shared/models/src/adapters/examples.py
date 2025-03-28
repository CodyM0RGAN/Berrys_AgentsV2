"""
Usage examples for service boundary adapters.

This module provides examples of how to use the service boundary adapters
in real-world scenarios.
"""

import uuid
from typing import Dict, Any

from shared.models.src.adapters import (
    WebToCoordinatorAdapter,
    CoordinatorToAgentAdapter,
    AgentToModelAdapter
)
from shared.models.src.project import Project as ProjectPydantic
from shared.models.src.agent import Agent as AgentPydantic
from shared.models.src.task import Task as TaskPydantic


def example_web_to_coordinator_project():
    """
    Example of converting a Web Dashboard project to a Project Coordinator project.
    
    This example demonstrates how to convert a project from the Web Dashboard
    representation to the Project Coordinator representation.
    """
    # Create a Web Dashboard project (could be from a database query)
    web_project = {
        "id": uuid.uuid4(),
        "name": "Example Project",
        "description": "An example project",
        "status": "DRAFT",
        "owner_id": uuid.uuid4(),
        "metadata": {"key": "value"}
    }
    
    # Convert to Project Coordinator representation
    coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(web_project)
    
    # Now coordinator_project can be used with Project Coordinator APIs
    print(f"Converted project: {coordinator_project}")
    
    return coordinator_project


def example_coordinator_to_agent_project(coordinator_project: Dict[str, Any]):
    """
    Example of converting a Project Coordinator project to an Agent Orchestrator project.
    
    This example demonstrates how to convert a project from the Project Coordinator
    representation to the Agent Orchestrator representation.
    
    Args:
        coordinator_project: A Project Coordinator project
    """
    # Convert to Agent Orchestrator representation
    agent_project = CoordinatorToAgentAdapter.project_to_agent(coordinator_project)
    
    # Now agent_project can be used with Agent Orchestrator APIs
    print(f"Converted project: {agent_project}")
    
    return agent_project


def example_agent_to_model_project(agent_project: Dict[str, Any]):
    """
    Example of converting an Agent Orchestrator project to a Model Orchestration project.
    
    This example demonstrates how to convert a project from the Agent Orchestrator
    representation to the Model Orchestration representation.
    
    Args:
        agent_project: An Agent Orchestrator project
    """
    # Convert to Model Orchestration representation
    model_project = AgentToModelAdapter.project_to_model(agent_project)
    
    # Now model_project can be used with Model Orchestration APIs
    print(f"Converted project: {model_project}")
    
    return model_project


def example_full_chain_conversion():
    """
    Example of converting a project through the full chain of service boundaries.
    
    This example demonstrates how to convert a project from the Web Dashboard
    representation through all service boundaries to the Model Orchestration
    representation.
    """
    # Create a Web Dashboard project
    web_project = ProjectPydantic(
        id=uuid.uuid4(),
        name="Example Project",
        description="An example project",
        status="DRAFT",
        owner_id=uuid.uuid4(),
        metadata={"key": "value"}
    )
    
    # Convert to Project Coordinator representation
    coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(web_project)
    
    # Convert to Agent Orchestrator representation
    agent_project = CoordinatorToAgentAdapter.project_to_agent(coordinator_project)
    
    # Convert to Model Orchestration representation
    model_project = AgentToModelAdapter.project_to_model(agent_project)
    
    # Now model_project can be used with Model Orchestration APIs
    print(f"Final converted project: {model_project}")
    
    return model_project


def example_error_handling():
    """
    Example of handling errors during conversion.
    
    This example demonstrates how to handle errors that may occur during
    the conversion process.
    """
    try:
        # Create an invalid project (missing required fields)
        invalid_project = {"name": "Invalid Project"}
        
        # Try to convert to Project Coordinator representation
        coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(invalid_project)
        
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        
        # Handle the error (e.g., log it, return a default value, etc.)
        coordinator_project = {
            "id": uuid.uuid4(),
            "name": "Default Project",
            "description": "",
            "status": "DRAFT",
            "owner_id": None,
            "project_metadata": {}
        }
    
    return coordinator_project


def example_service_communication():
    """
    Example of using adapters in service communication.
    
    This example demonstrates how to use adapters in service communication
    to ensure consistent data representation across service boundaries.
    """
    # In Web Dashboard service
    def web_create_project(project_data):
        # Create a project in the Web Dashboard
        web_project = ProjectPydantic(**project_data)
        
        # Save to database
        # db.save(web_project)
        
        # Convert to Project Coordinator representation for API call
        coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(web_project)
        
        # Call Project Coordinator API
        # response = api_client.post("/projects", json=coordinator_project)
        
        return web_project
    
    # In Project Coordinator service
    def coordinator_receive_project(coordinator_project):
        # Validate the project
        # validate_project(coordinator_project)
        
        # Save to database
        # db.save(coordinator_project)
        
        # Convert to Agent Orchestrator representation for API call
        agent_project = CoordinatorToAgentAdapter.project_to_agent(coordinator_project)
        
        # Call Agent Orchestrator API
        # response = api_client.post("/projects", json=agent_project)
        
        return coordinator_project
    
    # Example usage
    project_data = {
        "name": "Example Project",
        "description": "An example project",
        "status": "DRAFT",
        "owner_id": uuid.uuid4(),
        "metadata": {"key": "value"}
    }
    
    web_project = web_create_project(project_data)
    coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(web_project)
    coordinator_project = coordinator_receive_project(coordinator_project)
    
    return coordinator_project


if __name__ == "__main__":
    # Run the examples
    coordinator_project = example_web_to_coordinator_project()
    agent_project = example_coordinator_to_agent_project(coordinator_project)
    model_project = example_agent_to_model_project(agent_project)
    
    example_full_chain_conversion()
    example_error_handling()
    example_service_communication()
