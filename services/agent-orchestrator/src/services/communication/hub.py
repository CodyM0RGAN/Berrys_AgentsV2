"""
Communication hub for agent communication.

This module implements the CommunicationHub class, which ties together the routing and priority
components to provide a comprehensive communication system for agents.
"""

import logging
import json
import asyncio
import copy
import time
import uuid
from typing import List, Dict, Any, Optional, Set, Tuple, Callable
from uuid import UUID
from datetime import datetime

from .routing import TopicRouter, ContentRouter, RuleBasedRouter
from .priority import (
    PriorityQueue, 
    PriorityDeterminer, 
    PriorityDispatcher, 
    FairnessManager, 
    PriorityInheritanceManager
)
from .metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class CommunicationHub:
    """
    Communication hub for agent communication.
    
    This class ties together the routing and priority components to provide a comprehensive
    communication system for agents.
    """
    
    def __init__(self, redis_client, config: Dict[str, Any], metrics_collector: Optional[MetricsCollector] = None):
        """
        Initialize the communication hub.
        
        Args:
            redis_client: Redis client
            config: Hub configuration
            metrics_collector: Metrics collector for tracking message events
        """
        self.redis_client = redis_client
        self.config = config
        self.metrics_collector = metrics_collector
        
        # Initialize routing components
        self.topic_router = TopicRouter()
        self.content_router = ContentRouter()
        self.rule_router = RuleBasedRouter()
        
        # Initialize priority components
        self.priority_dispatcher = PriorityDispatcher(redis_client, config.get('priority', {}))
        self.fairness_manager = FairnessManager(redis_client, config.get('fairness', {}))
        self.priority_inheritance_manager = PriorityInheritanceManager(redis_client, config.get('inheritance', {}))
        
        # Initialize message handlers
        self.message_handlers = {}  # message_type -> list of handler functions
        
        # Initialize subscriptions
        self.agent_subscriptions = {}  # agent_id -> set of topics
        
        logger.info("Communication hub initialized")
    
    async def send_message(self, message: Dict[str, Any]) -> str:
        """
        Send a message through the communication hub.
        
        Args:
            message: Message to send
            
        Returns:
            ID of the sent message
        """
        # Ensure the message has required fields
        if 'source_agent_id' not in message:
            raise ValueError("Message must have a source_agent_id")
        
        if 'type' not in message:
            raise ValueError("Message must have a type")
        
        if 'payload' not in message:
            message['payload'] = {}
        
        if 'headers' not in message:
            message['headers'] = {}
        
        # Generate a message ID if not provided
        if 'id' not in message:
            message['id'] = str(uuid.uuid4())
        
        # Add timestamp if not provided
        if 'timestamp' not in message:
            message['timestamp'] = datetime.utcnow().isoformat()
        
        # Track message creation
        message_uuid = uuid.UUID(message['id'])
        source_agent_id = uuid.UUID(message['source_agent_id']) if message['source_agent_id'] else None
        destination_agent_id = None
        topic = message.get('headers', {}).get('topic')
        priority = message.get('priority', 0)
        correlation_id = uuid.UUID(message['correlation_id']) if 'correlation_id' in message else None
        
        if self.metrics_collector:
            await self.metrics_collector.track_message_created(
                message_id=message_uuid,
                source_agent_id=source_agent_id,
                destination_agent_id=destination_agent_id,
                topic=topic,
                priority=priority,
                correlation_id=correlation_id,
                metadata=message.get('headers')
            )
        
        # Route the message
        start_time = time.time()
        routed_message = await self._route_message(message)
        routing_time_ms = int((time.time() - start_time) * 1000)
        
        if not routed_message:
            logger.warning(f"Message {message['id']} was dropped during routing")
            
            # Track message failure
            if self.metrics_collector:
                await self.metrics_collector.track_message_failed(
                    message_id=message_uuid,
                    error_message="Message was dropped during routing"
                )
            
            return message['id']
        
        # Track message routing
        routing_path = None
        if 'destination' in routed_message:
            destination = routed_message['destination']
            if destination.get('type') == 'agent' and 'id' in destination:
                destination_agent_id = uuid.UUID(destination['id']) if destination['id'] else None
                routing_path = {"destination_type": "agent", "destination_id": destination['id']}
        
        if self.metrics_collector:
            await self.metrics_collector.track_message_routed(
                message_id=message_uuid,
                routing_path=routing_path
            )
        
        # Dispatch the message to the appropriate queue
        await self.priority_dispatcher.dispatch(routed_message)
        
        logger.info(f"Message {message['id']} sent from {message['source_agent_id']} to {routed_message.get('destination', {}).get('id', 'unknown')}")
        
        return message['id']
    
    async def receive_message(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Receive a message for an agent.
        
        Args:
            agent_id: ID of the agent to receive a message for
            
        Returns:
            Message or None if no message is available
        """
        # Check if we should process a lower-priority message for fairness
        process_lower_priority = await self.fairness_manager.should_process_lower_priority()
        
        # Get the next message for the agent
        message = await self.priority_dispatcher.get_next_message(agent_id)
        
        if message:
            # Update the fairness manager
            await self.fairness_manager.update_last_processed(message.get('priority', 0))
            
            # Track message delivery
            if self.metrics_collector and 'id' in message:
                message_uuid = uuid.UUID(message['id'])
                destination_agent_id = uuid.UUID(agent_id) if agent_id else None
                
                await self.metrics_collector.track_message_delivered(
                    message_id=message_uuid,
                    destination_agent_id=destination_agent_id
                )
            
            # Handle the message
            start_time = time.time()
            await self._handle_message(message)
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Track message processing
            if self.metrics_collector and 'id' in message:
                message_uuid = uuid.UUID(message['id'])
                
                await self.metrics_collector.track_message_processed(
                    message_id=message_uuid,
                    processing_time_ms=processing_time_ms
                )
            
            logger.info(f"Message {message['id']} received by {agent_id}")
            
            return message
        
        return None
    
    async def subscribe(self, agent_id: str, topic: str) -> None:
        """
        Subscribe an agent to a topic.
        
        Args:
            agent_id: ID of the agent
            topic: Topic to subscribe to
        """
        # Add the subscription to the topic router
        self.topic_router.subscribe(topic, agent_id)
        
        # Add the subscription to the agent's subscriptions
        if agent_id not in self.agent_subscriptions:
            self.agent_subscriptions[agent_id] = set()
        self.agent_subscriptions[agent_id].add(topic)
        
        # Update topic subscriber count
        if self.metrics_collector:
            subscriber_count = len(self.topic_router.get_subscribers(topic))
            await self.metrics_collector.update_topic_subscriber_count(
                topic=topic,
                subscriber_count=subscriber_count
            )
        
        logger.info(f"Agent {agent_id} subscribed to topic {topic}")
    
    async def unsubscribe(self, agent_id: str, topic: str) -> None:
        """
        Unsubscribe an agent from a topic.
        
        Args:
            agent_id: ID of the agent
            topic: Topic to unsubscribe from
        """
        # Remove the subscription from the topic router
        self.topic_router.unsubscribe(topic, agent_id)
        
        # Remove the subscription from the agent's subscriptions
        if agent_id in self.agent_subscriptions:
            self.agent_subscriptions[agent_id].discard(topic)
        
        # Update topic subscriber count
        if self.metrics_collector:
            subscriber_count = len(self.topic_router.get_subscribers(topic))
            await self.metrics_collector.update_topic_subscriber_count(
                topic=topic,
                subscriber_count=subscriber_count
            )
        
        logger.info(f"Agent {agent_id} unsubscribed from topic {topic}")
    
    async def get_subscriptions(self, agent_id: str) -> List[str]:
        """
        Get an agent's subscriptions.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of topics the agent is subscribed to
        """
        if agent_id in self.agent_subscriptions:
            return list(self.agent_subscriptions[agent_id])
        return []
    
    async def add_content_rule(self, condition: Callable[[Dict[str, Any]], bool], destination: str) -> None:
        """
        Add a content-based routing rule.
        
        Args:
            condition: Function that takes a message and returns True if the rule applies
            destination: Destination for messages that match the condition
        """
        self.content_router.add_rule(condition, destination)
        logger.info(f"Added content-based routing rule to destination {destination}")
    
    async def add_rule(self, rule: Dict[str, Any]) -> None:
        """
        Add a rule-based routing rule.
        
        Args:
            rule: Rule definition
        """
        self.rule_router.add_rule_from_dict(rule)
        logger.info(f"Added rule-based routing rule: {rule.get('name', 'unnamed')}")
    
    async def register_message_handler(self, message_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a handler for a message type.
        
        Args:
            message_type: Type of message to handle
            handler: Handler function
        """
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
        logger.info(f"Registered handler for message type {message_type}")
    
    async def publish_to_topic(self, topic: str, message: Dict[str, Any]) -> str:
        """
        Publish a message to a topic.
        
        Args:
            topic: Topic to publish to
            message: Message to publish
            
        Returns:
            ID of the published message
        """
        # Add the topic to the message headers
        if 'headers' not in message:
            message['headers'] = {}
        message['headers']['topic'] = topic
        
        # Get subscribers for the topic
        subscribers = self.topic_router.get_subscribers(topic)
        
        # Send the message to each subscriber
        for subscriber_id in subscribers:
            # Create a copy of the message for each subscriber
            subscriber_message = copy.deepcopy(message)
            subscriber_message['destination'] = {
                'type': 'agent',
                'id': subscriber_id
            }
            
            # Send the message
            await self.send_message(subscriber_message)
        
        logger.info(f"Published message {message.get('id', 'unknown')} to topic {topic} with {len(subscribers)} subscribers")
        
        return message.get('id', 'unknown')
    
    async def send_request(self, request: Dict[str, Any], timeout: float = 60.0) -> Optional[Dict[str, Any]]:
        """
        Send a request and wait for a reply.
        
        Args:
            request: Request to send
            timeout: Timeout in seconds
            
        Returns:
            Reply or None if the request timed out
        """
        # Generate a correlation ID
        correlation_id = str(uuid.uuid4())
        
        # Add the correlation ID to the request
        request['correlation_id'] = correlation_id
        
        # Add the reply_to field
        request['reply_to'] = request.get('source_agent_id')
        
        # Create a future for the reply
        reply_future = asyncio.Future()
        
        # Register a handler for the reply
        async def reply_handler(reply: Dict[str, Any]) -> None:
            if reply.get('correlation_id') == correlation_id:
                reply_future.set_result(reply)
        
        # Register the handler
        await self.register_message_handler('reply', reply_handler)
        
        # Send the request
        await self.send_message(request)
        
        # Wait for the reply
        try:
            reply = await asyncio.wait_for(reply_future, timeout)
            logger.info(f"Received reply for request {correlation_id}")
            return reply
        except asyncio.TimeoutError:
            logger.warning(f"Request {correlation_id} timed out")
            
            # Track message failure
            if self.metrics_collector and 'id' in request:
                message_uuid = uuid.UUID(request['id'])
                
                await self.metrics_collector.track_message_failed(
                    message_id=message_uuid,
                    error_message=f"Request timed out after {timeout} seconds"
                )
            
            return None
    
    async def broadcast(self, message: Dict[str, Any], agent_ids: List[str]) -> List[str]:
        """
        Broadcast a message to multiple agents.
        
        Args:
            message: Message to broadcast
            agent_ids: IDs of the agents to broadcast to
            
        Returns:
            List of message IDs
        """
        message_ids = []
        
        # Send the message to each agent
        for agent_id in agent_ids:
            # Create a copy of the message for each agent
            agent_message = copy.deepcopy(message)
            agent_message['destination'] = {
                'type': 'agent',
                'id': agent_id
            }
            
            # Send the message
            message_id = await self.send_message(agent_message)
            message_ids.append(message_id)
        
        logger.info(f"Broadcast message to {len(agent_ids)} agents")
        
        return message_ids
    
    async def _route_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Route a message according to the routing rules.
        
        Args:
            message: Message to route
            
        Returns:
            Routed message or None if the message was dropped
        """
        # If the message already has a destination, return it as is
        if 'destination' in message and message['destination'].get('type') == 'agent':
            return message
        
        # Check if the message has a topic
        topic = message.get('headers', {}).get('topic')
        if topic:
            # Get subscribers for the topic
            subscribers = self.topic_router.get_subscribers(topic)
            
            # If there are subscribers, route to the first one
            if subscribers:
                message['destination'] = {
                    'type': 'agent',
                    'id': subscribers[0]
                }
                return message
        
        # Check content-based routing rules
        destinations = self.content_router.get_destinations(message)
        if destinations:
            message['destination'] = {
                'type': 'agent',
                'id': destinations[0]
            }
            return message
        
        # Check rule-based routing
        routed_message = self.rule_router.route_message(message)
        if routed_message:
            return routed_message
        
        # If no routing rules matched, return the message as is
        # (it will be dropped if it has no destination)
        return message
    
    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handle a message.
        
        Args:
            message: Message to handle
        """
        # Get the message type
        message_type = message.get('type')
        
        # If there are handlers for this message type, call them
        if message_type in self.message_handlers:
            for handler in self.message_handlers[message_type]:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Error handling message {message.get('id', 'unknown')}: {str(e)}")
