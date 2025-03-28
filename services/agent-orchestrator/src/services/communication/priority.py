"""
Priority module for agent communication hub.

This module implements a priority queue system for agent messages:
- PriorityQueue: A priority queue implementation using Redis Sorted Sets
- PriorityDeterminer: Determines message priorities based on message attributes
- PriorityDispatcher: Dispatches messages to appropriate queues based on priority
- FairnessManager: Ensures fairness in message processing
- PriorityInheritanceManager: Implements priority inheritance for related messages
"""

import json
import logging
import time
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from uuid import UUID

logger = logging.getLogger(__name__)


class PriorityQueue:
    """Priority queue for messages using Redis Sorted Sets."""
    
    def __init__(self, redis_client, queue_name: str):
        """
        Initialize the priority queue.
        
        Args:
            redis_client: Redis client
            queue_name: Name of the queue
        """
        self.redis_client = redis_client
        self.queue_name = queue_name
    
    async def enqueue(self, message: Dict[str, Any], priority: int = 0) -> None:
        """
        Enqueue a message with a priority.
        
        Args:
            message: Message to enqueue
            priority: Priority of the message (higher values = higher priority)
        """
        # Serialize the message
        message_json = json.dumps(message)
        
        # Add the message to the sorted set with the priority as the score
        await self.redis_client.zadd(self.queue_name, {message_json: priority})
        logger.debug(f"Enqueued message in {self.queue_name} with priority {priority}")
    
    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """
        Dequeue the highest-priority message.
        
        Returns:
            Highest-priority message or None if the queue is empty
        """
        # Get the highest-priority message from the sorted set
        result = await self.redis_client.zpopmax(self.queue_name)
        
        if not result:
            return None
        
        # Deserialize the message
        message_json, _ = result[0]
        message = json.loads(message_json)
        logger.debug(f"Dequeued message from {self.queue_name}")
        
        return message
    
    async def peek(self) -> Optional[Dict[str, Any]]:
        """
        Peek at the highest-priority message without removing it.
        
        Returns:
            Highest-priority message or None if the queue is empty
        """
        # Get the highest-priority message from the sorted set
        result = await self.redis_client.zrange(self.queue_name, -1, -1, withscores=True)
        
        if not result:
            return None
        
        # Deserialize the message
        message_json, _ = result[0]
        return json.loads(message_json)
    
    async def remove(self, message: Dict[str, Any]) -> None:
        """
        Remove a message from the queue.
        
        Args:
            message: Message to remove
        """
        # Serialize the message
        message_json = json.dumps(message)
        
        # Remove the message from the sorted set
        await self.redis_client.zrem(self.queue_name, message_json)
        logger.debug(f"Removed message from {self.queue_name}")
    
    async def update_priority(self, message: Dict[str, Any], priority: int) -> None:
        """
        Update the priority of a message.
        
        Args:
            message: Message to update
            priority: New priority
        """
        # Serialize the message
        message_json = json.dumps(message)
        
        # Update the priority of the message in the sorted set
        await self.redis_client.zadd(self.queue_name, {message_json: priority})
        logger.debug(f"Updated message priority in {self.queue_name} to {priority}")
    
    async def get_length(self) -> int:
        """
        Get the number of messages in the queue.
        
        Returns:
            Number of messages
        """
        return await self.redis_client.zcard(self.queue_name)
    
    async def get_all(self) -> List[Tuple[Dict[str, Any], int]]:
        """
        Get all messages in the queue with their priorities.
        
        Returns:
            List of (message, priority) tuples
        """
        # Get all messages from the sorted set
        result = await self.redis_client.zrange(self.queue_name, 0, -1, withscores=True)
        
        # Deserialize the messages
        return [(json.loads(message_json), int(priority)) for message_json, priority in result]


