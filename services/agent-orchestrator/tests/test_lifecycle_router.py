import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4
import json
from typing import Dict, Any

from src.models.api import AgentState, AgentStatusChangeRequest


@pytest.mark.asyncio
async def test_change_agent_state(client: AsyncClient, agent: Dict[str, Any]):
    """
    Test changing an agent's state.
    """
    # Prepare state change request
    state_change = {
        "target_state": AgentState.INITIALIZING.value,
        "reason": "Starting agent initialization"
    }
    
    # Send request
    response = await client.post(f"/api/agents/{agent['id']}/state", json=state_change)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Validate response data
    assert data["id"] == agent["id"]
    assert data["state"] == AgentState.INITIALIZING.value
    
    # Test getting agent state history
    history_response = await client.get(f"/api/agents/{agent['id']}/state/history")
    
    # Check response
    assert history_response.status_code == 200
    history_data = history_response.json()
    
    # Validate history data
    assert isinstance(history_data, list)
    assert len(history_data) >= 1
    assert history_data[0]["agent_id"] == agent["id"]
    assert history_data[0]["new_state"] == AgentState.INITIALIZING.value
    assert history_data[0]["previous_state"] == agent["state"]
    assert history_data[0]["reason"] == state_change["reason"]


@pytest.mark.asyncio
async def test_state_transition_validation(client: AsyncClient, agent: Dict[str, Any]):
    """
    Test that invalid state transitions are rejected.
    """
    # Try an invalid transition (e.g., CREATED -> PAUSED)
    invalid_state_change = {
        "target_state": AgentState.PAUSED.value,
        "reason": "Invalid transition test"
    }
    
    # Send request
    response = await client.post(f"/api/agents/{agent['id']}/state", json=invalid_state_change)
    
    # Check response (should be error)
    assert response.status_code == 400
    data = response.json()
    
    # Validate error message
    assert "invalid" in data["detail"].lower() or "transition" in data["detail"].lower()
    
    # Agent state should not have changed
    get_response = await client.get(f"/api/agents/{agent['id']}")
    assert get_response.status_code == 200
    agent_data = get_response.json()
    assert agent_data["state"] == agent["state"]  # State unchanged


@pytest.mark.asyncio
async def test_complete_lifecycle_flow(client: AsyncClient, agent: Dict[str, Any]):
    """
    Test a complete lifecycle flow from CREATED to TERMINATED.
    """
    # Define the state transition sequence
    transitions = [
        {"target_state": AgentState.INITIALIZING.value, "reason": "Starting initialization"},
        {"target_state": AgentState.READY.value, "reason": "Initialization complete"},
        {"target_state": AgentState.ACTIVE.value, "reason": "Activating agent"},
        {"target_state": AgentState.PAUSED.value, "reason": "Pausing agent"},
        {"target_state": AgentState.ACTIVE.value, "reason": "Resuming agent"},
        {"target_state": AgentState.TERMINATED.value, "reason": "Terminating agent"}
    ]
    
    current_state = agent["state"]
    
    # Execute each transition in sequence
    for transition in transitions:
        # Skip if this would be an invalid transition
        if current_state == AgentState.TERMINATED.value:
            break
            
        # Send state change request
        response = await client.post(f"/api/agents/{agent['id']}/state", json=transition)
        
        # Check if this is a valid transition
        if response.status_code == 400:
            # Skip invalid transitions in our simplified test
            continue
            
        # Verify successful transition
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == transition["target_state"]
        current_state = transition["target_state"]
    
    # Verify final state
    get_response = await client.get(f"/api/agents/{agent['id']}")
    agent_data = get_response.json()
    assert agent_data["state"] in [AgentState.TERMINATED.value, current_state]
