"""
Integration tests for the agent-orchestrator service.

This module tests the integration between the agent-orchestrator service
and other services it interacts with, ensuring proper communication
and behavior across service boundaries.
"""

import os
import pytest
import asyncio
from unittest.mock import patch

from shared.utils.src.testing.integration import (
    ServiceHarness,
    IntegrationTestHarness,
    MockIntegrationService,
    integration_test,
    with_retries
)

from src.models.agent import Agent
from src.models.template import AgentTemplate


class TestServiceIntegration:
    """Integration tests for agent-orchestrator service interactions."""
    
    @pytest.fixture
    def mock_model_orchestration(self):
        """Create a mock model-orchestration service."""
        service = MockIntegrationService("model-orchestration")
        
        # Add mock endpoints
        service.add_endpoint(
            path="/v1/models/generate",
            method="POST",
            response_data={
                "id": "gen-123456",
                "model": "gpt-4",
                "choices": [
                    {
                        "text": "This is a generated response from the model orchestration service.",
                        "index": 0,
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 15,
                    "completion_tokens": 42,
                    "total_tokens": 57
                }
            }
        )
        
        service.add_endpoint(
            path="/v1/models",
            method="GET",
            response_data={
                "models": [
                    {"id": "gpt-4", "name": "GPT-4", "max_tokens": 8192},
                    {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "max_tokens": 4096}
                ]
            }
        )
        
        return service
        
    @pytest.fixture
    def mock_project_coordinator(self):
        """Create a mock project-coordinator service."""
        service = MockIntegrationService("project-coordinator")
        
        # Add mock endpoints
        service.add_endpoint(
            path="/v1/projects/project-123",
            method="GET",
            response_data={
                "id": "project-123",
                "name": "Test Project",
                "description": "A test project",
                "status": "ACTIVE",
                "created_at": "2025-03-15T12:00:00Z",
                "updated_at": "2025-03-15T14:30:00Z"
            }
        )
        
        return service
    
    @patch('src.services.model_client.ModelClient.generate_text')
    @patch('src.services.project_client.ProjectClient.get_project')
    async def test_agent_lifecycle_with_mocks(self, mock_get_project, mock_generate_text):
        """Test agent lifecycle with mocked service clients."""
        # Set up mock responses
        mock_generate_text.return_value = {
            "id": "gen-123456",
            "choices": [
                {
                    "text": "This is a generated response from the mocked model client.",
                    "index": 0,
                    "finish_reason": "stop"
                }
            ]
        }
        
        mock_get_project.return_value = {
            "id": "project-123",
            "name": "Test Project",
            "status": "ACTIVE"
        }
        
        # Import the service here to ensure mocks are in place
        from src.services.agent_service import AgentService
        
        # Create service and execute flow
        service = AgentService()
        agent = await service.create_agent(
            name="Test Agent",
            agent_type="ASSISTANT",
            project_id="project-123",
            config={
                "capabilities": ["chat", "planning"],
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
        )
        
        # Check that the agent was created
        assert agent.name == "Test Agent"
        assert agent.agent_type == "ASSISTANT"
        assert agent.project_id == "project-123"
        
        # Verify mock calls
        mock_get_project.assert_called_once_with("project-123")
        
        # Run agent
        result = await service.run_agent(
            agent_id=agent.id,
            input_data={"message": "Hello, agent!"}
        )
        
        # Check that the model was called
        mock_generate_text.assert_called_once()
        assert "response" in result
        
    @integration_test(
        services=["agent-orchestrator"],
        mock_services=["model-orchestration", "project-coordinator"]
    )
    async def test_agent_lifecycle_with_service_harness(
        self, 
        harness, 
        mock_services
    ):
        """
        Test agent lifecycle using the integration test harness.
        
        This test starts the agent-orchestrator service and uses mock
        services for model-orchestration and project-coordinator.
        """
        # Set up mock services
        model_orch = mock_services["model-orchestration"]
        model_orch.add_endpoint(
            path="/v1/models/generate",
            method="POST",
            response_data={
                "id": "gen-123456",
                "model": "gpt-4",
                "choices": [
                    {
                        "text": "This is a generated response from the mock model orchestration service.",
                        "index": 0,
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 15,
                    "completion_tokens": 42,
                    "total_tokens": 57
                }
            }
        )
        
        proj_coord = mock_services["project-coordinator"]
        proj_coord.add_endpoint(
            path="/v1/projects/project-123",
            method="GET",
            response_data={
                "id": "project-123",
                "name": "Test Project",
                "description": "A test project",
                "status": "ACTIVE",
                "created_at": "2025-03-15T12:00:00Z",
                "updated_at": "2025-03-15T14:30:00Z"
            }
        )
        
        # Get agent-orchestrator service instance
        agent_orch = harness.get_service("agent-orchestrator")
        
        # Create agent
        response = agent_orch.post(
            "/v1/agents",
            json={
                "name": "Test Agent",
                "agent_type": "ASSISTANT",
                "project_id": "project-123",
                "config": {
                    "capabilities": ["chat", "planning"],
                    "parameters": {
                        "temperature": 0.7,
                        "max_tokens": 2000
                    }
                }
            }
        )
        
        # Check response
        assert response.status_code == 200
        agent_data = response.json()
        assert agent_data["name"] == "Test Agent"
        assert agent_data["agent_type"] == "ASSISTANT"
        assert agent_data["project_id"] == "project-123"
        
        # Verify project service was called
        assert any(
            r["path"] == "/v1/projects/project-123" and r["method"] == "GET"
            for r in proj_coord.requests
        )
        
        # Run agent
        agent_id = agent_data["id"]
        response = agent_orch.post(
            f"/v1/agents/{agent_id}/run",
            json={"message": "Hello, agent!"}
        )
        
        # Check response
        assert response.status_code == 200
        result = response.json()
        assert "response" in result
        
        # Verify model service was called
        assert any(
            r["path"] == "/v1/models/generate" and r["method"] == "POST"
            for r in model_orch.requests
        )
        
    @pytest.mark.skip(reason="Requires running all actual services")
    @integration_test(
        services=[
            "agent-orchestrator", 
            "model-orchestration", 
            "project-coordinator"
        ]
    )
    async def test_full_integration(self, harness):
        """
        Test full integration between all real services.
        
        Note: This test is skipped by default as it requires all services
        to be running. Use it for full integration testing in a controlled
        environment.
        """
        # Get service instances
        agent_orch = harness.get_service("agent-orchestrator")
        model_orch = harness.get_service("model-orchestration")
        proj_coord = harness.get_service("project-coordinator")
        
        # Create project
        proj_response = proj_coord.post(
            "/v1/projects",
            json={
                "name": "Integration Test Project",
                "description": "A project for integration testing"
            }
        )
        assert proj_response.status_code == 200
        project_data = proj_response.json()
        project_id = project_data["id"]
        
        # Create agent
        agent_response = agent_orch.post(
            "/v1/agents",
            json={
                "name": "Integration Test Agent",
                "agent_type": "ASSISTANT",
                "project_id": project_id,
                "config": {
                    "capabilities": ["chat"],
                    "parameters": {
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                }
            }
        )
        assert agent_response.status_code == 200
        agent_data = agent_response.json()
        agent_id = agent_data["id"]
        
        # Run agent
        run_response = agent_orch.post(
            f"/v1/agents/{agent_id}/run",
            json={"message": "Tell me a brief story about integration testing."}
        )
        assert run_response.status_code == 200
        result = run_response.json()
        assert "response" in result
        
        # Clean up
        delete_response = agent_orch.delete(f"/v1/agents/{agent_id}")
        assert delete_response.status_code in (200, 204)
        
        proj_delete_response = proj_coord.delete(f"/v1/projects/{project_id}")
        assert proj_delete_response.status_code in (200, 204)


# Utility function to demonstrate the `with_retries` decorator
@with_retries(retries=3, delay=1.0)
async def get_agent_with_retry(service, agent_id):
    """
    Get an agent with retry logic.
    
    This demonstrates how to use the with_retries decorator to handle
    potentially flaky service calls.
    
    Args:
        service: Service instance to call.
        agent_id: ID of the agent to get.
        
    Returns:
        Agent data.
    """
    response = service.get(f"/v1/agents/{agent_id}")
    if response.status_code != 200:
        raise Exception(f"Failed to get agent: {response.status_code}")
    return response.json()
