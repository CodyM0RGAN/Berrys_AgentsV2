"""
Tests for the enhanced communication models.
"""

import pytest
import uuid
from datetime import datetime
from typing import Dict, Any, List

from pydantic import ValidationError

from ...src.models.enhanced_communication import (
    TopicSubscriptionRequest,
    TopicSubscriptionResponse,
    TopicPublishRequest,
    TopicPublishResponse,
    BroadcastRequest,
    BroadcastResponse,
    RequestReplyRequest,
    RequestReplyResponse,
    RoutingRuleRequest,
    RoutingRuleResponse,
)


def test_topic_subscription_request():
    """
    Test TopicSubscriptionRequest model.
    """
    # Create a valid request
    agent_id = uuid.uuid4()
    request = TopicSubscriptionRequest(
        agent_id=agent_id,
        topic="test.topic",
    )
    
    # Check the request
    assert request.agent_id == agent_id
    assert request.topic == "test.topic"
    
    # Test validation
    with pytest.raises(ValidationError):
        # Missing agent_id
        TopicSubscriptionRequest(
            topic="test.topic",
        )
    
    with pytest.raises(ValidationError):
        # Missing topic
        TopicSubscriptionRequest(
            agent_id=agent_id,
        )


def test_topic_subscription_response():
    """
    Test TopicSubscriptionResponse model.
    """
    # Create a valid response
    agent_id = uuid.uuid4()
    response = TopicSubscriptionResponse(
        agent_id=agent_id,
        topic="test.topic",
        status="subscribed",
    )
    
    # Check the response
    assert response.agent_id == agent_id
    assert response.topic == "test.topic"
    assert response.status == "subscribed"
    
    # Test validation
    with pytest.raises(ValidationError):
        # Missing agent_id
        TopicSubscriptionResponse(
            topic="test.topic",
            status="subscribed",
        )
    
    with pytest.raises(ValidationError):
        # Missing topic
        TopicSubscriptionResponse(
            agent_id=agent_id,
            status="subscribed",
        )
    
    with pytest.raises(ValidationError):
        # Missing status
        TopicSubscriptionResponse(
            agent_id=agent_id,
            topic="test.topic",
        )


def test_topic_publish_request():
    """
    Test TopicPublishRequest model.
    """
    # Create a valid request
    agent_id = uuid.uuid4()
    request = TopicPublishRequest(
        agent_id=agent_id,
        topic="test.topic",
        content={"message": "Test message"},
    )
    
    # Check the request
    assert request.agent_id == agent_id
    assert request.topic == "test.topic"
    assert request.content == {"message": "Test message"}
    assert request.message_type == "topic_message"  # Default value
    
    # Test with custom message type
    request = TopicPublishRequest(
        agent_id=agent_id,
        topic="test.topic",
        content={"message": "Test message"},
        message_type="custom_type",
    )
    
    # Check the request
    assert request.message_type == "custom_type"
    
    # Test validation
    with pytest.raises(ValidationError):
        # Missing agent_id
        TopicPublishRequest(
            topic="test.topic",
            content={"message": "Test message"},
        )
    
    with pytest.raises(ValidationError):
        # Missing topic
        TopicPublishRequest(
            agent_id=agent_id,
            content={"message": "Test message"},
        )
    
    with pytest.raises(ValidationError):
        # Missing content
        TopicPublishRequest(
            agent_id=agent_id,
            topic="test.topic",
        )


