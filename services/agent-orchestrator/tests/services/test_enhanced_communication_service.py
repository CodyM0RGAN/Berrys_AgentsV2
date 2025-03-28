"""
Tests for the enhanced communication service.
"""

import pytest
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from ...src.config import AgentOrchestratorConfig
from ...src.services.enhanced_communication_service import EnhancedCommunicationService
from ...src.models.api import AgentCommunicationRequest
from ...src.models.internal import AgentModel, AgentCommunicationModel
from shared.utils.src.messaging import EventBus, CommandBus
from shared.utils.src.redis import get_redis_client


@pytest.fixture
async def db_session():
    """
    Fixture for database session.
    
    This uses the actual test database for testing.
    """
    # Import here to avoid circular imports
    from ...src.database import get_db
    
    # Get a database session
    async for session in get_db():
        yield session


@pytest.fixture
async def redis_client():
    """
    Fixture for Redis client.
    
    This uses the actual Redis instance for testing.
    """
    # Use the test database (1) to avoid conflicts with development data
    redis_url = "redis://localhost:6379/1"
    client = get_redis_client(redis_url)
    
    # Clear the test database before each test
    await client.flushdb()
    
    yield client
    
    # Clean up after the test
    await client.flushdb()
    await client.close()


@pytest.fixture
async def event_bus():
    """
    Fixture for event bus.
    """
    # Create a mock event bus
    bus = AsyncMock(spec=EventBus)
    
    yield bus


@pytest.fixture
async def command_bus():
    """
    Fixture for command bus.
    """
    # Create a mock command bus
    bus = AsyncMock(spec=CommandBus)
    
    yield bus


@pytest.fixture
async def settings():
    """
    Fixture for settings.
    """
    # Create settings with Redis configuration
    settings = AgentOrchestratorConfig()
    settings.redis_url = "redis://localhost:6379/1"
    
    yield settings


@pytest.fixture
async def enhanced_communication_service(db_session, event_bus, command_bus, settings):
    """
    Fixture for enhanced communication service.
    """
    # Create the service
    service = EnhancedCommunicationService(
        db=db_session,
        event_bus=event_bus,
        command_bus=command_bus,
        settings=settings,
    )
    
    yield service


@pytest.fixture
async def agent_model(db_session):
    """
    Fixture for agent model.
    """
    # Create a project ID
    project_id = uuid.uuid4()
    
    # Create an agent
    agent = AgentModel(
        id=uuid.uuid4(),
        name="Test Agent",
        type="TEST",
        project_id=project_id,
        status="ACTIVE",
        configuration={},
    )
    
    # Add the agent to the database
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    
    yield agent
    
    # Clean up
    await db_session.delete(agent)
    await db_session.commit()


@pytest.fixture
async def another_agent_model(db_session, agent_model):
    """
    Fixture for another agent model.
    """
    # Create another agent in the same project
    agent = AgentModel(
        id=uuid.uuid4(),
        name="Another Test Agent",
        type="TEST",
        project_id=agent_model.project_id,
        status="ACTIVE",
        configuration={},
    )
    
    # Add the agent to the database
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    
    yield agent
    
    # Clean up
    await db_session.delete(agent)
    await db_session.commit()


@pytest.mark.asyncio
async def test_send_communication(enhanced_communication_service, agent_model, another_agent_model, event_bus):
    """
    Test sending a communication.
    """
    # Create a communication request
    request = AgentCommunicationRequest(
        to_agent_id=another_agent_model.id,
        content={"message": "Test message"},
        type="test_message",
    )
    
    # Send the communication
    response = await enhanced_communication_service.send_communication(agent_model.id, request)
    
    # Check the response
    assert response is not None
    assert response.from_agent_id == agent_model.id
    assert response.to_agent_id == another_agent_model.id
    assert response.status == "sent"
    
    # Check that the event was published
    event_bus.publish_event.assert_called_once()
    args, kwargs = event_bus.publish_event.call_args
    assert args[0] == "agent.communication.sent"
    assert args[1]["from_agent_id"] == str(agent_model.id)
    assert args[1]["to_agent_id"] == str(another_agent_model.id)


@pytest.mark.asyncio
async def test_receive_message(enhanced_communication_service, agent_model, another_agent_model):
    """
    Test receiving a message.
    """
    # Create a communication request
    request = AgentCommunicationRequest(
        to_agent_id=another_agent_model.id,
        content={"message": "Test message"},
        type="test_message",
    )
    
    # Send the communication
    response = await enhanced_communication_service.send_communication(agent_model.id, request)
    
    # Receive the message
    message = await enhanced_communication_service.receive_message(another_agent_model.id)
    
    # Check the message
    assert message is not None
    assert message["source_agent_id"] == str(agent_model.id)
    assert message["destination"]["id"] == str(another_agent_model.id)
    assert message["type"] == "test_message"
    assert message["payload"]["message"] == "Test message"


