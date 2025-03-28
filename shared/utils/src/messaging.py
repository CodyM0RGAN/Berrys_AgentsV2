import os
import json
import asyncio
import aioredis
from typing import Dict, List, Any, Callable, Awaitable, Optional, Union
import logging
from uuid import uuid4
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
SERVICE_NAME = os.getenv("SERVICE_NAME", "mas-framework")


class MessageBroker:
    """
    Message broker for inter-service communication using Redis.
    """
    
    def __init__(self, redis_url: str = REDIS_URL, service_name: str = SERVICE_NAME):
        """
        Initialize the message broker.
        
        Args:
            redis_url: Redis connection URL
            service_name: Name of the service
        """
        self.redis_url = redis_url
        self.service_name = service_name
        self.redis = None
        self.pubsub = None
        self.handlers = {}
        self.running = False
        self.tasks = []
        
    async def connect(self) -> None:
        """
        Connect to Redis.
        """
        try:
            self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)
            self.pubsub = self.redis.pubsub()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
            
    async def disconnect(self) -> None:
        """
        Disconnect from Redis.
        """
        if self.running:
            await self.stop()
            
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
            
    async def publish(self, channel: str, message: Dict[str, Any]) -> None:
        """
        Publish a message to a channel.
        
        Args:
            channel: Channel to publish to
            message: Message to publish
        """
        if not self.redis:
            await self.connect()
            
        # Add metadata to message
        message_with_metadata = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "sender": self.service_name,
            "data": message,
        }
        
        # Publish message
        await self.redis.publish(channel, json.dumps(message_with_metadata))
        logger.debug(f"Published message to {channel}: {message_with_metadata['id']}")
            
    async def subscribe(
        self, 
        channel: str, 
        handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        Subscribe to a channel.
        
        Args:
            channel: Channel to subscribe to
            handler: Async function to handle messages
        """
        if not self.redis:
            await self.connect()
            
        # Store handler
        if channel not in self.handlers:
            self.handlers[channel] = []
        self.handlers[channel].append(handler)
        
        # Subscribe to channel
        await self.pubsub.subscribe(channel)
        logger.info(f"Subscribed to channel: {channel}")
        
        # Start message processing if not already running
        if not self.running:
            await self.start()
            
    async def unsubscribe(self, channel: str) -> None:
        """
        Unsubscribe from a channel.
        
        Args:
            channel: Channel to unsubscribe from
        """
        if not self.redis:
            return
            
        # Unsubscribe from channel
        await self.pubsub.unsubscribe(channel)
        
        # Remove handlers
        if channel in self.handlers:
            del self.handlers[channel]
            
        logger.info(f"Unsubscribed from channel: {channel}")
            
    async def start(self) -> None:
        """
        Start processing messages.
        """
        if self.running:
            return
            
        self.running = True
        self.tasks.append(asyncio.create_task(self._process_messages()))
        logger.info("Started message processing")
            
    async def stop(self) -> None:
        """
        Stop processing messages.
        """
        if not self.running:
            return
            
        self.running = False
        
        # Cancel tasks
        for task in self.tasks:
            task.cancel()
            
        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks = []
        
        logger.info("Stopped message processing")
            
    async def _process_messages(self) -> None:
        """
        Process messages from subscribed channels.
        """
        try:
            while self.running:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                
                if message:
                    channel = message["channel"]
                    data = message["data"]
                    
                    try:
                        # Parse message
                        message_data = json.loads(data)
                        
                        # Skip messages from self
                        if message_data.get("sender") == self.service_name:
                            continue
                            
                        # Call handlers
                        if channel in self.handlers:
                            for handler in self.handlers[channel]:
                                try:
                                    await handler(message_data)
                                except Exception as e:
                                    logger.error(f"Error in message handler: {str(e)}")
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON message: {data}")
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
                        
                # Yield to other tasks
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            logger.info("Message processing task cancelled")
        except Exception as e:
            logger.error(f"Error in message processing loop: {str(e)}")
            self.running = False


class EventBus:
    """
    Event bus for publishing and subscribing to events.
    """
    
    def __init__(self, broker: Optional[MessageBroker] = None):
        """
        Initialize the event bus.
        
        Args:
            broker: Message broker to use
        """
        self.broker = broker or MessageBroker()
        self.event_handlers = {}
        
    async def connect(self) -> None:
        """
        Connect to the message broker.
        """
        await self.broker.connect()
        
    async def disconnect(self) -> None:
        """
        Disconnect from the message broker.
        """
        await self.broker.disconnect()
        
    async def publish_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Publish an event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        channel = f"event:{event_type}"
        await self.broker.publish(channel, data)
        logger.debug(f"Published event: {event_type}")
        
    async def subscribe_to_event(
        self, 
        event_type: str, 
        handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        Subscribe to an event.
        
        Args:
            event_type: Type of event
            handler: Async function to handle events
        """
        channel = f"event:{event_type}"
        
        # Wrap handler to extract event data
        async def event_handler(message: Dict[str, Any]) -> None:
            await handler(message["data"])
            
        # Subscribe to channel
        await self.broker.subscribe(channel, event_handler)
        
        # Store handler for reference
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        
        logger.info(f"Subscribed to event: {event_type}")
        
    async def unsubscribe_from_event(self, event_type: str) -> None:
        """
        Unsubscribe from an event.
        
        Args:
            event_type: Type of event
        """
        channel = f"event:{event_type}"
        await self.broker.unsubscribe(channel)
        
        # Remove handlers
        if event_type in self.event_handlers:
            del self.event_handlers[event_type]
            
        logger.info(f"Unsubscribed from event: {event_type}")


class CommandBus:
    """
    Command bus for sending commands to services.
    """
    
    def __init__(self, broker: Optional[MessageBroker] = None):
        """
        Initialize the command bus.
        
        Args:
            broker: Message broker to use
        """
        self.broker = broker or MessageBroker()
        self.command_handlers = {}
        self.response_handlers = {}
        
    async def connect(self) -> None:
        """
        Connect to the message broker.
        """
        await self.broker.connect()
        
        # Subscribe to response channel
        response_channel = f"response:{self.broker.service_name}"
        await self.broker.subscribe(response_channel, self._handle_response)
        
    async def disconnect(self) -> None:
        """
        Disconnect from the message broker.
        """
        await self.broker.disconnect()
        
    async def send_command(
        self, 
        service: str, 
        command: str, 
        data: Dict[str, Any],
        wait_for_response: bool = False,
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """
        Send a command to a service.
        
        Args:
            service: Target service
            command: Command to send
            data: Command data
            wait_for_response: Whether to wait for a response
            timeout: Timeout in seconds
            
        Returns:
            Optional[Dict[str, Any]]: Response data if wait_for_response is True
        """
        command_id = str(uuid4())
        channel = f"command:{service}"
        
        # Prepare command message
        command_data = {
            "command_id": command_id,
            "command": command,
            "data": data,
            "response_channel": f"response:{self.broker.service_name}" if wait_for_response else None,
        }
        
        # Send command
        await self.broker.publish(channel, command_data)
        logger.debug(f"Sent command {command} to {service}: {command_id}")
        
        # Wait for response if requested
        if wait_for_response:
            # Create future for response
            response_future = asyncio.Future()
            self.response_handlers[command_id] = response_future
            
            try:
                # Wait for response with timeout
                return await asyncio.wait_for(response_future, timeout)
            except asyncio.TimeoutError:
                logger.error(f"Command {command_id} timed out after {timeout} seconds")
                del self.response_handlers[command_id]
                return None
            except Exception as e:
                logger.error(f"Error waiting for command response: {str(e)}")
                if command_id in self.response_handlers:
                    del self.response_handlers[command_id]
                return None
                
        return None
        
    async def register_command_handler(
        self, 
        command: str, 
        handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
    ) -> None:
        """
        Register a handler for a command.
        
        Args:
            command: Command to handle
            handler: Async function to handle command
        """
        # Store handler
        self.command_handlers[command] = handler
        
        # Subscribe to command channel if not already
        command_channel = f"command:{self.broker.service_name}"
        if command_channel not in self.broker.handlers:
            await self.broker.subscribe(command_channel, self._handle_command)
            
        logger.info(f"Registered handler for command: {command}")
        
    async def _handle_command(self, message: Dict[str, Any]) -> None:
        """
        Handle incoming commands.
        
        Args:
            message: Command message
        """
        data = message["data"]
        command_id = data.get("command_id")
        command = data.get("command")
        command_data = data.get("data", {})
        response_channel = data.get("response_channel")
        
        logger.debug(f"Received command: {command} ({command_id})")
        
        # Check if we have a handler for this command
        if command in self.command_handlers:
            try:
                # Call handler
                result = await self.command_handlers[command](command_data)
                
                # Send response if requested
                if response_channel:
                    response_data = {
                        "command_id": command_id,
                        "success": True,
                        "data": result,
                    }
                    await self.broker.publish(response_channel, response_data)
                    logger.debug(f"Sent response for command: {command} ({command_id})")
            except Exception as e:
                logger.error(f"Error handling command {command}: {str(e)}")
                
                # Send error response if requested
                if response_channel:
                    error_data = {
                        "command_id": command_id,
                        "success": False,
                        "error": str(e),
                    }
                    await self.broker.publish(response_channel, error_data)
                    logger.debug(f"Sent error response for command: {command} ({command_id})")
        else:
            logger.warning(f"No handler for command: {command}")
            
            # Send error response if requested
            if response_channel:
                error_data = {
                    "command_id": command_id,
                    "success": False,
                    "error": f"No handler for command: {command}",
                }
                await self.broker.publish(response_channel, error_data)
                logger.debug(f"Sent error response for command: {command} ({command_id})")
                
    async def _handle_response(self, message: Dict[str, Any]) -> None:
        """
        Handle command responses.
        
        Args:
            message: Response message
        """
        data = message["data"]
        command_id = data.get("command_id")
        success = data.get("success", False)
        
        # Check if we're waiting for this response
        if command_id in self.response_handlers:
            response_future = self.response_handlers[command_id]
            
            # Set result or exception
            if success:
                response_future.set_result(data.get("data", {}))
            else:
                response_future.set_exception(Exception(data.get("error", "Unknown error")))
                
            # Remove future
            del self.response_handlers[command_id]
            logger.debug(f"Handled response for command: {command_id}")
        else:
            logger.warning(f"Received response for unknown command: {command_id}")


# Singleton instances
message_broker = None
event_bus = None
command_bus = None


async def init_messaging(service_name: str = SERVICE_NAME) -> None:
    """
    Initialize messaging components.
    
    Args:
        service_name: Name of the service
    """
    global message_broker, event_bus, command_bus
    
    # Create message broker
    message_broker = MessageBroker(service_name=service_name)
    await message_broker.connect()
    
    # Create event bus
    event_bus = EventBus(broker=message_broker)
    
    # Create command bus
    command_bus = CommandBus(broker=message_broker)
    await command_bus.connect()
    
    logger.info(f"Messaging initialized for service: {service_name}")


async def close_messaging() -> None:
    """
    Close messaging components.
    """
    global message_broker, event_bus, command_bus
    
    # Close command bus
    if command_bus:
        await command_bus.disconnect()
        command_bus = None
        
    # Close event bus
    if event_bus:
        await event_bus.disconnect()
        event_bus = None
        
    # Close message broker
    if message_broker:
        await message_broker.disconnect()
        message_broker = None
        
    logger.info("Messaging closed")


def get_event_bus() -> EventBus:
    """
    Get the event bus instance.
    
    Returns:
        EventBus: Event bus instance
    """
    if not event_bus:
        raise RuntimeError("Event bus not initialized. Call init_messaging() first.")
    return event_bus


def get_command_bus() -> CommandBus:
    """
    Get the command bus instance.
    
    Returns:
        CommandBus: Command bus instance
    """
    if not command_bus:
        raise RuntimeError("Command bus not initialized. Call init_messaging() first.")
    return command_bus
