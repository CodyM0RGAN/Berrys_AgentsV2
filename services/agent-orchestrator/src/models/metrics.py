"""
Metrics models for the Agent Communication Hub Monitoring and Analytics feature.

This module provides SQLAlchemy models for storing and retrieving metrics data
for the Agent Communication Hub.
"""

from sqlalchemy import Column, String, ForeignKey, JSON, DateTime, Integer, Float, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import List, Optional, Dict, Any
from enum import Enum as PyEnum

from shared.models.src.base import StandardModel
from shared.utils.src.database import UUID, generate_uuid


class MessageStatus(str, PyEnum):
    """
    Status of a message in the communication hub.
    """
    CREATED = "CREATED"
    ROUTED = "ROUTED"
    DELIVERED = "DELIVERED"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class MetricType(str, PyEnum):
    """
    Type of metric for alert configuration.
    """
    QUEUE_LENGTH = "QUEUE_LENGTH"
    PROCESSING_TIME = "PROCESSING_TIME"
    ROUTING_TIME = "ROUTING_TIME"
    DELIVERY_TIME = "DELIVERY_TIME"
    MESSAGE_COUNT = "MESSAGE_COUNT"
    ERROR_RATE = "ERROR_RATE"
    TOPIC_ACTIVITY = "TOPIC_ACTIVITY"
    AGENT_ACTIVITY = "AGENT_ACTIVITY"


class ComparisonOperator(str, PyEnum):
    """
    Comparison operator for alert configuration.
    """
    GT = "GT"  # Greater than
    LT = "LT"  # Less than
    GTE = "GTE"  # Greater than or equal
    LTE = "LTE"  # Less than or equal
    EQ = "EQ"  # Equal
    NEQ = "NEQ"  # Not equal


class AlertSeverity(str, PyEnum):
    """
    Severity level for alerts.
    """
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MessageMetricsModel(StandardModel):
    """
    SQLAlchemy model for message metrics.
    """
    __tablename__ = "message_metrics"
    
    # Message identification
    message_id = Column(UUID, nullable=False, index=True)
    correlation_id = Column(UUID, nullable=True, index=True)
    
    # Agent associations
    source_agent_id = Column(UUID, ForeignKey("agent.id", ondelete="SET NULL"), nullable=True, index=True)
    destination_agent_id = Column(UUID, ForeignKey("agent.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Message information
    topic = Column(String, nullable=True, index=True)
    priority = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    routed_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Performance metrics
    processing_time_ms = Column(Integer, nullable=True)
    queue_time_ms = Column(Integer, nullable=True)
    total_time_ms = Column(Integer, nullable=True)
    
    # Status
    status = Column(Enum(MessageStatus), nullable=False, index=True)
    
    # Additional data
    routing_path = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    source_agent = relationship("AgentModel", foreign_keys=[source_agent_id])
    destination_agent = relationship("AgentModel", foreign_keys=[destination_agent_id])
    
    def __repr__(self):
        return f"<MessageMetrics(id={self.id}, message_id={self.message_id}, status='{self.status}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            "id": str(self.id),
            "message_id": str(self.message_id),
            "correlation_id": str(self.correlation_id) if self.correlation_id else None,
            "source_agent_id": str(self.source_agent_id) if self.source_agent_id else None,
            "destination_agent_id": str(self.destination_agent_id) if self.destination_agent_id else None,
            "topic": self.topic,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "routed_at": self.routed_at.isoformat() if self.routed_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "processing_time_ms": self.processing_time_ms,
            "queue_time_ms": self.queue_time_ms,
            "total_time_ms": self.total_time_ms,
            "status": self.status.value if self.status else None,
            "routing_path": self.routing_path,
            "metadata": self.metadata,
        }


class AgentMetricsModel(StandardModel):
    """
    SQLAlchemy model for agent metrics.
    """
    __tablename__ = "agent_metrics"
    
    # Agent association
    agent_id = Column(UUID, ForeignKey("agent.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Metrics
    messages_sent = Column(Integer, nullable=False, default=0)
    messages_received = Column(Integer, nullable=False, default=0)
    average_processing_time_ms = Column(Float, nullable=True)
    
    # Additional data
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    agent = relationship("AgentModel", foreign_keys=[agent_id])
    
    def __repr__(self):
        return f"<AgentMetrics(id={self.id}, agent_id={self.agent_id}, timestamp='{self.timestamp}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "average_processing_time_ms": self.average_processing_time_ms,
            "metadata": self.metadata,
        }


class TopicMetricsModel(StandardModel):
    """
    SQLAlchemy model for topic metrics.
    """
    __tablename__ = "topic_metrics"
    
    # Topic information
    topic = Column(String, nullable=False, index=True)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Metrics
    message_count = Column(Integer, nullable=False, default=0)
    subscriber_count = Column(Integer, nullable=False, default=0)
    
    # Additional data
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<TopicMetrics(id={self.id}, topic='{self.topic}', timestamp='{self.timestamp}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            "id": str(self.id),
            "topic": self.topic,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "message_count": self.message_count,
            "subscriber_count": self.subscriber_count,
            "metadata": self.metadata,
        }


class AlertConfigurationModel(StandardModel):
    """
    SQLAlchemy model for alert configurations.
    """
    __tablename__ = "alert_configurations"
    
    # Alert information
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Alert configuration
    metric_type = Column(Enum(MetricType), nullable=False)
    threshold = Column(Float, nullable=False)
    comparison = Column(Enum(ComparisonOperator), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    
    # Notification configuration
    notification_channels = Column(JSON, nullable=True)
    
    # Additional data
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    alert_history = relationship("AlertHistoryModel", back_populates="alert_configuration", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AlertConfiguration(id={self.id}, name='{self.name}', metric_type='{self.metric_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "metric_type": self.metric_type.value if self.metric_type else None,
            "threshold": self.threshold,
            "comparison": self.comparison.value if self.comparison else None,
            "severity": self.severity.value if self.severity else None,
            "enabled": self.enabled,
            "notification_channels": self.notification_channels,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }


class AlertHistoryModel(StandardModel):
    """
    SQLAlchemy model for alert history.
    """
    __tablename__ = "alert_history"
    
    # Alert configuration association
    alert_configuration_id = Column(UUID, ForeignKey("alert_configurations.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Alert information
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    value = Column(Float, nullable=False)
    message = Column(String, nullable=False)
    
    # Acknowledgment information
    acknowledged = Column(Boolean, nullable=False, default=False)
    acknowledged_by = Column(UUID, nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional data
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    alert_configuration = relationship("AlertConfigurationModel", back_populates="alert_history")
    
    def __repr__(self):
        return f"<AlertHistory(id={self.id}, alert_configuration_id={self.alert_configuration_id}, timestamp='{self.timestamp}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            "id": str(self.id),
            "alert_configuration_id": str(self.alert_configuration_id) if self.alert_configuration_id else None,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "value": self.value,
            "message": self.message,
            "acknowledged": self.acknowledged,
            "acknowledged_by": str(self.acknowledged_by) if self.acknowledged_by else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "metadata": self.metadata,
        }