def test_topic_publish_response():
    """
    Test TopicPublishResponse model.
    """
    # Create a valid response
    agent_id = uuid.uuid4()
    response = TopicPublishResponse(
        message_id="msg_123456789",
        agent_id=agent_id,
        topic="test.topic",
        status="published",
    )
    
    # Check the response
    assert response.message_id == "msg_123456789"
    assert response.agent_id == agent_id
    assert response.topic == "test.topic"
    assert response.status == "published"
    
    # Test validation
    with pytest.raises(ValidationError):
        # Missing message_id
        TopicPublishResponse(
            agent_id=agent_id,
            topic="test.topic",
            status="published",
        )
    
    with pytest.raises(ValidationError):
        # Missing agent_id
        TopicPublishResponse(
            message_id="msg_123456789",
            topic="test.topic",
            status="published",
        )
    
    with pytest.raises(ValidationError):
        # Missing topic
        TopicPublishResponse(
            message_id="msg_123456789",
            agent_id=agent_id,
            status="published",
        )
    
    with pytest.raises(ValidationError):
        # Missing status
        TopicPublishResponse(
            message_id="msg_123456789",
            agent_id=agent_id,
            topic="test.topic",
        )


def test_broadcast_request():
    """
    Test BroadcastRequest model.
    """
    # Create a valid request
    from_agent_id = uuid.uuid4()
    to_agent_ids = [uuid.uuid4(), uuid.uuid4()]
    request = BroadcastRequest(
        from_agent_id=from_agent_id,
        to_agent_ids=to_agent_ids,
        content={"message": "Test broadcast"},
    )
    
    # Check the request
    assert request.from_agent_id == from_agent_id
    assert request.to_agent_ids == to_agent_ids
    assert request.content == {"message": "Test broadcast"}
    assert request.message_type == "broadcast"  # Default value
    
    # Test with custom message type
    request = BroadcastRequest(
        from_agent_id=from_agent_id,
        to_agent_ids=to_agent_ids,
        content={"message": "Test broadcast"},
        message_type="custom_type",
    )
    
    # Check the request
    assert request.message_type == "custom_type"
    
    # Test validation
    with pytest.raises(ValidationError):
        # Missing from_agent_id
        BroadcastRequest(
            to_agent_ids=to_agent_ids,
            content={"message": "Test broadcast"},
        )
    
    with pytest.raises(ValidationError):
        # Missing to_agent_ids
        BroadcastRequest(
            from_agent_id=from_agent_id,
            content={"message": "Test broadcast"},
        )
    
    with pytest.raises(ValidationError):
        # Missing content
        BroadcastRequest(
            from_agent_id=from_agent_id,
            to_agent_ids=to_agent_ids,
        )


def test_broadcast_response():
    """
    Test BroadcastResponse model.
    """
    # Create a valid response
    from_agent_id = uuid.uuid4()
    to_agent_ids = [uuid.uuid4(), uuid.uuid4()]
    response = BroadcastResponse(
        message_ids=["msg_123456789", "msg_987654321"],
        from_agent_id=from_agent_id,
        to_agent_ids=to_agent_ids,
        status="broadcast",
    )
    
    # Check the response
    assert response.message_ids == ["msg_123456789", "msg_987654321"]
    assert response.from_agent_id == from_agent_id
    assert response.to_agent_ids == to_agent_ids
    assert response.status == "broadcast"
    
    # Test validation
    with pytest.raises(ValidationError):
        # Missing message_ids
        BroadcastResponse(
            from_agent_id=from_agent_id,
            to_agent_ids=to_agent_ids,
            status="broadcast",
        )
    
    with pytest.raises(ValidationError):
        # Missing from_agent_id
        BroadcastResponse(
            message_ids=["msg_123456789", "msg_987654321"],
            to_agent_ids=to_agent_ids,
            status="broadcast",
        )
    
    with pytest.raises(ValidationError):
        # Missing to_agent_ids
        BroadcastResponse(
            message_ids=["msg_123456789", "msg_987654321"],
            from_agent_id=from_agent_id,
            status="broadcast",
        )
    
    with pytest.raises(ValidationError):
        # Missing status
        BroadcastResponse(
            message_ids=["msg_123456789", "msg_987654321"],
            from_agent_id=from_agent_id,
            to_agent_ids=to_agent_ids,
        )