@pytest.mark.asyncio
async def test_topic_subscription(enhanced_communication_service, agent_model):
    """
    Test topic subscription.
    """
    # Subscribe to a topic
    topic = "test.topic"
    await enhanced_communication_service.subscribe(agent_model.id, topic)
    
    # Get subscriptions
    subscriptions = await enhanced_communication_service.get_subscriptions(agent_model.id)
    
    # Check that the agent is subscribed to the topic
    assert topic in subscriptions
    
    # Unsubscribe from the topic
    await enhanced_communication_service.unsubscribe(agent_model.id, topic)
    
    # Get subscriptions
    subscriptions = await enhanced_communication_service.get_subscriptions(agent_model.id)
    
    # Check that the agent is no longer subscribed to the topic
    assert topic not in subscriptions


@pytest.mark.asyncio
async def test_publish_to_topic(enhanced_communication_service, agent_model, another_agent_model):
    """
    Test publishing to a topic.
    """
    # Subscribe to a topic
    topic = "test.topic"
    await enhanced_communication_service.subscribe(another_agent_model.id, topic)
    
    # Publish to the topic
    content = {"message": "Test message"}
    message_id = await enhanced_communication_service.publish_to_topic(agent_model.id, topic, content)
    
    # Check that the message was published
    assert message_id is not None
    
    # Receive the message
    message = await enhanced_communication_service.receive_message(another_agent_model.id)
    
    # Check the message
    assert message is not None
    assert message["source_agent_id"] == str(agent_model.id)
    assert message["type"] == "topic_message"
    assert message["payload"]["message"] == "Test message"
    assert message["headers"]["topic"] == topic


@pytest.mark.asyncio
async def test_broadcast(enhanced_communication_service, agent_model, another_agent_model):
    """
    Test broadcasting a message.
    """
    # Create a third agent
    third_agent = AgentModel(
        id=uuid.uuid4(),
        name="Third Test Agent",
        type="TEST",
        project_id=agent_model.project_id,
        status="ACTIVE",
        configuration={},
    )
    
    # Add the agent to the database
    enhanced_communication_service.db.add(third_agent)
    await enhanced_communication_service.db.commit()
    await enhanced_communication_service.db.refresh(third_agent)
    
    try:
        # Broadcast a message
        content = {"message": "Test broadcast"}
        to_agent_ids = [another_agent_model.id, third_agent.id]
        message_ids = await enhanced_communication_service.broadcast(agent_model.id, to_agent_ids, content)
        
        # Check that the message was broadcast
        assert len(message_ids) == len(to_agent_ids)
        
        # Receive the messages
        for agent_id in to_agent_ids:
            message = await enhanced_communication_service.receive_message(agent_id)
            
            # Check the message
            assert message is not None
            assert message["source_agent_id"] == str(agent_model.id)
            assert message["type"] == "broadcast"
            assert message["payload"]["message"] == "Test broadcast"
    finally:
        # Clean up
        await enhanced_communication_service.db.delete(third_agent)
        await enhanced_communication_service.db.commit()


@pytest.mark.asyncio
async def test_send_request(enhanced_communication_service, agent_model, another_agent_model):
    """
    Test sending a request and waiting for a reply.
    """
    # Create a request handler
    async def handle_request(message):
        if message["type"] == "request":
            # Create a reply
            reply = {
                "source_agent_id": str(another_agent_model.id),
                "destination": {
                    "type": "agent",
                    "id": message["source_agent_id"],
                },
                "type": "reply",
                "correlation_id": message["correlation_id"],
                "payload": {
                    "message": "Test reply",
                },
            }
            
            # Send the reply
            await enhanced_communication_service.hub.send_message(reply)
    
    # Register the request handler
    await enhanced_communication_service.hub.register_message_handler("request", handle_request)
    
    # Send a request
    content = {"message": "Test request"}
    reply = await enhanced_communication_service.send_request(agent_model.id, another_agent_model.id, content)
    
    # Check the reply
    assert reply is not None
    assert reply["type"] == "reply"
    assert reply["payload"]["message"] == "Test reply"


@pytest.mark.asyncio
async def test_add_rule(enhanced_communication_service, agent_model, another_agent_model):
    """
    Test adding a routing rule.
    """
    # Add a routing rule
    rule = {
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
                "destination": str(another_agent_model.id),
            },
        ],
        "is_terminal": True,
    }
    
    await enhanced_communication_service.add_rule(rule)
    
    # Create a message that matches the rule
    message = {
        "source_agent_id": str(agent_model.id),
        "type": "test_message",
        "payload": {
            "message": "Test message",
            "task_type": "research",
        },
    }
    
    # Send the message
    await enhanced_communication_service.hub.send_message(message)
    
    # Receive the message
    received_message = await enhanced_communication_service.receive_message(another_agent_model.id)
    
    # Check the message
    assert received_message is not None
    assert received_message["source_agent_id"] == str(agent_model.id)
    assert received_message["type"] == "test_message"
    assert received_message["payload"]["task_type"] == "research"
