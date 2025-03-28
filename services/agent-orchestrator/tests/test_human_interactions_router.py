import uuid
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import status
from fastapi.testclient import TestClient

from src.main import app
from src.exceptions import AgentNotFoundError, HumanInteractionError
from src.models.api import (
    HumanApprovalRequest,
    HumanInteractionResponse,
    HumanFeedbackRequest,
)
from src.models.internal import HumanInteractionModel


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def mock_interaction_service():
    with patch("src.dependencies.get_human_interaction_service") as mock:
        service_mock = AsyncMock()
        mock.return_value.__aenter__.return_value = service_mock
        mock.return_value.__aexit__.return_value = None
        yield service_mock


@pytest.fixture
def test_agent_id():
    return uuid.uuid4()


@pytest.fixture
def test_execution_id():
    return uuid.uuid4()


@pytest.fixture
def test_interaction_id():
    return uuid.uuid4()


@pytest.fixture
def human_approval_request(test_execution_id):
    return {
        "execution_id": str(test_execution_id),
        "title": "Test Approval",
        "description": "Please review this test action",
        "options": ["Approve", "Reject", "Request changes"],
        "context": {"key": "value"},
        "deadline": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
        "priority": "high",
        "metadata": {"source": "test"}
    }


@pytest.fixture
def human_feedback_request(test_execution_id):
    return {
        "execution_id": str(test_execution_id),
        "feedback_type": "quality",
        "content": "Good work on this task",
        "rating": 4.5,
        "context": {"task": "test task"},
        "metadata": {"reviewer": "test_user"}
    }


def test_request_approval(test_client, mock_interaction_service, test_agent_id, human_approval_request):
    # Mock the response
    response_data = {
        "interaction_id": str(uuid.uuid4()),
        "agent_id": str(test_agent_id),
        "status": "pending",
        "timestamp": datetime.utcnow().isoformat()
    }
    mock_interaction_service.request_approval.return_value = response_data
    
    # Make the request
    response = test_client.post(
        f"/api/agents/{test_agent_id}/request-approval",
        json=human_approval_request
    )
    
    # Check the response
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == response_data
    
    # Verify service call
    mock_interaction_service.request_approval.assert_awaited_once()


def test_request_approval_agent_not_found(test_client, mock_interaction_service, test_agent_id, human_approval_request):
    # Mock the service to raise an exception
    mock_interaction_service.request_approval.side_effect = AgentNotFoundError(test_agent_id)
    
    # Make the request
    response = test_client.post(
        f"/api/agents/{test_agent_id}/request-approval",
        json=human_approval_request
    )
    
    # Check the response
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_request_approval_error(test_client, mock_interaction_service, test_agent_id, human_approval_request):
    # Mock the service to raise an exception
    mock_interaction_service.request_approval.side_effect = HumanInteractionError(
        test_agent_id, "Test error"
    )
    
    # Make the request
    response = test_client.post(
        f"/api/agents/{test_agent_id}/request-approval",
        json=human_approval_request
    )
    
    # Check the response
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "test error" in response.json()["detail"].lower()


def test_provide_approval(test_client, mock_interaction_service, test_interaction_id):
    # Create a mock interaction model
    interaction = MagicMock()
    interaction.to_dict.return_value = {
        "id": str(test_interaction_id),
        "status": "completed",
        "response": {"decision": "Approve", "feedback": "Looks good"}
    }
    
    # Mock the service
    mock_interaction_service.provide_approval.return_value = interaction
    
    # Make the request
    response = test_client.post(
        f"/api/agents/interactions/{test_interaction_id}/approve",
        params={"response": "Approve", "feedback": "Looks good"}
    )
    
    # Check the response
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == interaction.to_dict.return_value
    
    # Verify service call
    mock_interaction_service.provide_approval.assert_awaited_once_with(
        interaction_id=test_interaction_id,
        response="Approve",
        feedback="Looks good",
        user_id=None
    )


