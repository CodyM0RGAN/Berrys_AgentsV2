"""
Metrics collector for the Agent Communication Hub.

This module provides the MetricsCollector class, which is responsible for collecting
metrics from the CommunicationHub and storing them in the database.
"""

import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from ...models.metrics import (
    MessageMetricsModel,
    AgentMetricsModel,
    TopicMetricsModel,
    MessageStatus
)

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and stores metrics for the Agent Communication Hub.
    """
    
    def __init__(self, session_factory):
        """
        Initialize the MetricsCollector.
        
        Args:
            session_factory: Factory function that returns a SQLAlchemy AsyncSession
        """
        self.session_factory = session_factory
        self.message_metrics_cache = {}  # Cache for message metrics
        self.agent_metrics_cache = {}  # Cache for agent metrics
        self.topic_metrics_cache = {}  # Cache for topic metrics
    
    async def track_message_created(
        self,
        message_id: uuid.UUID,
        source_agent_id: Optional[uuid.UUID],
        destination_agent_id: Optional[uuid.UUID],
        topic: Optional[str] = None,
        priority: Optional[int] = None,
        correlation_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> uuid.UUID:
        """
        Track a message creation event.
        
        Args:
            message_id: ID of the message
            source_agent_id: ID of the source agent
            destination_agent_id: ID of the destination agent
            topic: Topic of the message (for topic-based messages)
            priority: Priority of the message
            correlation_id: ID for correlating related messages
            metadata: Additional metadata
            
        Returns:
            UUID of the created message metrics record
        """
        now = datetime.utcnow()
        
        # Create message metrics record
        async with self.session_factory() as session:
            message_metrics = MessageMetricsModel(
                message_id=message_id,
                correlation_id=correlation_id,
                source_agent_id=source_agent_id,
                destination_agent_id=destination_agent_id,
                topic=topic,
                priority=priority,
                created_at=now,
                status=MessageStatus.CREATED,
                metadata=metadata or {}
            )
            session.add(message_metrics)
            await session.commit()
            await session.refresh(message_metrics)
            
            # Cache the message metrics for later updates
            self.message_metrics_cache[str(message_id)] = {
                "id": message_metrics.id,
                "created_at": now
            }
            
            # Update agent metrics
            if source_agent_id:
                await self._update_agent_metrics(session, source_agent_id, sent=1, received=0)
            
            # Update topic metrics
            if topic:
                await self._update_topic_metrics(session, topic, 1)
            
            return message_metrics.id
    
    async def track_message_routed(
        self,
        message_id: uuid.UUID,
        routing_path: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track a message routing event.
        
        Args:
            message_id: ID of the message
            routing_path: Information about the routing decisions
        """
        now = datetime.utcnow()
        message_id_str = str(message_id)
        
        # Update message metrics record
        async with self.session_factory() as session:
            # Get the message metrics from cache or database
            metrics_id = None
            created_at = None
            if message_id_str in self.message_metrics_cache:
                cache_entry = self.message_metrics_cache[message_id_str]
                metrics_id = cache_entry["id"]
                created_at = cache_entry["created_at"]
            
            if not metrics_id:
                # Look up in the database
                stmt = select(MessageMetricsModel).where(MessageMetricsModel.message_id == message_id)
                result = await session.execute(stmt)
                message_metrics = result.scalars().first()
                
                if not message_metrics:
                    logger.warning(f"Message metrics not found for message_id {message_id}")
                    return
                
                metrics_id = message_metrics.id
                created_at = message_metrics.created_at
                
                # Cache for future updates
                self.message_metrics_cache[message_id_str] = {
                    "id": metrics_id,
                    "created_at": created_at
                }
            
            # Calculate queue time
            queue_time_ms = None
            if created_at:
                queue_time_ms = int((now - created_at).total_seconds() * 1000)
            
            # Update the message metrics
            stmt = select(MessageMetricsModel).where(MessageMetricsModel.id == metrics_id)
            result = await session.execute(stmt)
            message_metrics = result.scalars().first()
            
            if message_metrics:
                message_metrics.status = MessageStatus.ROUTED
                message_metrics.routed_at = now
                message_metrics.queue_time_ms = queue_time_ms
                message_metrics.routing_path = routing_path
                await session.commit()
    
    async def track_message_delivered(
        self,
        message_id: uuid.UUID,
        destination_agent_id: Optional[uuid.UUID] = None
    ) -> None:
        """
        Track a message delivery event.
        
        Args:
            message_id: ID of the message
            destination_agent_id: ID of the destination agent
        """
        now = datetime.utcnow()
        message_id_str = str(message_id)
        
        # Update message metrics record
        async with self.session_factory() as session:
            # Get the message metrics from cache or database
            metrics_id = None
            if message_id_str in self.message_metrics_cache:
                cache_entry = self.message_metrics_cache[message_id_str]
                metrics_id = cache_entry["id"]
            
            if not metrics_id:
                # Look up in the database
                stmt = select(MessageMetricsModel).where(MessageMetricsModel.message_id == message_id)
                result = await session.execute(stmt)
                message_metrics = result.scalars().first()
                
                if not message_metrics:
                    logger.warning(f"Message metrics not found for message_id {message_id}")
                    return
                
                metrics_id = message_metrics.id
                
                # Cache for future updates
                self.message_metrics_cache[message_id_str] = {
                    "id": metrics_id,
                    "created_at": message_metrics.created_at
                }
            
            # Update the message metrics
            stmt = select(MessageMetricsModel).where(MessageMetricsModel.id == metrics_id)
            result = await session.execute(stmt)
            message_metrics = result.scalars().first()
            
            if message_metrics:
                message_metrics.status = MessageStatus.DELIVERED
                message_metrics.delivered_at = now
                
                # Update destination agent if provided
                if destination_agent_id and not message_metrics.destination_agent_id:
                    message_metrics.destination_agent_id = destination_agent_id
                
                await session.commit()
            
            # Update agent metrics
            if destination_agent_id:
                await self._update_agent_metrics(session, destination_agent_id, sent=0, received=1)
    
    async def track_message_processed(
        self,
        message_id: uuid.UUID,
        processing_time_ms: Optional[int] = None
    ) -> None:
        """
        Track a message processing event.
        
        Args:
            message_id: ID of the message
            processing_time_ms: Time taken to process the message in milliseconds
        """
        now = datetime.utcnow()
        message_id_str = str(message_id)
        
        # Update message metrics record
        async with self.session_factory() as session:
            # Get the message metrics from cache or database
            metrics_id = None
            if message_id_str in self.message_metrics_cache:
                cache_entry = self.message_metrics_cache[message_id_str]
                metrics_id = cache_entry["id"]
            
            if not metrics_id:
                # Look up in the database
                stmt = select(MessageMetricsModel).where(MessageMetricsModel.message_id == message_id)
                result = await session.execute(stmt)
                message_metrics = result.scalars().first()
                
                if not message_metrics:
                    logger.warning(f"Message metrics not found for message_id {message_id}")
                    return
                
                metrics_id = message_metrics.id
                
                # Cache for future updates
                self.message_metrics_cache[message_id_str] = {
                    "id": metrics_id,
                    "created_at": message_metrics.created_at
                }
            
            # Update the message metrics
            stmt = select(MessageMetricsModel).where(MessageMetricsModel.id == metrics_id)
            result = await session.execute(stmt)
            message_metrics = result.scalars().first()
            
            if message_metrics:
                message_metrics.status = MessageStatus.PROCESSED
                message_metrics.processed_at = now
                message_metrics.processing_time_ms = processing_time_ms
                
                # Calculate total time
                if message_metrics.created_at:
                    message_metrics.total_time_ms = int((now - message_metrics.created_at).total_seconds() * 1000)
                
                await session.commit()
                
                # Update agent metrics with processing time
                if message_metrics.destination_agent_id and processing_time_ms:
                    await self._update_agent_processing_time(
                        session, 
                        message_metrics.destination_agent_id, 
                        processing_time_ms
                    )
    
    async def track_message_failed(
        self,
        message_id: uuid.UUID,
        error_message: Optional[str] = None
    ) -> None:
        """
        Track a message failure event.
        
        Args:
            message_id: ID of the message
            error_message: Error message
        """
        now = datetime.utcnow()
        message_id_str = str(message_id)
        
        # Update message metrics record
        async with self.session_factory() as session:
            # Get the message metrics from cache or database
            metrics_id = None
            if message_id_str in self.message_metrics_cache:
                cache_entry = self.message_metrics_cache[message_id_str]
                metrics_id = cache_entry["id"]
            
            if not metrics_id:
                # Look up in the database
                stmt = select(MessageMetricsModel).where(MessageMetricsModel.message_id == message_id)
                result = await session.execute(stmt)
                message_metrics = result.scalars().first()
                
                if not message_metrics:
                    logger.warning(f"Message metrics not found for message_id {message_id}")
                    return
                
                metrics_id = message_metrics.id
                
                # Cache for future updates
                self.message_metrics_cache[message_id_str] = {
                    "id": metrics_id,
                    "created_at": message_metrics.created_at
                }
            
            # Update the message metrics
            stmt = select(MessageMetricsModel).where(MessageMetricsModel.id == metrics_id)
            result = await session.execute(stmt)
            message_metrics = result.scalars().first()
            
            if message_metrics:
                message_metrics.status = MessageStatus.FAILED
                
                # Add error message to metadata
                if error_message:
                    metadata = message_metrics.metadata or {}
                    metadata["error_message"] = error_message
                    message_metrics.metadata = metadata
                
                await session.commit()
    
    async def _update_agent_metrics(
        self,
        session: AsyncSession,
        agent_id: uuid.UUID,
        sent: int = 0,
        received: int = 0
    ) -> None:
        """
        Update agent metrics.
        
        Args:
            session: SQLAlchemy session
            agent_id: ID of the agent
            sent: Number of messages sent
            received: Number of messages received
        """
        now = datetime.utcnow()
        today = now.date()
        
        # Get the agent metrics for today
        stmt = select(AgentMetricsModel).where(
            AgentMetricsModel.agent_id == agent_id,
            func.date(AgentMetricsModel.timestamp) == today
        )
        result = await session.execute(stmt)
        agent_metrics = result.scalars().first()
        
        if agent_metrics:
            # Update existing metrics
            agent_metrics.messages_sent += sent
            agent_metrics.messages_received += received
            agent_metrics.timestamp = now
        else:
            # Create new metrics
            agent_metrics = AgentMetricsModel(
                agent_id=agent_id,
                timestamp=now,
                messages_sent=sent,
                messages_received=received
            )
            session.add(agent_metrics)
        
        await session.commit()
    
    async def _update_agent_processing_time(
        self,
        session: AsyncSession,
        agent_id: uuid.UUID,
        processing_time_ms: int
    ) -> None:
        """
        Update agent processing time metrics.
        
        Args:
            session: SQLAlchemy session
            agent_id: ID of the agent
            processing_time_ms: Processing time in milliseconds
        """
        now = datetime.utcnow()
        today = now.date()
        
        # Get the agent metrics for today
        stmt = select(AgentMetricsModel).where(
            AgentMetricsModel.agent_id == agent_id,
            func.date(AgentMetricsModel.timestamp) == today
        )
        result = await session.execute(stmt)
        agent_metrics = result.scalars().first()
        
        if agent_metrics:
            # Update average processing time
            if agent_metrics.average_processing_time_ms is None:
                agent_metrics.average_processing_time_ms = processing_time_ms
            else:
                # Calculate new average
                total_messages = agent_metrics.messages_received
                if total_messages > 0:
                    current_total = agent_metrics.average_processing_time_ms * (total_messages - 1)
                    new_average = (current_total + processing_time_ms) / total_messages
                    agent_metrics.average_processing_time_ms = new_average
            
            await session.commit()
    
    async def _update_topic_metrics(
        self,
        session: AsyncSession,
        topic: str,
        message_count: int = 1
    ) -> None:
        """
        Update topic metrics.
        
        Args:
            session: SQLAlchemy session
            topic: Topic name
            message_count: Number of messages
        """
        now = datetime.utcnow()
        today = now.date()
        
        # Get the topic metrics for today
        stmt = select(TopicMetricsModel).where(
            TopicMetricsModel.topic == topic,
            func.date(TopicMetricsModel.timestamp) == today
        )
        result = await session.execute(stmt)
        topic_metrics = result.scalars().first()
        
        if topic_metrics:
            # Update existing metrics
            topic_metrics.message_count += message_count
            topic_metrics.timestamp = now
        else:
            # Create new metrics
            topic_metrics = TopicMetricsModel(
                topic=topic,
                timestamp=now,
                message_count=message_count,
                subscriber_count=0  # Will be updated separately
            )
            session.add(topic_metrics)
        
        await session.commit()
    
    async def update_topic_subscriber_count(
        self,
        topic: str,
        subscriber_count: int
    ) -> None:
        """
        Update the subscriber count for a topic.
        
        Args:
            topic: Topic name
            subscriber_count: Number of subscribers
        """
        now = datetime.utcnow()
        today = now.date()
        
        async with self.session_factory() as session:
            # Get the topic metrics for today
            stmt = select(TopicMetricsModel).where(
                TopicMetricsModel.topic == topic,
                func.date(TopicMetricsModel.timestamp) == today
            )
            result = await session.execute(stmt)
            topic_metrics = result.scalars().first()
            
            if topic_metrics:
                # Update existing metrics
                topic_metrics.subscriber_count = subscriber_count
                topic_metrics.timestamp = now
            else:
                # Create new metrics
                topic_metrics = TopicMetricsModel(
                    topic=topic,
                    timestamp=now,
                    message_count=0,  # Will be updated when messages are sent
                    subscriber_count=subscriber_count
                )
                session.add(topic_metrics)
            
            await session.commit()
    
    async def get_message_metrics(
        self,
        message_id: Optional[uuid.UUID] = None,
        source_agent_id: Optional[uuid.UUID] = None,
        destination_agent_id: Optional[uuid.UUID] = None,
        topic: Optional[str] = None,
        status: Optional[MessageStatus] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get message metrics.
        
        Args:
            message_id: Filter by message ID
            source_agent_id: Filter by source agent ID
            destination_agent_id: Filter by destination agent ID
            topic: Filter by topic
            status: Filter by status
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of message metrics
        """
        async with self.session_factory() as session:
            query = select(MessageMetricsModel)
            
            # Apply filters
            if message_id:
                query = query.where(MessageMetricsModel.message_id == message_id)
            if source_agent_id:
                query = query.where(MessageMetricsModel.source_agent_id == source_agent_id)
            if destination_agent_id:
                query = query.where(MessageMetricsModel.destination_agent_id == destination_agent_id)
            if topic:
                query = query.where(MessageMetricsModel.topic == topic)
            if status:
                query = query.where(MessageMetricsModel.status == status)
            if start_time:
                query = query.where(MessageMetricsModel.created_at >= start_time)
            if end_time:
                query = query.where(MessageMetricsModel.created_at <= end_time)
            
            # Apply pagination
            query = query.order_by(MessageMetricsModel.created_at.desc())
            query = query.limit(limit).offset(offset)
            
            result = await session.execute(query)
            message_metrics = result.scalars().all()
            
            return [m.to_dict() for m in message_metrics]
    
    async def get_agent_metrics(
        self,
        agent_id: Optional[uuid.UUID] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get agent metrics.
        
        Args:
            agent_id: Filter by agent ID
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of agent metrics
        """
        async with self.session_factory() as session:
            query = select(AgentMetricsModel)
            
            # Apply filters
            if agent_id:
                query = query.where(AgentMetricsModel.agent_id == agent_id)
            if start_time:
                query = query.where(AgentMetricsModel.timestamp >= start_time)
            if end_time:
                query = query.where(AgentMetricsModel.timestamp <= end_time)
            
            # Apply pagination
            query = query.order_by(AgentMetricsModel.timestamp.desc())
            query = query.limit(limit).offset(offset)
            
            result = await session.execute(query)
            agent_metrics = result.scalars().all()
            
            return [m.to_dict() for m in agent_metrics]
    
    async def get_topic_metrics(
        self,
        topic: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get topic metrics.
        
        Args:
            topic: Filter by topic
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of topic metrics
        """
        async with self.session_factory() as session:
            query = select(TopicMetricsModel)
            
            # Apply filters
            if topic:
                query = query.where(TopicMetricsModel.topic == topic)
            if start_time:
                query = query.where(TopicMetricsModel.timestamp >= start_time)
            if end_time:
                query = query.where(TopicMetricsModel.timestamp <= end_time)
            
            # Apply pagination
            query = query.order_by(TopicMetricsModel.timestamp.desc())
            query = query.limit(limit).offset(offset)
            
            result = await session.execute(query)
            topic_metrics = result.scalars().all()
            
            return [m.to_dict() for m in topic_metrics]
    
    async def get_performance_metrics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Args:
            start_time: Filter by start time
            end_time: Filter by end time
            
        Returns:
            Performance metrics
        """
        async with self.session_factory() as session:
            # Define time range
            if not start_time:
                start_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            if not end_time:
                end_time = datetime.utcnow()
            
            # Get message count
            query = select(func.count(MessageMetricsModel.id)).where(
                MessageMetricsModel.created_at >= start_time,
                MessageMetricsModel.created_at <= end_time
            )
            result = await session.execute(query)
            message_count = result.scalar() or 0
            
            # Get average processing time
            query = select(func.avg(MessageMetricsModel.processing_time_ms)).where(
                MessageMetricsModel.created_at >= start_time,
                MessageMetricsModel.created_at <= end_time,
                MessageMetricsModel.processing_time_ms.isnot(None)
            )
            result = await session.execute(query)
            avg_processing_time = result.scalar() or 0
            
            # Get average queue time
            query = select(func.avg(MessageMetricsModel.queue_time_ms)).where(
                MessageMetricsModel.created_at >= start_time,
                MessageMetricsModel.created_at <= end_time,
                MessageMetricsModel.queue_time_ms.isnot(None)
            )
            result = await session.execute(query)
            avg_queue_time = result.scalar() or 0
            
            # Get average total time
            query = select(func.avg(MessageMetricsModel.total_time_ms)).where(
                MessageMetricsModel.created_at >= start_time,
                MessageMetricsModel.created_at <= end_time,
                MessageMetricsModel.total_time_ms.isnot(None)
            )
            result = await session.execute(query)
            avg_total_time = result.scalar() or 0
            
            # Get message count by status
            status_counts = {}
            for status in MessageStatus:
                query = select(func.count(MessageMetricsModel.id)).where(
                    MessageMetricsModel.created_at >= start_time,
                    MessageMetricsModel.created_at <= end_time,
                    MessageMetricsModel.status == status
                )
                result = await session.execute(query)
                status_counts[status.value] = result.scalar() or 0
            
            # Get top topics by message count
            query = select(
                MessageMetricsModel.topic,
                func.count(MessageMetricsModel.id).label("count")
            ).where(
                MessageMetricsModel.created_at >= start_time,
                MessageMetricsModel.created_at <= end_time,
                MessageMetricsModel.topic.isnot(None)
            ).group_by(
                MessageMetricsModel.topic
            ).order_by(
                func.count(MessageMetricsModel.id).desc()
            ).limit(10)
            result = await session.execute(query)
            top_topics = [{"topic": row[0], "count": row[1]} for row in result]
            
            # Get top agents by message count
            query = select(
                MessageMetricsModel.source_agent_id,
                func.count(MessageMetricsModel.id).label("count")
            ).where(
                MessageMetricsModel.created_at >= start_time,
                MessageMetricsModel.created_at <= end_time,
                MessageMetricsModel.source_agent_id.isnot(None)
            ).group_by(
                MessageMetricsModel.source_agent_id
            ).order_by(
                func.count(MessageMetricsModel.id).desc()
            ).limit(10)
            result = await session.execute(query)
            top_source_agents = [{"agent_id": str(row[0]), "count": row[1]} for row in result]
            
            # Return performance metrics
            return {
                "message_count": message_count,
                "avg_processing_time_ms": float(avg_processing_time),
                "avg_queue_time_ms": float(avg_queue_time),
                "avg_total_time_ms": float(avg_total_time),
                "status_counts": status_counts,
                "top_topics": top_topics,
                "top_source_agents": top_source_agents,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