def test_request_reply_request():
    """
    Test RequestReplyRequest model.
    """
    # Create a valid request
    from_agent_id = uuid.uuid4()
    to_agent_id = uuid.uuid4()
    request = RequestReplyRequest(
        from_agent_id=from_agent_id,
        to_agent_id=to_agent_id,
        content={"message": "Test request"},
    )
    
    # Check the request
    assert request.from_agent_id == from_agent_id
    assert request.to_agent_id == to_agent_id
    assert request.content == {"message": "Test request"}
    assert request.timeout == 60.0  # Default value
    
    # Test with custom timeout
    request = RequestReplyRequest(
        from_agent_id=from_agent_id,
        to_agent_id=to_agent_id,
        content={"message": "Test request"},
        timeout=30.0,
    )
    
    # Check the request
    assert request.timeout == 30.0
    
    # Test validation
    with pytest.raises(ValidationError):
        # Missing from_agent_id
        RequestReplyRequest(
            to_agent_id=to_agent_id,
            content={"message": "Test request"},
        )
    
    with pytest.raises(ValidationError):
        # Missing to_agent_id
        RequestReplyRequest(
            from_agent_id=from_agent_id,
            content={"message": "Test request"},
        )
    
    with pytest.raises(ValidationError):
        # Missing content
        RequestReplyRequest(
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
        )


def test_request_reply_response():
    """
    Test RequestReplyResponse model.
    """
    # Create a valid response
    from_agent_id = uuid.uuid4()
    to_agent_id = uuid.uuid4()
    response = RequestReplyResponse(
        correlation_id="corr_123456789",
        from_agent_id=from_agent_id,
        to_agent_id=to_agent_id,
        status="replied",
        reply={"message": "Test reply"},
    )
    
    # Check the response
    assert response.correlation_id == "corr_123456789"
    assert response.from_agent_id == from_agent_id
    assert response.to_agent_id == to_agent_id
    assert response.status == "replied"
    assert response.reply == {"message": "Test reply"}
    
    # Test validation
    with pytest.raises(ValidationError):
        # Missing correlation_id
        RequestReplyResponse(
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            status="replied",
            reply={"message": "Test reply"},
        )
    
    with pytest.raises(ValidationError):
        # Missing from_agent_id
        RequestReplyResponse(
            correlation_id="corr_123456789",
            to_agent_id=to_agent_id,
            status="replied",
            reply={"message": "Test reply"},
        )
    
    with pytest.raises(ValidationError):
        # Missing to_agent_id
        RequestReplyResponse(
            correlation_id="corr_123456789",
            from_agent_id=from_agent_id,
            status="replied",
            reply={"message": "Test reply"},
        )
    
    with pytest.raises(ValidationError):
        # Missing status
        RequestReplyResponse(
            correlation_id="corr_123456789",
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            reply={"message": "Test reply"},
        )
    
    with pytest.raises(ValidationError):
        # Missing reply
        RequestReplyResponse(
            correlation_id="corr_123456789",
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            status="replied",
        )


def test_routing_rule_request():
    """
    Test RoutingRuleRequest model.
    """
    # Create a valid request
    request = RoutingRuleRequest(
        rule={
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
    )
    
    # Check the request
    assert request.rule["name"] == "test_rule"
    assert request.rule["conditions"][0]["field"] == "task_type"
    assert request.rule["actions"][0]["type"] == "route"
    assert request.rule["is_terminal"] is True
    
    # Test validation
    with pytest.raises(ValidationError):
        # Missing rule
        RoutingRuleRequest()


def test_routing_rule_response():
    """
    Test RoutingRuleResponse model.
    """
    # Create a valid response
    response = RoutingRuleResponse(
        rule_name="test_rule",
        status="added",
    )
    
    # Check the response
    assert response.rule_name == "test_rule"
    assert response.status == "added"
    
    # Test validation
    with pytest.raises(ValidationError):
        # Missing rule_name
        RoutingRuleResponse(
            status="added",
        )
    
    with pytest.raises(ValidationError):
        # Missing status
        RoutingRuleResponse(
            rule_name="test_rule",
        )