def test_submit_feedback(test_client, mock_interaction_service, test_agent_id, human_feedback_request):
    # Mock the response
    response_data = {
        "interaction_id": str(uuid.uuid4()),
        "agent_id": str(test_agent_id),
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat()
    }
    mock_interaction_service.submit_feedback.return_value = response_data
    
    # Make the request
    response = test_client.post(
        f"/api/agents/{test_agent_id}/submit-feedback",
        json=human_feedback_request
    )
    
    # Check the response
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == response_data
    
    # Verify service call
    mock_interaction_service.submit_feedback.assert_awaited_once()


def test_send_notification(test_client, mock_interaction_service, test_agent_id):
    # Create a notification
    notification = {"message": "Test notification", "data": {"key": "value"}}
    
    # Create a mock interaction model
    interaction = MagicMock()
    interaction.to_dict.return_value = {
        "id": str(uuid.uuid4()),
        "agent_id": str(test_agent_id),
        "type": "notification",
        "status": "delivered",
        "content": notification
    }
    
    # Mock the service
    mock_interaction_service.send_notification.return_value = interaction
    
    # Make the request
    response = test_client.post(
        f"/api/agents/{test_agent_id}/notify",
        json=notification
    )
    
    # Check the response
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == interaction.to_dict.return_value
    
    # Verify service call
    mock_interaction_service.send_notification.assert_awaited_once_with(
        agent_id=test_agent_id,
        notification=notification,
        execution_id=None,
        priority="normal"
    )


def test_get_interactions(test_client, mock_interaction_service, test_agent_id):
    # Create mock interactions
    interactions = [MagicMock() for _ in range(3)]
    for i, interaction in enumerate(interactions):
        interaction.to_dict.return_value = {
            "id": str(uuid.uuid4()),
            "agent_id": str(test_agent_id),
            "type": "notification",
            "status": "delivered",
            "content": {"message": f"Test {i}"}
        }
    
    # Mock the service
    mock_interaction_service.get_interactions_for_agent.return_value = (interactions, 3)
    
    # Make the request
    response = test_client.get(
        f"/api/agents/{test_agent_id}/interactions",
        params={"page": 1, "page_size": 20}
    )
    
    # Check the response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert len(data["items"]) == 3
    
    # Verify service call
    mock_interaction_service.get_interactions_for_agent.assert_awaited_once_with(
        agent_id=test_agent_id,
        interaction_type=None,
        status=None,
        page=1,
        page_size=20
    )


def test_get_interaction(test_client, mock_interaction_service, test_interaction_id):
    # Create a mock interaction
    interaction = MagicMock()
    interaction.to_dict.return_value = {
        "id": str(test_interaction_id),
        "type": "approval_request",
        "status": "pending",
        "content": {"title": "Test"}
    }
    
    # Mock the service
    mock_interaction_service.get_interaction.return_value = interaction
    
    # Make the request
    response = test_client.get(f"/api/agents/interactions/{test_interaction_id}")
    
    # Check the response
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == interaction.to_dict.return_value
    
    # Verify service call
    mock_interaction_service.get_interaction.assert_awaited_once_with(test_interaction_id)


def test_get_interaction_not_found(test_client, mock_interaction_service, test_interaction_id):
    # Mock the service to return None
    mock_interaction_service.get_interaction.return_value = None
    
    # Make the request
    response = test_client.get(f"/api/agents/interactions/{test_interaction_id}")
    
    # Check the response
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_get_pending_approvals(test_client, mock_interaction_service):
    # Create mock interactions
    interactions = [MagicMock() for _ in range(2)]
    for i, interaction in enumerate(interactions):
        interaction.to_dict.return_value = {
            "id": str(uuid.uuid4()),
            "type": "approval_request",
            "status": "pending",
            "content": {"title": f"Pending {i}"}
        }
    
    # Mock the service
    mock_interaction_service.get_pending_approvals.return_value = (interactions, 2)
    
    # Make the request
    response = test_client.get("/api/agents/pending-approvals")
    
    # Check the response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 2
    assert data["page"] == 1
    assert len(data["items"]) == 2
    
    # Verify service call
    mock_interaction_service.get_pending_approvals.assert_awaited_once_with(
        project_id=None,
        page=1,
        page_size=20
    )
