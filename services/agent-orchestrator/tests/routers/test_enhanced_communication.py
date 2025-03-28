"""
Tests for the enhanced communication router.
"""

import pytest
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from ...src.config import AgentOrchestratorConfig
from ...src.models.api import UserInfo
from ...src.models.internal import AgentModel
from ...src.routers.enhanced_communication import router
from ...src.dependencies import get_enhanced_communication_service, get_current_user


@pytest.fixture
def app():
    """
    Fixture for FastAPI app.
    """
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """
    Fixture for test client.
    """
    return TestClient(app)


@pytest.fixture
def user_info():
    """
    Fixture for user info.
    """
    return UserInfo(
        id="test_user",
        username="test_user",
        email="test@example.com",
        is_admin=True,
        roles=["admin"],
    )


@pytest.fixture
def mock_enhanced_communication_service():
    """
    Fixture for mock enhanced communication service.
    """
    service = AsyncMock()
    return service


@pytest.fixture
def mock_dependencies(app, user_info, mock_enhanced_communication_service):
    """
    Fixture for mock dependencies.
    """
    # Override dependencies
    app.dependency_overrides[get_current_user] = lambda: user_info
    app.dependency_overrides[get_enhanced_communication_service] = lambda: mock_enhanced_communication_service
    
    yield
    
    # Reset dependencies
    app.dependency_overrides = {}


