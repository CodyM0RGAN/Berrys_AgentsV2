"""
Enhanced communication router for agent communication.

This module provides API endpoints for enhanced agent communication functionality.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..database import get_db
from ..dependencies import get_current_user, get_enhanced_communication_service
from ..models.api import (
    UserInfo,
    AgentCommunicationRequest,
    AgentCommunicationResponse,
    AgentCommunicationListResponse,
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
from ..services.enhanced_communication_service import EnhancedCommunicationService
from ..exceptions import (
    AgentNotFoundError,
    AgentCommunicationError,
    DatabaseError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/enhanced-communication",
    tags=["enhanced-communication"],
)


@router.post(
    "/send",
    response_model=AgentCommunicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a communication from one agent to another",
    description="Send a communication from one agent to another with enhanced routing and prioritization.",
)
async def send_communication(
    from_agent_id: UUID,
    communication_request: AgentCommunicationRequest,
    user: UserInfo = Depends(get_current_user),
    service: EnhancedCommunicationService = Depends(get_enhanced_communication_service),
):
    """
    Send a communication from one agent to another.
    
    Args:
        from_agent_id: Sender agent ID
        communication_request: Communication request
        user: Current authenticated user
        service: Enhanced communication service
        
    Returns:
        AgentCommunicationResponse: Communication response
    """
    try:
        response = await service.send_communication(from_agent_id, communication_request)
        return response
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AgentCommunicationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error sending communication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/receive/{agent_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Receive a message for an agent",
    description="Receive a message for an agent from the priority queue.",
)
async def receive_message(
    agent_id: UUID = Path(..., description="Agent ID"),
    user: UserInfo = Depends(get_current_user),
    service: EnhancedCommunicationService = Depends(get_enhanced_communication_service),
):
    """
    Receive a message for an agent.
    
    Args:
        agent_id: Agent ID
        user: Current authenticated user
        service: Enhanced communication service
        
    Returns:
        Dict[str, Any]: Message or empty dict if no message is available
    """
    try:
        message = await service.receive_message(agent_id)
        return message or {}
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error receiving message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/subscribe",
    response_model=TopicSubscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Subscribe an agent to a topic",
    description="Subscribe an agent to a topic for topic-based routing.",
)
async def subscribe_to_topic(
    request: TopicSubscriptionRequest,
    user: UserInfo = Depends(get_current_user),
    service: EnhancedCommunicationService = Depends(get_enhanced_communication_service),
):
    """
    Subscribe an agent to a topic.
    
    Args:
        request: Subscription request
        user: Current authenticated user
        service: Enhanced communication service
        
    Returns:
        TopicSubscriptionResponse: Subscription response
    """
    try:
        await service.subscribe(request.agent_id, request.topic)
        return TopicSubscriptionResponse(
            agent_id=request.agent_id,
            topic=request.topic,
            status="subscribed",
        )
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error subscribing to topic: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/unsubscribe",
    response_model=TopicSubscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Unsubscribe an agent from a topic",
    description="Unsubscribe an agent from a topic.",
)
async def unsubscribe_from_topic(
    request: TopicSubscriptionRequest,
    user: UserInfo = Depends(get_current_user),
    service: EnhancedCommunicationService = Depends(get_enhanced_communication_service),
):
    """
    Unsubscribe an agent from a topic.
    
    Args:
        request: Subscription request
        user: Current authenticated user
        service: Enhanced communication service
        
    Returns:
        TopicSubscriptionResponse: Subscription response
    """
    try:
        await service.unsubscribe(request.agent_id, request.topic)
        return TopicSubscriptionResponse(
            agent_id=request.agent_id,
            topic=request.topic,
            status="unsubscribed",
        )
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error unsubscribing from topic: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/subscriptions/{agent_id}",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="Get an agent's subscriptions",
    description="Get the list of topics an agent is subscribed to.",
)
async def get_subscriptions(
    agent_id: UUID = Path(..., description="Agent ID"),
    user: UserInfo = Depends(get_current_user),
    service: EnhancedCommunicationService = Depends(get_enhanced_communication_service),
):
    """
    Get an agent's subscriptions.
    
    Args:
        agent_id: Agent ID
        user: Current authenticated user
        service: Enhanced communication service
        
    Returns:
        List[str]: List of topics the agent is subscribed to
    """
    try:
        subscriptions = await service.get_subscriptions(agent_id)
        return subscriptions
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error getting subscriptions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/publish",
    response_model=TopicPublishResponse,
    status_code=status.HTTP_200_OK,
    summary="Publish a message to a topic",
    description="Publish a message to a topic for all subscribers.",
)
async def publish_to_topic(
    request: TopicPublishRequest,
    user: UserInfo = Depends(get_current_user),
    service: EnhancedCommunicationService = Depends(get_enhanced_communication_service),
):
    """
    Publish a message to a topic.
    
    Args:
        request: Publish request
        user: Current authenticated user
        service: Enhanced communication service
        
    Returns:
        TopicPublishResponse: Publish response
    """
    try:
        message_id = await service.publish_to_topic(
            request.agent_id,
            request.topic,
            request.content,
            request.message_type,
        )
        return TopicPublishResponse(
            message_id=message_id,
            agent_id=request.agent_id,
            topic=request.topic,
            status="published",
        )
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AgentCommunicationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error publishing to topic: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/broadcast",
    response_model=BroadcastResponse,
    status_code=status.HTTP_200_OK,
    summary="Broadcast a message to multiple agents",
    description="Broadcast a message to multiple agents.",
)
async def broadcast_message(
    request: BroadcastRequest,
    user: UserInfo = Depends(get_current_user),
    service: EnhancedCommunicationService = Depends(get_enhanced_communication_service),
):
    """
    Broadcast a message to multiple agents.
    
    Args:
        request: Broadcast request
        user: Current authenticated user
        service: Enhanced communication service
        
    Returns:
        BroadcastResponse: Broadcast response
    """
    try:
        message_ids = await service.broadcast(
            request.from_agent_id,
            request.to_agent_ids,
            request.content,
            request.message_type,
        )
        return BroadcastResponse(
            message_ids=message_ids,
            from_agent_id=request.from_agent_id,
            to_agent_ids=request.to_agent_ids,
            status="broadcast",
        )
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AgentCommunicationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error broadcasting message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/request",
    response_model=RequestReplyResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a request and wait for a reply",
    description="Send a request to an agent and wait for a reply.",
)
async def send_request(
    request: RequestReplyRequest,
    user: UserInfo = Depends(get_current_user),
    service: EnhancedCommunicationService = Depends(get_enhanced_communication_service),
):
    """
    Send a request and wait for a reply.
    
    Args:
        request: Request-reply request
        user: Current authenticated user
        service: Enhanced communication service
        
    Returns:
        RequestReplyResponse: Request-reply response
    """
    try:
        reply = await service.send_request(
            request.from_agent_id,
            request.to_agent_id,
            request.content,
            request.timeout,
        )
        
        if reply:
            return RequestReplyResponse(
                correlation_id=reply.get('correlation_id', ''),
                from_agent_id=request.from_agent_id,
                to_agent_id=request.to_agent_id,
                status="replied",
                reply=reply.get('payload', {}),
            )
        else:
            return RequestReplyResponse(
                correlation_id='',
                from_agent_id=request.from_agent_id,
                to_agent_id=request.to_agent_id,
                status="timeout",
                reply={},
            )
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error sending request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/rules",
    response_model=RoutingRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a routing rule",
    description="Add a rule-based routing rule.",
)
async def add_routing_rule(
    request: RoutingRuleRequest,
    user: UserInfo = Depends(get_current_user),
    service: EnhancedCommunicationService = Depends(get_enhanced_communication_service),
):
    """
    Add a routing rule.
    
    Args:
        request: Routing rule request
        user: Current authenticated user
        service: Enhanced communication service
        
    Returns:
        RoutingRuleResponse: Routing rule response
    """
    try:
        await service.add_rule(request.rule)
        return RoutingRuleResponse(
            rule_name=request.rule.get('name', 'unnamed'),
            status="added",
        )
    except Exception as e:
        logger.error(f"Error adding routing rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
