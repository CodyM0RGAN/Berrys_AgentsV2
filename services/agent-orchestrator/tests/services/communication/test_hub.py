"""
Tests for the enhanced communication hub.
"""

import pytest
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from ....src.config import AgentOrchestratorConfig
from ....src.services.communication.hub import CommunicationHub
from ....src.services.communication.routing import TopicRouter, ContentRouter, RuleBasedRouter
from ....src.services.communication.priority import (
    PriorityQueue, 
    PriorityDeterminer, 
    PriorityDispatcher, 
    FairnessManager, 
    PriorityInheritanceManager
)
from shared.utils.src.redis import get_redis_client


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
async def communication_hub(redis_client):
    """
    Fixture for communication hub.
    """
    config = {
        'priority': {
            'priority_levels': 6,
            'default_priority': 2,
            'urgent_priority': 5,
        },
        'fairness': {
            'starvation_threshold': 60,  # 60 seconds
        },
        'inheritance': {
            'aging_threshold': 300,  # 5 minutes
            'aging_boost': 1,
        },
    }
    
    hub = CommunicationHub(redis_client, config)
    
    yield hub


@pytest.mark.asyncio
async def test_topic_subscription(communication_hub):
    """
    Test topic subscription.
    """
    agent_id = str(uuid.uuid4())
    topic = "test.topic"
    
    # Subscribe to topic
    await communication_hub.subscribe(agent_id, topic)
    
    # Get subscriptions
    subscriptions = await communication_hub.get_subscriptions(agent_id)
    
    # Check that the agent is subscribed to the topic
    assert topic in subscriptions
    
    # Unsubscribe from topic
    await communication_hub.unsubscribe(agent_id, topic)
    
    # Get subscriptions
    subscriptions = await communication_hub.get_subscriptions(agent_id)
    
    # Check that the agent is no longer subscribed to the topic
    assert topic not in subscriptions


@pytest.mark.asyncio
async def test_topic_publishing(communication_hub):
    """
    Test topic publishing.
    """
    agent_id = str(uuid.uuid4())
    topic = "test.topic"
    
    # Subscribe to topic
    await communication_hub.subscribe(agent_id, topic)
    
    # Create message
    message = {
        'source_agent_id': str(uuid.uuid4()),
        'type': 'test_message',
        'payload': {
            'message': 'Test message',
        },
        'headers': {
            'topic': topic,
        },
    }
    
    # Publish message to topic
    message_id = await communication_hub.publish_to_topic(topic, message)
    
    # Receive message
    received_message = await communication_hub.receive_message(agent_id)
    
    # Check that the message was received
    assert received_message is not None
    assert received_message['type'] == 'test_message'
    assert received_message['payload']['message'] == 'Test message'


@pytest.mark.asyncio
async def test_wildcard_topic_subscription(communication_hub):
    """
    Test wildcard topic subscription.
    """
    agent_id = str(uuid.uuid4())
    
    # Subscribe to wildcard topic
    await communication_hub.subscribe(agent_id, "test.*")
    
    # Create message
    message = {
        'source_agent_id': str(uuid.uuid4()),
        'type': 'test_message',
        'payload': {
            'message': 'Test message',
        },
        'headers': {
            'topic': 'test.subtopic',
        },
    }
    
    # Publish message to topic
    message_id = await communication_hub.publish_to_topic('test.subtopic', message)
    
    # Receive message
    received_message = await communication_hub.receive_message(agent_id)
    
    # Check that the message was received
    assert received_message is not None
    assert received_message['type'] == 'test_message'
    assert received_message['payload']['message'] == 'Test message'


@pytest.mark.asyncio
async def test_content_based_routing(communication_hub):
    """
    Test content-based routing.
    """
    agent_id = str(uuid.uuid4())
    
    # Add content-based routing rule
    await communication_hub.add_content_rule(
        lambda message: message.get('payload', {}).get('task_type') == 'research',
        agent_id
    )
    
    # Create message
    message = {
        'source_agent_id': str(uuid.uuid4()),
        'type': 'test_message',
        'payload': {
            'message': 'Test message',
            'task_type': 'research',
        },
    }
    
    # Send message
    await communication_hub.send_message(message)
    
    # Receive message
    received_message = await communication_hub.receive_message(agent_id)
    
    # Check that the message was received
    assert received_message is not None
    assert received_message['type'] == 'test_message'
    assert received_message['payload']['task_type'] == 'research'


@pytest.mark.asyncio
async def test_rule_based_routing(communication_hub):
    """
    Test rule-based routing.
    """
    agent_id = str(uuid.uuid4())
    
    # Add rule-based routing rule
    await communication_hub.add_rule({
        'name': 'research_rule',
        'conditions': [
            {
                'type': 'field',
                'field': 'task_type',
                'operator': 'eq',
                'value': 'research',
            },
        ],
        'actions': [
            {
                'type': 'route',
                'destination': agent_id,
            },
        ],
        'is_terminal': True,
    })
    
    # Create message
    message = {
        'source_agent_id': str(uuid.uuid4()),
        'type': 'test_message',
        'payload': {
            'message': 'Test message',
            'task_type': 'research',
        },
    }
    
    # Send message
    await communication_hub.send_message(message)
    
    # Receive message
    received_message = await communication_hub.receive_message(agent_id)
    
    # Check that the message was received
    assert received_message is not None
    assert received_message['type'] == 'test_message'
    assert received_message['payload']['task_type'] == 'research'