def test_send_communication(client, mock_dependencies, mock_enhanced_communication_service):
    """
    Test sending a communication.
    """
    # Create a communication request
    from_agent_id = str(uuid.uuid4())
    to_agent_id = str(uuid.uuid4())
    request_data = {
        "to_agent_id": to_agent_id,
        "content": {"message": "Test message"},
        "type": "test_message",
    }
    
    # Mock the response
    mock_enhanced_communication_service.send_communication.return_value = {
        "communication_id": str(uuid.uuid4()),
        "from_agent_id": from_agent_id,
        "to_agent_id": to_agent_id,
        "status": "sent",
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Send the request
    response = client.post(f"/enhanced-communication/send?from_agent_id={from_agent_id}", json=request_data)
    
    # Check the response
    assert response.status_code == 201
    assert response.json()["from_agent_id"] == from_agent_id
    assert response.json()["to_agent_id"] == to_agent_id
    assert response.json()["status"] == "sent"
    
    # Check that the service was called
    mock_enhanced_communication_service.send_communication.assert_called_once_with(
        uuid.UUID(from_agent_id),
        pytest.approx(request_data),
    )


def test_receive_message(client, mock_dependencies, mock_enhanced_communication_service):
    """
    Test receiving a message.
    """
    # Create an agent ID
    agent_id = str(uuid.uuid4())
    
    # Mock the response
    mock_enhanced_communication_service.receive_message.return_value = {
        "id": str(uuid.uuid4()),
        "source_agent_id": str(uuid.uuid4()),
        "destination": {
            "type": "agent",
            "id": agent_id,
        },
        "type": "test_message",
        "payload": {
            "message": "Test message",
        },
    }
    
    # Send the request
    response = client.get(f"/enhanced-communication/receive/{agent_id}")
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["destination"]["id"] == agent_id
    assert response.json()["payload"]["message"] == "Test message"
    
    # Check that the service was called
    mock_enhanced_communication_service.receive_message.assert_called_once_with(uuid.UUID(agent_id))


def test_subscribe_to_topic(client, mock_dependencies, mock_enhanced_communication_service):
    """
    Test subscribing to a topic.
    """
    # Create an agent ID
    agent_id = str(uuid.uuid4())
    
    # Create a subscription request
    request_data = {
        "agent_id": agent_id,
        "topic": "test.topic",
    }
    
    # Send the request
    response = client.post("/enhanced-communication/subscribe", json=request_data)
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["agent_id"] == agent_id
    assert response.json()["topic"] == "test.topic"
    assert response.json()["status"] == "subscribed"
    
    # Check that the service was called
    mock_enhanced_communication_service.subscribe.assert_called_once_with(
        uuid.UUID(agent_id),
        "test.topic",
    )


def test_unsubscribe_from_topic(client, mock_dependencies, mock_enhanced_communication_service):
    """
    Test unsubscribing from a topic.
    """
    # Create an agent ID
    agent_id = str(uuid.uuid4())
    
    # Create a subscription request
    request_data = {
        "agent_id": agent_id,
        "topic": "test.topic",
    }
    
    # Send the request
    response = client.post("/enhanced-communication/unsubscribe", json=request_data)
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["agent_id"] == agent_id
    assert response.json()["topic"] == "test.topic"
    assert response.json()["status"] == "unsubscribed"
    
    # Check that the service was called
    mock_enhanced_communication_service.unsubscribe.assert_called_once_with(
        uuid.UUID(agent_id),
        "test.topic",
    )


def test_get_subscriptions(client, mock_dependencies, mock_enhanced_communication_service):
    """
    Test getting subscriptions.
    """
    # Create an agent ID
    agent_id = str(uuid.uuid4())
    
    # Mock the response
    mock_enhanced_communication_service.get_subscriptions.return_value = [
        "test.topic1",
        "test.topic2",
    ]
    
    # Send the request
    response = client.get(f"/enhanced-communication/subscriptions/{agent_id}")
    
    # Check the response
    assert response.status_code == 200
    assert response.json() == ["test.topic1", "test.topic2"]
    
    # Check that the service was called
    mock_enhanced_communication_service.get_subscriptions.assert_called_once_with(uuid.UUID(agent_id))


def test_publish_to_topic(client, mock_dependencies, mock_enhanced_communication_service):
    """
    Test publishing to a topic.
    """
    # Create an agent ID
    agent_id = str(uuid.uuid4())
    
    # Create a publish request
    request_data = {
        "agent_id": agent_id,
        "topic": "test.topic",
        "content": {"message": "Test message"},
        "message_type": "test_message",
    }
    
    # Mock the response
    mock_enhanced_communication_service.publish_to_topic.return_value = "msg_123456789"
    
    # Send the request
    response = client.post("/enhanced-communication/publish", json=request_data)
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["message_id"] == "msg_123456789"
    assert response.json()["agent_id"] == agent_id
    assert response.json()["topic"] == "test.topic"
    assert response.json()["status"] == "published"
    
    # Check that the service was called
    mock_enhanced_communication_service.publish_to_topic.assert_called_once_with(
        uuid.UUID(agent_id),
        "test.topic",
        {"message": "Test message"},
        "test_message",
    )


def test_broadcast_message(client, mock_dependencies, mock_enhanced_communication_service):
    """
    Test broadcasting a message.
    """
    # Create agent IDs
    from_agent_id = str(uuid.uuid4())
    to_agent_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
    
    # Create a broadcast request
    request_data = {
        "from_agent_id": from_agent_id,
        "to_agent_ids": to_agent_ids,
        "content": {"message": "Test broadcast"},
        "message_type": "broadcast",
    }
    
    # Mock the response
    mock_enhanced_communication_service.broadcast.return_value = ["msg_123456789", "msg_987654321"]
    
    # Send the request
    response = client.post("/enhanced-communication/broadcast", json=request_data)
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["message_ids"] == ["msg_123456789", "msg_987654321"]
    assert response.json()["from_agent_id"] == from_agent_id
    assert response.json()["to_agent_ids"] == to_agent_ids
    assert response.json()["status"] == "broadcast"
    
    # Check that the service was called
    mock_enhanced_communication_service.broadcast.assert_called_once_with(
        uuid.UUID(from_agent_id),
        [uuid.UUID(agent_id) for agent_id in to_agent_ids],
        {"message": "Test broadcast"},
        "broadcast",
    )


def test_send_request(client, mock_dependencies, mock_enhanced_communication_service):
    """
    Test sending a request and waiting for a reply.
    """
    # Create agent IDs
    from_agent_id = str(uuid.uuid4())
    to_agent_id = str(uuid.uuid4())
    
    # Create a request-reply request
    request_data = {
        "from_agent_id": from_agent_id,
        "to_agent_id": to_agent_id,
        "content": {"message": "Test request"},
        "timeout": 30.0,
    }
    
    # Mock the response
    mock_enhanced_communication_service.send_request.return_value = {
        "correlation_id": "corr_123456789",
        "type": "reply",
        "payload": {
            "message": "Test reply",
        },
    }
    
    # Send the request
    response = client.post("/enhanced-communication/request", json=request_data)
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["correlation_id"] == "corr_123456789"
    assert response.json()["from_agent_id"] == from_agent_id
    assert response.json()["to_agent_id"] == to_agent_id
    assert response.json()["status"] == "replied"
    assert response.json()["reply"]["message"] == "Test reply"
    
    # Check that the service was called
    mock_enhanced_communication_service.send_request.assert_called_once_with(
        uuid.UUID(from_agent_id),
        uuid.UUID(to_agent_id),
        {"message": "Test request"},
        30.0,
    )


def test_add_routing_rule(client, mock_dependencies, mock_enhanced_communication_service):
    """
    Test adding a routing rule.
    """
    # Create a routing rule request
    request_data = {
        "rule": {
            "name": "test_rule",
            "conditions": [
                {
                    "type": "field",
                    "field": "task_type",
                    "operator": "eq",
                    "value": "research",
                },
            ],
            "actions": [
                {
                    "type": "route",
                    "destination": str(uuid.uuid4()),
                },
            ],
            "is_terminal": True,
        },
    }
    
    # Send the request
    response = client.post("/enhanced-communication/rules", json=request_data)
    
    # Check the response
    assert response.status_code == 201
    assert response.json()["rule_name"] == "test_rule"
    assert response.json()["status"] == "added"
    
    # Check that the service was called
    mock_enhanced_communication_service.add_rule.assert_called_once_with(request_data["rule"])
