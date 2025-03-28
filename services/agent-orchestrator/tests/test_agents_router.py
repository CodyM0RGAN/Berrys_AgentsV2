import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4
import json
from typing import Dict, Any

from src.models.api import AgentState


@pytest.mark.asyncio
async def test_create_agent(client: AsyncClient, agent_template: Dict[str, Any]):
    """
    Test creating an agent.
    """
    # Prepare request data
    agent_data = {
        "name": "New Test Agent",
        "description": "A test agent created via API",
        "type": "RESEARCHER",
        "project_id": "00000000-0000-0000-0000-000000000001",
        "template_id": agent_template["id"],
        "configuration": {
            "key1": "test-value",
            "key2": 100,
        },
        "prompt_template": "You are a {{agent_type}} agent named {{name}}.",
    }
    
    # Send request
    response = await client.post("/api/agents", json=agent_data)
    
    # Check response
    assert response.status_code == 201
    data = response.json()
    
    # Validate response data
    assert data["name"] == agent_data["name"]
    assert data["description"] == agent_data["description"]
    assert data["type"] == agent_data["type"]
    assert data["project_id"] == agent_data["project_id"]
    assert data["template_id"] == agent_data["template_id"]
    assert data["configuration"] == agent_data["configuration"]
    assert data["prompt_template"] == agent_data["prompt_template"]
    assert data["state"] == AgentState.CREATED.value
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_get_agent(client: AsyncClient, agent: Dict[str, Any]):
    """
    Test getting an agent by ID.
    """
    # Send request
    response = await client.get(f"/api/agents/{agent['id']}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Validate response data
    assert data["id"] == agent["id"]
    assert data["name"] == agent["name"]
    assert data["description"] == agent["description"]
    assert data["type"] == agent["type"]
    assert data["project_id"] == agent["project_id"]
    assert data["template_id"] == agent["template_id"]
    assert data["configuration"] == agent["configuration"]
    assert data["prompt_template"] == agent["prompt_template"]
    assert data["state"] == agent["state"]


@pytest.mark.asyncio
async def test_get_agent_not_found(client: AsyncClient):
    """
    Test getting a non-existent agent.
    """
    # Generate random UUID
    random_id = str(uuid4())
    
    # Send request
    response = await client.get(f"/api/agents/{random_id}")
    
    # Check response
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert random_id in data["detail"]


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient, agent: Dict[str, Any]):
    """
    Test listing agents.
    """
    # Send request
    response = await client.get("/api/agents")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Validate response data
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert data["total"] >= 1
    assert data["page"] == 1
    
    # Check if our agent is in the list
    agent_ids = [item["id"] for item in data["items"]]
    assert agent["id"] in agent_ids


@pytest.mark.asyncio
async def test_update_agent(client: AsyncClient, agent: Dict[str, Any]):
    """
    Test updating an agent.
    """
    # Prepare update data
    update_data = {
        "name": "Updated Agent Name",
        "description": "Updated description",
        "configuration": {
            "key1": "updated-value",
            "key2": 200,
            "key3": "new-value",
        },
    }
    
    # Send request
    response = await client.put(f"/api/agents/{agent['id']}", json=update_data)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Validate response data
    assert data["id"] == agent["id"]
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["configuration"] == update_data["configuration"]
    assert data["type"] == agent["type"]  # Unchanged
    assert data["project_id"] == agent["project_id"]  # Unchanged
    assert data["template_id"] == agent["template_id"]  # Unchanged
    assert data["prompt_template"] == agent["prompt_template"]  # Unchanged


@pytest.mark.asyncio
async def test_delete_agent(client: AsyncClient, agent: Dict[str, Any]):
    """
    Test deleting an agent.
    """
    # Send delete request
    response = await client.delete(f"/api/agents/{agent['id']}")
    
    # Check response
    assert response.status_code == 204
    
    # Verify agent is deleted
    get_response = await client.get(f"/api/agents/{agent['id']}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_execute_agent(client: AsyncClient, agent: Dict[str, Any]):
    """
    Test executing an agent.
    """
    # Prepare execution request
    execution_request = {
        "task_id": "00000000-0000-0000-0000-000000000001",
        "input": {
            "query": "What is the capital of France?",
            "context": ["France is a country in Europe."],
        },
        "parameters": {
            "max_tokens": 100,
            "temperature": 0.7,
        },
    }
    
    # Send request
    response = await client.post(f"/api/agents/{agent['id']}/execute", json=execution_request)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Validate response data
    assert "execution_id" in data
    assert "agent_id" in data
    assert "task_id" in data
    assert "status" in data
    assert data["agent_id"] == agent["id"]
    assert data["task_id"] == execution_request["task_id"]
