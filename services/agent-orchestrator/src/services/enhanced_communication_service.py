"""
Enhanced communication service for agent communication.

This module implements an enhanced version of the CommunicationService class that integrates
with the new CommunicationHub to provide advanced routing and prioritization capabilities.
It also includes metrics collection and alerting functionality.
"""

import logging
import json
import asyncio
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple, Dict, Any, Callable
from uuid import UUID
from datetime import datetime

from shared.utils.src.messaging import EventBus, CommandBus
from shared.utils.src.redis import get_redis_client

from ..config import AgentOrchestratorConfig
from ..exceptions import (
    AgentNotFoundError,
    AgentCommunicationError,
    DatabaseError,
)
from ..models.api import (
    AgentCommunicationRequest,
    AgentCommunicationResponse,
)
from ..models.internal import (
    AgentModel,
    AgentCommunicationModel,
)

from .communication.hub import CommunicationHub
from .communication.metrics_collector import MetricsCollector
from .communication.alerting_service import AlertingService

logger = logging.getLogger(__name__)


class EnhancedCommunicationService:
    """
    Enhanced service for agent communication operations.
    
    This service extends the basic CommunicationService with advanced routing and
    prioritization capabilities provided by the CommunicationHub.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        command_bus: CommandBus,
        settings: AgentOrchestratorConfig,
    ):
        """
        Initialize the enhanced communication service.
        
        Args:
            db: Database session
            event_bus: Event bus
            command_bus: Command bus
            settings: Application settings
        """
        self.db = db
        self.event_bus = event_bus
        self.command_bus = command_bus
        self.settings = settings
        
        # Initialize Redis client
        self.redis_client = get_redis_client(settings.redis_url)
        
        # Initialize metrics collector
        self.metrics_collector = MetricsCollector(lambda: db)
        
        # Initialize alerting service
        self.alerting_service = AlertingService(lambda: db, self.metrics_collector)
        
        # Initialize communication hub
        self.hub = CommunicationHub(
            self.redis_client, 
            {
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
            },
            metrics_collector=self.metrics_collector
        )
        
        # Start the alerting service
        asyncio.create_task(self.alerting_service.start())
        
        # Register notification handlers
        self._register_notification_handlers()
        
        logger.info("Enhanced communication service initialized")
    
    def _register_notification_handlers(self):
        """
        Register notification handlers for the alerting service.
        """
        # Register email notification handler
        self.alerting_service.register_notification_handler(
            "email",
            self._handle_email_notification
        )
        
        # Register dashboard notification handler
        self.alerting_service.register_notification_handler(
            "dashboard",
            self._handle_dashboard_notification
        )
        
        logger.info("Notification handlers registered")
    
    async def _handle_email_notification(self, config, alert_history, channel_config):
        """
        Handle email notifications.
        
        Args:
            config: Alert configuration
            alert_history: Alert history record
            channel_config: Channel configuration
        """
        # In a real implementation, this would send an email
        # For now, just log the notification
        logger.info(f"Email notification for alert {config.name}: {alert_history.message}")
        
        # Publish event
        await self.event_bus.publish_event(
            "alert.notification.email",
            {
                "alert_id": str(alert_history.id),
                "alert_configuration_id": str(config.id),
                "message": alert_history.message,
                "recipients": channel_config.get("recipients", []),
            }
        )
    
    async def _handle_dashboard_notification(self, config, alert_history, channel_config):
        """
        Handle dashboard notifications.
        
        Args:
            config: Alert configuration
            alert_history: Alert history record
            channel_config: Channel configuration
        """
        # In a real implementation, this would send a notification to the dashboard
        # For now, just log the notification
        logger.info(f"Dashboard notification for alert {config.name}: {alert_history.message}")
        
        # Publish event
        await self.event_bus.publish_event(
            "alert.notification.dashboard",
            {
                "alert_id": str(alert_history.id),
                "alert_configuration_id": str(config.id),
                "message": alert_history.message,
                "severity": config.severity.value,
            }
        )
    
    async def send_communication(
        self,
        from_agent_id: UUID,
        communication_request: AgentCommunicationRequest,
    ) -> AgentCommunicationResponse:
        """
        Send a communication from one agent to another.
        
        Args:
            from_agent_id: Sender agent ID
            communication_request: Communication request
            
        Returns:
            AgentCommunicationResponse: Communication response
            
        Raises:
            AgentNotFoundError: If agent not found
            AgentCommunicationError: If communication fails
            DatabaseError: If database operation fails
        """
        try:
            # Check if sender agent exists
            query = select(AgentModel).where(AgentModel.id == from_agent_id)
            result = await self.db.execute(query)
            from_agent = result.scalars().first()
            
            if not from_agent:
                raise AgentNotFoundError(from_agent_id)
            
            # Check if recipient agent exists
            to_agent_id = communication_request.to_agent_id
            query = select(AgentModel).where(AgentModel.id == to_agent_id)
            result = await self.db.execute(query)
            to_agent = result.scalars().first()
            
            if not to_agent:
                raise AgentNotFoundError(to_agent_id)
            
            # Create communication record
            communication = AgentCommunicationModel(
                from_agent_id=from_agent_id,
                to_agent_id=to_agent_id,
                type=communication_request.type,
                content=communication_request.content,
                status="sent",
            )
            
            self.db.add(communication)
            await self.db.commit()
            await self.db.refresh(communication)
            
            # Create message for the hub
            message = {
                'id': str(communication.id),
                'source_agent_id': str(from_agent_id),
                'destination': {
                    'type': 'agent',
                    'id': str(to_agent_id),
                },
                'type': communication_request.type,
                'payload': communication_request.content,
                'headers': {
                    'project_id': str(from_agent.project_id),
                },
                'timestamp': communication.created_at.isoformat(),
            }
            
            # Send the message through the hub
            await self.hub.send_message(message)
            
            # Create response
            response = AgentCommunicationResponse(
                communication_id=communication.id,
                from_agent_id=from_agent_id,
                to_agent_id=to_agent_id,
                status="sent",
                timestamp=communication.created_at,
            )
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.communication.sent",
                {
                    "communication_id": str(communication.id),
                    "from_agent_id": str(from_agent_id),
                    "to_agent_id": str(to_agent_id),
                    "type": communication.type,
                    "project_id": str(from_agent.project_id),
                }
            )
            
            return response
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error sending communication from {from_agent_id} to {communication_request.to_agent_id}: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
            
            raise AgentCommunicationError(
                from_agent_id=from_agent_id,
                to_agent_id=communication_request.to_agent_id,
                message=f"Failed to send communication: {str(e)}",
            )
    
    async def mark_as_delivered(
        self,
        communication_id: UUID,
    ) -> AgentCommunicationModel:
        """
        Mark a communication as delivered.
        
        Args:
            communication_id: Communication ID
            
        Returns:
            AgentCommunicationModel: Updated communication
            
        Raises:
            AgentCommunicationError: If communication not found
            DatabaseError: If database operation fails
        """
        try:
            # Query communication
            query = select(AgentCommunicationModel).where(AgentCommunicationModel.id == communication_id)
            result = await self.db.execute(query)
            communication = result.scalars().first()
            
            if not communication:
                raise AgentCommunicationError(
                    from_agent_id=UUID('00000000-0000-0000-0000-000000000000'),
                    to_agent_id=UUID('00000000-0000-0000-0000-000000000000'),
                    message=f"Communication {communication_id} not found",
                )
            
            # Update status and delivered timestamp
            communication.status = "delivered"
            communication.delivered_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(communication)
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.communication.delivered",
                {
                    "communication_id": str(communication.id),
                    "from_agent_id": str(communication.from_agent_id),
                    "to_agent_id": str(communication.to_agent_id),
                }
            )
            
            return communication
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error marking communication {communication_id} as delivered: {str(e)}")
            
            if isinstance(e, AgentCommunicationError):
                raise
            
            raise DatabaseError(f"Failed to mark communication as delivered: {str(e)}")
    
    async def get_communications_for_agent(
        self,
        agent_id: UUID,
        page: int = 1,
        page_size: int = 20,
        direction: str = "both",
        status: Optional[str] = None,
    ) -> Tuple[List[AgentCommunicationModel], int]:
        """
        Get communications for an agent.
        
        Args:
            agent_id: Agent ID
            page: Page number
            page_size: Page size
            direction: Direction of communications ("sent", "received", or "both")
            status: Filter by status
            
        Returns:
            Tuple[List[AgentCommunicationModel], int]: List of communications and total count
            
        Raises:
            AgentNotFoundError: If agent not found
            DatabaseError: If database operation fails
        """
        try:
            # Check if agent exists
            query = select(AgentModel).where(AgentModel.id == agent_id)
            result = await self.db.execute(query)
            agent = result.scalars().first()
            
            if not agent:
                raise AgentNotFoundError(agent_id)
            
            # Build query
            if direction == "sent":
                query = select(AgentCommunicationModel).where(AgentCommunicationModel.from_agent_id == agent_id)
                count_query = select(func.count()).where(AgentCommunicationModel.from_agent_id == agent_id)
            elif direction == "received":
                query = select(AgentCommunicationModel).where(AgentCommunicationModel.to_agent_id == agent_id)
                count_query = select(func.count()).where(AgentCommunicationModel.to_agent_id == agent_id)
            else:  # "both"
                query = select(AgentCommunicationModel).where(
                    or_(
                        AgentCommunicationModel.from_agent_id == agent_id,
                        AgentCommunicationModel.to_agent_id == agent_id,
                    )
                )
                count_query = select(func.count()).where(
                    or_(
                        AgentCommunicationModel.from_agent_id == agent_id,
                        AgentCommunicationModel.to_agent_id == agent_id,
                    )
                )
            
            # Apply status filter
            if status:
                query = query.where(AgentCommunicationModel.status == status)
                count_query = count_query.where(AgentCommunicationModel.status == status)
            
            # Get total count
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()
            
            # Apply pagination and ordering
            query = (
                query
                .order_by(AgentCommunicationModel.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            
            # Execute query
            result = await self.db.execute(query)
            communications = result.scalars().all()
            
            return list(communications), total
        except Exception as e:
            logger.error(f"Error getting communications for agent {agent_id}: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
            
            raise DatabaseError(f"Failed to get communications: {str(e)}")
    
    async def get_communication(
        self,
        communication_id: UUID,
    ) -> Optional[AgentCommunicationModel]:
        """
        Get a communication by ID.
        
        Args:
            communication_id: Communication ID
            
        Returns:
            Optional[AgentCommunicationModel]: Communication if found, None otherwise
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Query communication
            query = select(AgentCommunicationModel).where(AgentCommunicationModel.id == communication_id)
            result = await self.db.execute(query)
            communication = result.scalars().first()
            
            return communication
        except Exception as e:
            logger.error(f"Error getting communication {communication_id}: {str(e)}")
            raise DatabaseError(f"Failed to get communication: {str(e)}")
    
    async def receive_message(
        self,
        agent_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Receive a message for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Optional[Dict[str, Any]]: Message or None if no message is available
            
        Raises:
            AgentNotFoundError: If agent not found
        """
        try:
            # Check if agent exists
            query = select(AgentModel).where(AgentModel.id == agent_id)
            result = await self.db.execute(query)
            agent = result.scalars().first()
            
            if not agent:
                raise AgentNotFoundError(agent_id)
            
            # Receive a message from the hub
            message = await self.hub.receive_message(str(agent_id))
            
            if message:
                # Mark the communication as delivered
                communication_id = message.get('id')
                if communication_id:
                    try:
                        await self.mark_as_delivered(UUID(communication_id))
                    except Exception as e:
                        logger.error(f"Error marking communication {communication_id} as delivered: {str(e)}")
            
            return message
        except Exception as e:
            logger.error(f"Error receiving message for agent {agent_id}: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
            
            return None
    
    async def subscribe(
        self,
        agent_id: UUID,
        topic: str,
    ) -> None:
        """
        Subscribe an agent to a topic.
        
        Args:
            agent_id: Agent ID
            topic: Topic to subscribe to
            
        Raises:
            AgentNotFoundError: If agent not found
        """
        try:
            # Check if agent exists
            query = select(AgentModel).where(AgentModel.id == agent_id)
            result = await self.db.execute(query)
            agent = result.scalars().first()
            
            if not agent:
                raise AgentNotFoundError(agent_id)
            
            # Subscribe the agent to the topic
            await self.hub.subscribe(str(agent_id), topic)
            
            logger.info(f"Agent {agent_id} subscribed to topic {topic}")
        except Exception as e:
            logger.error(f"Error subscribing agent {agent_id} to topic {topic}: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
    
    async def unsubscribe(
        self,
        agent_id: UUID,
        topic: str,
    ) -> None:
        """
        Unsubscribe an agent from a topic.
        
        Args:
            agent_id: Agent ID
            topic: Topic to unsubscribe from
            
        Raises:
            AgentNotFoundError: If agent not found
        """
        try:
            # Check if agent exists
            query = select(AgentModel).where(AgentModel.id == agent_id)
            result = await self.db.execute(query)
            agent = result.scalars().first()
            
            if not agent:
                raise AgentNotFoundError(agent_id)
            
            # Unsubscribe the agent from the topic
            await self.hub.unsubscribe(str(agent_id), topic)
            
            logger.info(f"Agent {agent_id} unsubscribed from topic {topic}")
        except Exception as e:
            logger.error(f"Error unsubscribing agent {agent_id} from topic {topic}: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
    
    async def get_subscriptions(
        self,
        agent_id: UUID,
    ) -> List[str]:
        """
        Get an agent's subscriptions.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            List[str]: List of topics the agent is subscribed to
            
        Raises:
            AgentNotFoundError: If agent not found
        """
        try:
            # Check if agent exists
            query = select(AgentModel).where(AgentModel.id == agent_id)
            result = await self.db.execute(query)
            agent = result.scalars().first()
            
            if not agent:
                raise AgentNotFoundError(agent_id)
            
            # Get the agent's subscriptions
            subscriptions = await self.hub.get_subscriptions(str(agent_id))
            
            return subscriptions
        except Exception as e:
            logger.error(f"Error getting subscriptions for agent {agent_id}: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
            
            return []
    
    async def publish_to_topic(
        self,
        agent_id: UUID,
        topic: str,
        content: Dict[str, Any],
        message_type: str = "topic_message",
    ) -> str:
        """
        Publish a message to a topic.
        
        Args:
            agent_id: ID of the publishing agent
            topic: Topic to publish to
            content: Message content
            message_type: Type of message
            
        Returns:
            str: ID of the published message
            
        Raises:
            AgentNotFoundError: If agent not found
        """
        try:
            # Check if agent exists
            query = select(AgentModel).where(AgentModel.id == agent_id)
            result = await self.db.execute(query)
            agent = result.scalars().first()
            
            if not agent:
                raise AgentNotFoundError(agent_id)
            
            # Create message
            message = {
                'source_agent_id': str(agent_id),
                'type': message_type,
                'payload': content,
                'headers': {
                    'project_id': str(agent.project_id),
                    'topic': topic,
                },
            }
            
            # Publish the message to the topic
            message_id = await self.hub.publish_to_topic(topic, message)
            
            logger.info(f"Agent {agent_id} published message {message_id} to topic {topic}")
            
            return message_id
        except Exception as e:
            logger.error(f"Error publishing message to topic {topic} by agent {agent_id}: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
            
            raise AgentCommunicationError(
                from_agent_id=agent_id,
                to_agent_id=UUID('00000000-0000-0000-0000-000000000000'),
                message=f"Failed to publish message to topic: {str(e)}",
            )
    
    async def send_request(
        self,
        from_agent_id: UUID,
        to_agent_id: UUID,
        content: Dict[str, Any],
        timeout: float = 60.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Send a request and wait for a reply.
        
        Args:
            from_agent_id: Sender agent ID
            to_agent_id: Recipient agent ID
            content: Request content
            timeout: Timeout in seconds
            
        Returns:
            Optional[Dict[str, Any]]: Reply or None if the request timed out
            
        Raises:
            AgentNotFoundError: If agent not found
        """
        try:
            # Check if sender agent exists
            query = select(AgentModel).where(AgentModel.id == from_agent_id)
            result = await self.db.execute(query)
            from_agent = result.scalars().first()
            
            if not from_agent:
                raise AgentNotFoundError(from_agent_id)
            
            # Check if recipient agent exists
            query = select(AgentModel).where(AgentModel.id == to_agent_id)
            result = await self.db.execute(query)
            to_agent = result.scalars().first()
            
            if not to_agent:
                raise AgentNotFoundError(to_agent_id)
            
            # Create request
            request = {
                'source_agent_id': str(from_agent_id),
                'destination': {
                    'type': 'agent',
                    'id': str(to_agent_id),
                },
                'type': 'request',
                'payload': content,
                'headers': {
                    'project_id': str(from_agent.project_id),
                },
            }
            
            # Send the request and wait for a reply
            reply = await self.hub.send_request(request, timeout)
            
            if reply:
                logger.info(f"Received reply for request from {from_agent_id} to {to_agent_id}")
            else:
                logger.warning(f"Request from {from_agent_id} to {to_agent_id} timed out")
            
            return reply
        except Exception as e:
            logger.error(f"Error sending request from {from_agent_id} to {to_agent_id}: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
            
            return None
    
    async def broadcast(
        self,
        from_agent_id: UUID,
        to_agent_ids: List[UUID],
        content: Dict[str, Any],
        message_type: str = "broadcast",
    ) -> List[str]:
        """
        Broadcast a message to multiple agents.
        
        Args:
            from_agent_id: Sender agent ID
            to_agent_ids: Recipient agent IDs
            content: Message content
            message_type: Type of message
            
        Returns:
            List[str]: List of message IDs
            
        Raises:
            AgentNotFoundError: If agent not found
        """
        try:
            # Check if sender agent exists
            query = select(AgentModel).where(AgentModel.id == from_agent_id)
            result = await self.db.execute(query)
            from_agent = result.scalars().first()
            
            if not from_agent:
                raise AgentNotFoundError(from_agent_id)
            
            # Create message
            message = {
                'source_agent_id': str(from_agent_id),
                'type': message_type,
                'payload': content,
                'headers': {
                    'project_id': str(from_agent.project_id),
                },
            }
            
            # Convert UUID list to string list
            agent_id_strings = [str(agent_id) for agent_id in to_agent_ids]
            
            # Broadcast the message
            message_ids = await self.hub.broadcast(message, agent_id_strings)
            
            logger.info(f"Agent {from_agent_id} broadcast message to {len(to_agent_ids)} agents")
            
            return message_ids
        except Exception as e:
            logger.error(f"Error broadcasting message from {from_agent_id} to {len(to_agent_ids)} agents: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
            
            raise AgentCommunicationError(
                from_agent_id=from_agent_id,
                to_agent_id=UUID('00000000-0000-0000-0000-000000000000'),
                message=f"Failed to broadcast message: {str(e)}",
            )
    
    async def add_content_rule(
        self,
        condition: Callable[[Dict[str, Any]], bool],
        destination_agent_id: UUID,
    ) -> None:
        """
        Add a content-based routing rule.
        
        Args:
            condition: Function that takes a message and returns True if the rule applies
            destination_agent_id: Destination agent ID
        """
        await self.hub.add_content_rule(condition, str(destination_agent_id))
        logger.info(f"Added content-based routing rule to destination {destination_agent_id}")
    
    async def add_rule(
        self,
        rule: Dict[str, Any],
    ) -> None:
        """
        Add a rule-based routing rule.
        
        Args:
            rule: Rule definition
        """
        await self.hub.add_rule(rule)
        logger.info(f"Added rule-based routing rule: {rule.get('name', 'unnamed')}")
    
    async def register_message_handler(
        self,
        message_type: str,
        handler: Callable[[Dict[str, Any]], None],
    ) -> None:
        """
        Register a handler for a message type.
        
        Args:
            message_type: Type of message to handle
            handler: Handler function
        """
        await self.hub.register_message_handler(message_type, handler)
        logger.info(f"Registered handler for message type {message_type}")