@pytest.mark.asyncio
async def test_priority_queue(redis_client):
    """
    Test priority queue.
    """
    # Create priority queue
    queue = PriorityQueue(redis_client, 'test_queue')
    
    # Create messages
    low_priority_message = {
        'id': str(uuid.uuid4()),
        'source_agent_id': str(uuid.uuid4()),
        'type': 'test_message',
        'payload': {
            'message': 'Low priority message',
        },
        'priority': 1,
    }
    
    high_priority_message = {
        'id': str(uuid.uuid4()),
        'source_agent_id': str(uuid.uuid4()),
        'type': 'test_message',
        'payload': {
            'message': 'High priority message',
        },
        'priority': 5,
    }
    
    # Enqueue messages
    await queue.enqueue(low_priority_message, 1)
    await queue.enqueue(high_priority_message, 5)
    
    # Dequeue message
    message = await queue.dequeue()
    
    # Check that the high priority message was dequeued first
    assert message is not None
    assert message['payload']['message'] == 'High priority message'
    
    # Dequeue message
    message = await queue.dequeue()
    
    # Check that the low priority message was dequeued second
    assert message is not None
    assert message['payload']['message'] == 'Low priority message'


@pytest.mark.asyncio
async def test_priority_dispatcher(redis_client):
    """
    Test priority dispatcher.
    """
    # Create priority dispatcher
    config = {
        'priority_levels': 6,
        'default_priority': 2,
        'urgent_priority': 5,
    }
    dispatcher = PriorityDispatcher(redis_client, config)
    
    # Create messages
    agent_id = str(uuid.uuid4())
    
    low_priority_message = {
        'id': str(uuid.uuid4()),
        'source_agent_id': str(uuid.uuid4()),
        'destination': {
            'type': 'agent',
            'id': agent_id,
        },
        'type': 'test_message',
        'payload': {
            'message': 'Low priority message',
        },
        'headers': {
            'priority': 1,
        },
    }
    
    high_priority_message = {
        'id': str(uuid.uuid4()),
        'source_agent_id': str(uuid.uuid4()),
        'destination': {
            'type': 'agent',
            'id': agent_id,
        },
        'type': 'test_message',
        'payload': {
            'message': 'High priority message',
        },
        'headers': {
            'priority': 5,
        },
    }
    
    # Dispatch messages
    await dispatcher.dispatch(low_priority_message)
    await dispatcher.dispatch(high_priority_message)
    
    # Get next message
    message = await dispatcher.get_next_message(agent_id)
    
    # Check that the high priority message was received first
    assert message is not None
    assert message['payload']['message'] == 'High priority message'
    
    # Get next message
    message = await dispatcher.get_next_message(agent_id)
    
    # Check that the low priority message was received second
    assert message is not None
    assert message['payload']['message'] == 'Low priority message'


@pytest.mark.asyncio
async def test_request_reply(communication_hub):
    """
    Test request-reply pattern.
    """
    # Create agent IDs
    requester_id = str(uuid.uuid4())
    responder_id = str(uuid.uuid4())
    
    # Create request
    request = {
        'source_agent_id': requester_id,
        'destination': {
            'type': 'agent',
            'id': responder_id,
        },
        'type': 'request',
        'payload': {
            'message': 'Test request',
        },
    }
    
    # Create reply handler
    async def reply_handler(message):
        # Check that the message is a request
        if message['type'] == 'request':
            # Create reply
            reply = {
                'source_agent_id': responder_id,
                'destination': {
                    'type': 'agent',
                    'id': message['source_agent_id'],
                },
                'type': 'reply',
                'correlation_id': message['correlation_id'],
                'payload': {
                    'message': 'Test reply',
                },
            }
            
            # Send reply
            await communication_hub.send_message(reply)
    
    # Register reply handler
    await communication_hub.register_message_handler('request', reply_handler)
    
    # Send request and wait for reply
    reply = await communication_hub.send_request(request, timeout=1.0)
    
    # Check that the reply was received
    assert reply is not None
    assert reply['type'] == 'reply'
    assert reply['payload']['message'] == 'Test reply'


@pytest.mark.asyncio
async def test_broadcast(communication_hub):
    """
    Test broadcast pattern.
    """
    # Create agent IDs
    sender_id = str(uuid.uuid4())
    receiver_ids = [str(uuid.uuid4()) for _ in range(3)]
    
    # Create message
    message = {
        'source_agent_id': sender_id,
        'type': 'broadcast',
        'payload': {
            'message': 'Test broadcast',
        },
    }
    
    # Broadcast message
    message_ids = await communication_hub.broadcast(message, receiver_ids)
    
    # Check that the message was broadcast to all receivers
    assert len(message_ids) == len(receiver_ids)
    
    # Receive messages
    for receiver_id in receiver_ids:
        received_message = await communication_hub.receive_message(receiver_id)
        
        # Check that the message was received
        assert received_message is not None
        assert received_message['type'] == 'broadcast'
        assert received_message['payload']['message'] == 'Test broadcast'
