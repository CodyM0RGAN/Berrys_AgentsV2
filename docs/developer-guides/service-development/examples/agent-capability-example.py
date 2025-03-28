"""
Agent Capability Configuration Example

This example demonstrates how to use the enhanced AgentToModelAdapter to properly
handle agent capabilities when converting between Agent Orchestrator and Model Orchestration
representations. It shows:

1. How different agent types are mapped to appropriate capabilities
2. How capability-specific configuration is automatically added
3. How to use the adapter in a service context
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

# Import shared models and adapters
from shared.models.src.adapters import AgentToModelAdapter
from shared.models.src.enums import AgentType, ModelCapability
from shared.models.src.api.errors import create_error_response
from shared.utils.src.request_id import RequestIdMiddleware, get_request_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Agent Capability Example")

# Add request ID middleware
app.add_middleware(RequestIdMiddleware)

# Mock client for Model Orchestration service
class ModelOrchestrationClient:
    """Mock client for Model Orchestration service."""
    
    BASE_URL = "http://model-orchestration:8000"
    
    async def create_agent(self, model_agent: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create an agent in the Model Orchestration service.
        
        Args:
            model_agent: The agent data in Model Orchestration format
            request_id: Optional request ID for tracing
            
        Returns:
            Created agent data
        """
        # In a real implementation, this would make an HTTP request to the service
        # For this example, we'll just log the agent data and return it
        
        logger.info(
            f"Creating agent in Model Orchestration: {model_agent['name']}",
            extra={
                "request_id": request_id,
                "agent_id": model_agent.get("agent_id"),
                "capabilities": model_agent.get("capabilities", [])
            }
        )
        
        # Log capability configuration for demonstration
        if "settings" in model_agent and "capability_config" in model_agent["settings"]:
            capability_config = model_agent["settings"]["capability_config"]
            logger.info(
                f"Agent capability configuration: {capability_config}",
                extra={"request_id": request_id}
            )
        
        # Simulate created agent with ID
        model_agent["created_at"] = "2025-03-26T12:00:00Z"
        model_agent["updated_at"] = "2025-03-26T12:00:00Z"
        
        return model_agent

# Create client instance
model_orchestration_client = ModelOrchestrationClient()

# Agent service with capability handling
class AgentService:
    """Service for managing agents with capability configuration."""
    
    def __init__(self, model_client: ModelOrchestrationClient):
        self.model_client = model_client
        
    async def create_agent(self, agent_data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create an agent with proper capability configuration.
        
        Args:
            agent_data: Agent data in Agent Orchestrator format
            request_id: Optional request ID for tracing
            
        Returns:
            Created agent data
        """
        try:
            # Ensure agent has an ID
            if "id" not in agent_data:
                agent_data["id"] = str(uuid.uuid4())
                
            # Convert to Model Orchestration format with capability configuration
            model_agent = AgentToModelAdapter.agent_to_model(agent_data)
            
            # Log the conversion for demonstration
            logger.info(
                f"Converted agent to Model Orchestration format",
                extra={
                    "request_id": request_id,
                    "agent_id": model_agent.get("agent_id"),
                    "agent_type": agent_data.get("agent_type"),
                    "capabilities": model_agent.get("capabilities", [])
                }
            )
            
            # Create agent in Model Orchestration service
            created_agent = await self.model_client.create_agent(model_agent, request_id)
            
            # Convert back to Agent Orchestrator format
            agent_orchestrator_agent = AgentToModelAdapter.agent_from_model(created_agent)
            
            return agent_orchestrator_agent
        except Exception as e:
            logger.error(
                f"Error creating agent: {str(e)}",
                extra={"request_id": request_id},
                exc_info=True
            )
            raise

# Create agent service
agent_service = AgentService(model_orchestration_client)

# Define API endpoints
@app.post("/agents")
async def create_agent(agent_data: Dict[str, Any], request: Request):
    """
    Create an agent with proper capability configuration.
    
    Args:
        agent_data: Agent data in Agent Orchestrator format
        request: FastAPI request object
        
    Returns:
        Created agent data
    """
    request_id = get_request_id(request)
    
    try:
        # Create agent with capability configuration
        agent = await agent_service.create_agent(agent_data, request_id)
        return agent
    except Exception as e:
        # Return 500 response
        logger.error(
            f"Unexpected error: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        error_response = create_error_response(
            code="AGENT_CREATION_ERROR",
            message="Failed to create agent",
            details={"error": str(e)},
            request_id=request_id
        )
        return JSONResponse(status_code=500, content=error_response)

# Example usage
@app.get("/examples")
async def get_examples(request: Request):
    """
    Get example agent configurations for different agent types.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Example agent configurations
    """
    request_id = get_request_id(request)
    
    # Create example agents for different types
    examples = {}
    
    # Developer agent example
    developer_agent = {
        "id": str(uuid.uuid4()),
        "name": "Developer Agent",
        "agent_type": AgentType.DEVELOPER,
        "status": "ACTIVE",
        "project_id": str(uuid.uuid4()),
        "config": {
            "language_preference": "python",
            "code_style": "pep8"
        }
    }
    
    # Designer agent example
    designer_agent = {
        "id": str(uuid.uuid4()),
        "name": "Designer Agent",
        "agent_type": AgentType.DESIGNER,
        "status": "ACTIVE",
        "project_id": str(uuid.uuid4()),
        "config": {
            "theme": "modern",
            "style_preference": "minimalist"
        }
    }
    
    # Researcher agent example
    researcher_agent = {
        "id": str(uuid.uuid4()),
        "name": "Researcher Agent",
        "agent_type": AgentType.RESEARCHER,
        "status": "ACTIVE",
        "project_id": str(uuid.uuid4()),
        "config": {
            "research_depth": "comprehensive",
            "sources": ["academic", "web"]
        }
    }
    
    # Convert to Model Orchestration format to show capability configuration
    examples["developer"] = {
        "agent_orchestrator": developer_agent,
        "model_orchestration": AgentToModelAdapter.agent_to_model(developer_agent)
    }
    
    examples["designer"] = {
        "agent_orchestrator": designer_agent,
        "model_orchestration": AgentToModelAdapter.agent_to_model(designer_agent)
    }
    
    examples["researcher"] = {
        "agent_orchestrator": researcher_agent,
        "model_orchestration": AgentToModelAdapter.agent_to_model(researcher_agent)
    }
    
    return examples

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