class PriorityDeterminer:
    """Determiner for message priorities."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the priority determiner.
        
        Args:
            config: Priority configuration
        """
        self.config = config
    
    def determine_priority(self, message: Dict[str, Any]) -> int:
        """
        Determine the priority of a message.
        
        Args:
            message: Message to determine priority for
            
        Returns:
            Priority of the message
        """
        # Check if the message has an explicit priority
        if 'priority' in message:
            return message['priority']
        
        # Check if the message has a header that indicates priority
        if 'headers' in message and 'priority' in message['headers']:
            return message['headers']['priority']
        
        # Check if the message has a header that indicates urgency
        if 'headers' in message and 'urgent' in message['headers']:
            if message['headers']['urgent']:
                return self.config.get('urgent_priority', 5)
        
        # Check if the message is a response to a high-priority message
        if 'correlation_id' in message:
            correlation_id = message['correlation_id']
            # In a real implementation, we would look up the priority of the original message
            # For now, we'll just return a default priority
            return self.config.get('default_priority', 2)
        
        # Default priority
        return self.config.get('default_priority', 2)


class PriorityDispatcher:
    """Dispatcher for priority-based message processing."""
    
    def __init__(self, redis_client, config: Dict[str, Any]):
        """
        Initialize the priority dispatcher.
        
        Args:
            redis_client: Redis client
            config: Dispatcher configuration
        """
        self.redis_client = redis_client
        self.config = config
        self.queues = {}  # priority -> PriorityQueue
        
        # Create queues for each priority level
        for priority in range(self.config.get('priority_levels', 6)):
            self.queues[priority] = PriorityQueue(redis_client, f"messages:priority:{priority}")
        
        # Create a queue for each agent
        self.agent_queues = {}  # agent_id -> PriorityQueue
    
    async def dispatch(self, message: Dict[str, Any]) -> None:
        """
        Dispatch a message to the appropriate queue.
        
        Args:
            message: Message to dispatch
        """
        # Determine the priority of the message
        priority_determiner = PriorityDeterminer(self.config)
        priority = priority_determiner.determine_priority(message)
        
        # Ensure the priority is within the valid range
        priority = max(0, min(priority, self.config.get('priority_levels', 6) - 1))
        
        # Add the priority to the message
        message['priority'] = priority
        
        # Add the message to the appropriate queue
        await self.queues[priority].enqueue(message, priority)
        logger.debug(f"Dispatched message to priority queue {priority}")
        
        # If the message has a destination agent, add it to the agent's queue
        if 'destination' in message and message['destination'].get('type') == 'agent':
            agent_id = message['destination'].get('id')
            if agent_id:
                if agent_id not in self.agent_queues:
                    self.agent_queues[agent_id] = PriorityQueue(self.redis_client, f"messages:agent:{agent_id}")
                await self.agent_queues[agent_id].enqueue(message, priority)
                logger.debug(f"Dispatched message to agent queue {agent_id}")
    
    async def get_next_message(self, agent_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get the next message to process.
        
        Args:
            agent_id: ID of the agent to get a message for (optional)
            
        Returns:
            Next message to process or None if there are no messages
        """
        # If an agent ID is provided, get the next message for that agent
        if agent_id:
            if agent_id in self.agent_queues:
                message = await self.agent_queues[agent_id].dequeue()
                if message:
                    logger.debug(f"Got next message for agent {agent_id}")
                return message
            return None
        
        # Otherwise, get the next message from the highest-priority non-empty queue
        for priority in range(self.config.get('priority_levels', 6) - 1, -1, -1):
            message = await self.queues[priority].dequeue()
            if message:
                logger.debug(f"Got next message from priority queue {priority}")
                return message
        
        return None
    
    async def get_agent_queue_length(self, agent_id: str) -> int:
        """
        Get the number of messages in an agent's queue.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Number of messages
        """
        if agent_id in self.agent_queues:
            return await self.agent_queues[agent_id].get_length()
        return 0
    
    async def get_priority_queue_length(self, priority: int) -> int:
        """
        Get the number of messages in a priority queue.
        
        Args:
            priority: Priority level
            
        Returns:
            Number of messages
        """
        if priority in self.queues:
            return await self.queues[priority].get_length()
        return 0


class FairnessManager:
    """Manager for ensuring fairness in message processing."""
    
    def __init__(self, redis_client, config: Dict[str, Any]):
        """
        Initialize the fairness manager.
        
        Args:
            redis_client: Redis client
            config: Fairness configuration
        """
        self.redis_client = redis_client
        self.config = config
        self.last_processed = {}  # priority -> timestamp
    
    async def should_process_lower_priority(self) -> bool:
        """
        Determine if a lower-priority message should be processed.
        
        Returns:
            True if a lower-priority message should be processed, False otherwise
        """
        # Get the current time
        now = time.time()
        
        # Check if any priority level has been starved
        for priority in range(self.config.get('priority_levels', 6)):
            # Skip the highest priority
            if priority == self.config.get('priority_levels', 6) - 1:
                continue
            
            # Check if this priority level has been starved
            last_processed = self.last_processed.get(priority, 0)
            starvation_threshold = self.config.get('starvation_threshold', 60)  # 60 seconds
            
            if now - last_processed > starvation_threshold:
                logger.debug(f"Priority level {priority} has been starved, processing lower priority")
                return True
        
        return False
    
    async def update_last_processed(self, priority: int) -> None:
        """
        Update the last processed timestamp for a priority level.
        
        Args:
            priority: Priority level
        """
        self.last_processed[priority] = time.time()
        logger.debug(f"Updated last processed timestamp for priority {priority}")


class PriorityInheritanceManager:
    """Manager for priority inheritance."""
    
    def __init__(self, redis_client, config: Dict[str, Any]):
        """
        Initialize the priority inheritance manager.
        
        Args:
            redis_client: Redis client
            config: Inheritance configuration
        """
        self.redis_client = redis_client
        self.config = config
        self.conversation_priorities = {}  # conversation_id -> priority
    
    async def get_inherited_priority(self, message: Dict[str, Any]) -> int:
        """
        Get the inherited priority for a message.
        
        Args:
            message: Message to get inherited priority for
            
        Returns:
            Inherited priority
        """
        # Check if the message is part of a conversation
        conversation_id = message.get('headers', {}).get('conversation_id')
        if conversation_id:
            # Check if we have a priority for this conversation
            if conversation_id in self.conversation_priorities:
                logger.debug(f"Inherited priority {self.conversation_priorities[conversation_id]} from conversation {conversation_id}")
                return self.conversation_priorities[conversation_id]
        
        # Check if the message is a reply to another message
        correlation_id = message.get('correlation_id')
        if correlation_id:
            # In a real implementation, we would look up the priority of the original message
            # For now, we'll just return a default priority
            return self.config.get('default_priority', 2)
        
        # Default priority
        return self.config.get('default_priority', 2)
    
    async def update_conversation_priority(self, conversation_id: str, priority: int) -> None:
        """
        Update the priority for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            priority: New priority
        """
        self.conversation_priorities[conversation_id] = priority
        logger.debug(f"Updated conversation {conversation_id} priority to {priority}")
    
    async def boost_aging_messages(self, queue: PriorityQueue) -> None:
        """
        Boost the priority of aging messages.
        
        Args:
            queue: Queue to boost messages in
        """
        # Get all messages in the queue
        messages = await queue.get_all()
        
        # Get the current time
        now = time.time()
        
        # Boost the priority of aging messages
        for message, priority in messages:
            # Check if the message has a timestamp
            timestamp = message.get('timestamp')
            if timestamp:
                # Convert the timestamp to a Unix timestamp
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    message_time = dt.timestamp()
                    
                    # Check if the message is aging
                    age = now - message_time
                    aging_threshold = self.config.get('aging_threshold', 300)  # 5 minutes
                    
                    if age > aging_threshold:
                        # Boost the priority
                        boost_amount = self.config.get('aging_boost', 1)
                        new_priority = min(priority + boost_amount, self.config.get('priority_levels', 6) - 1)
                        
                        # Update the priority
                        await queue.update_priority(message, new_priority)
                        logger.debug(f"Boosted message priority from {priority} to {new_priority} due to age")
                except (ValueError, TypeError):
                    # If the timestamp is invalid, skip this message
                    continue
