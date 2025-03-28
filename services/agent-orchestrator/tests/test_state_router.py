import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4
import json
from typing import Dict, Any


@pytest.mark.asyncio
async def test_get_agent_state(client: AsyncClient, agent: Dict[str, Any]):
    """
    Test getting an agent's state.
    """
    # Send request
    response = await client.get(f"/api/agents/{agent['id']}/state")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Validate response data - might be empty initially
    assert isinstance(data, dict) or data is None


@pytest.mark.asyncio
async def test_update_agent_state(client: AsyncClient, agent: Dict[str, Any]):
    """
    Test updating an agent's state.
    """
    # Prepare state update
    state_update = {
        "memory": {
            "key1": "value1",
            "key2": 100
        },
        "context": ["Context item 1", "Context item 2"],
        "conversation_history": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there! How can I help you?"}
        ]
    }
    
    # Send request
    response = await client.put(f"/api/agents/{agent['id']}/state", json=state_update)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Validate response data
    assert data["memory"]["key1"] == "value1"
    assert data["memory"]["key2"] == 100
    assert data["context"] == ["Context item 1", "Context item 2"]
    assert len(data["conversation_history"]) == 3
    
    # Get the state to verify it was saved
    get_response = await client.get(f"/api/agents/{agent['id']}/state")
    get_data = get_response.json()
    
    # Validate get response data
    assert get_data["memory"]["key1"] == "value1"
    assert get_data["memory"]["key2"] == 100
    assert get_data["context"] == ["Context item 1", "Context item 2"]
    assert len(get_data["conversation_history"]) == 3


@pytest.mark.asyncio
async def test_create_checkpoint(client: AsyncClient, agent: Dict[str, Any]):
    """
    Test creating a checkpoint.
    """
    # First, update the agent state
    state_update = {
        "memory": {"key": "value"},
        "context": ["Important context"]
    }
    
    await client.put(f"/api/agents/{agent['id']}/state", json=state_update)
    
    # Send checkpoint request
    response = await client.post(f"/api/agents/{agent['id']}/state/checkpoint")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Validate response data
    assert "id" in data
    assert "agent_id" in data
    assert data["agent_id"] == agent["id"]
    assert "sequence_number" in data
    assert data["sequence_number"] >= 1


@pytest.mark.asyncio
async def test_get_latest_checkpoint(client: AsyncClient, agent: Dict[str, Any]):
    """
    Test getting the latest checkpoint.
    """
    # First create a checkpoint
    await test_create_checkpoint(client, agent)
    
    # Send request
    response = await client.get(f"/api/agents/{agent['id']}/state/checkpoint")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Validate response data
    assert "id" in data
    assert "agent_id" in data
    assert data["agent_id"] == agent["id"]
    assert "state_data" in data
    assert "sequence_number" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_merge_state_update(client: AsyncClient, agent: Dict[str, Any]):
    """
    Test that state updates are merged correctly.
    """
    # First update
    first_update = {
        "memory": {
            "key1": "original-value",
            "key2": 100
        },
        "flags": {
            "flag1": True,
            "flag2": False
        }
    }
    
    # Second update (partial)
    second_update = {
        "memory": {
            "key1": "updated-value",
            "key3": "new-value"
        }
    }
    
    # Apply first update
    await client.put(f"/api/agents/{agent['id']}/state", json=first_update)
    
    # Apply second update
    response = await client.put(f"/api/agents/{agent['id']}/state", json=second_update)
    data = response.json()
    
    # Validate merged state
    assert data["memory"]["key1"] == "updated-value"  # Should be updated
    assert data["memory"]["key2"] == 100  # Should be preserved
    assert data["memory"]["key3"] == "new-value"  # Should be added
    assert data["flags"]["flag1"] == True  # Should be preserved
    assert data["flags"]["flag2"] == False  # Should be preserved
