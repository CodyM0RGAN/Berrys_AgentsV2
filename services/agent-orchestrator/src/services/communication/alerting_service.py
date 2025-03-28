"""
Alerting service for the Agent Communication Hub.

This module provides the AlertingService class, which is responsible for monitoring
metrics and triggering alerts when thresholds are exceeded.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.metrics import (
    AlertConfigurationModel,
    AlertHistoryModel,
    AlertSeverity,
    ComparisonOperator,
    MetricType,
)
from src.services.communication.metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class AlertingService:
    """
    Service for monitoring metrics and triggering alerts when thresholds are exceeded.
    """

    def __init__(self, db_factory: Callable[[], AsyncSession], metrics_collector: MetricsCollector):
        """
        Initialize the alerting service.

        Args:
            db_factory: Factory function to create a database session
            metrics_collector: Metrics collector instance
        """
        self.db_factory = db_factory
        self.metrics_collector = metrics_collector
        self._notification_handlers = {}
        self._running = False
        self._check_interval = 60  # seconds

    async def start(self):
        """
        Start the alerting service.
        """
        if self._running:
            return

        self._running = True
        logger.info("Starting alerting service")
        
        # Start the alert checking loop
        asyncio.create_task(self._check_alerts_loop())

    async def stop(self):
        """
        Stop the alerting service.
        """
        self._running = False
        logger.info("Stopping alerting service")

    async def _check_alerts_loop(self):
        """
        Periodically check for alert conditions.
        """
        while self._running:
            try:
                await self._check_alerts()
            except Exception as e:
                logger.error(f"Error checking alerts: {e}")
            
            await asyncio.sleep(self._check_interval)

    async def _check_alerts(self):
        """
        Check all enabled alert configurations and trigger alerts if conditions are met.
        """
        async with self.db_factory() as db:
            # Get all enabled alert configurations
            query = select(AlertConfigurationModel).where(AlertConfigurationModel.enabled == True)
            result = await db.execute(query)
            alert_configs = result.scalars().all()
            
            for config in alert_configs:
                try:
                    # Get the current metric value
                    value = await self._get_metric_value(config.metric_type, db)
                    
                    # Check if the alert condition is met
                    if value is not None and self._check_condition(value, config.threshold, config.comparison):
                        # Create an alert history record
                        await self._create_alert(config, value, db)
                except Exception as e:
                    logger.error(f"Error checking alert {config.id}: {e}")

    async def _get_metric_value(self, metric_type: MetricType, db: AsyncSession) -> Optional[float]:
        """
        Get the current value of a metric.

        Args:
            metric_type: Type of metric to get
            db: Database session

        Returns:
            Current value of the metric, or None if not available
        """
        # Time window for metrics (last hour)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        if metric_type == MetricType.QUEUE_LENGTH:
            # Get average queue length from message metrics
            return await self.metrics_collector.get_average_queue_length(start_time, end_time, db)
        
        elif metric_type == MetricType.PROCESSING_TIME:
            # Get average processing time from message metrics
            return await self.metrics_collector.get_average_processing_time(start_time, end_time, db)
        
        elif metric_type == MetricType.ROUTING_TIME:
            # Get average routing time from message metrics
            return await self.metrics_collector.get_average_routing_time(start_time, end_time, db)
        
        elif metric_type == MetricType.DELIVERY_TIME:
            # Get average delivery time from message metrics
            return await self.metrics_collector.get_average_delivery_time(start_time, end_time, db)
        
        elif metric_type == MetricType.MESSAGE_COUNT:
            # Get message count from message metrics
            return await self.metrics_collector.get_message_count(start_time, end_time, db)
        
        elif metric_type == MetricType.ERROR_RATE:
            # Get error rate from message metrics
            return await self.metrics_collector.get_error_rate(start_time, end_time, db)
        
        elif metric_type == MetricType.TOPIC_ACTIVITY:
            # Get topic activity from topic metrics
            return await self.metrics_collector.get_topic_activity(start_time, end_time, db)
        
        elif metric_type == MetricType.AGENT_ACTIVITY:
            # Get agent activity from agent metrics
            return await self.metrics_collector.get_agent_activity(start_time, end_time, db)
        
        else:
            logger.warning(f"Unknown metric type: {metric_type}")
            return None

    def _check_condition(self, value: float, threshold: float, comparison: ComparisonOperator) -> bool:
        """
        Check if a value meets a condition.

        Args:
            value: Value to check
            threshold: Threshold value
            comparison: Comparison operator

        Returns:
            True if the condition is met, False otherwise
        """
        if comparison == ComparisonOperator.GT:
            return value > threshold
        elif comparison == ComparisonOperator.LT:
            return value < threshold
        elif comparison == ComparisonOperator.GTE:
            return value >= threshold
        elif comparison == ComparisonOperator.LTE:
            return value <= threshold
        elif comparison == ComparisonOperator.EQ:
            return value == threshold
        elif comparison == ComparisonOperator.NEQ:
            return value != threshold
        else:
            logger.warning(f"Unknown comparison operator: {comparison}")
            return False

    async def _create_alert(self, config: AlertConfigurationModel, value: float, db: AsyncSession):
        """
        Create an alert history record.

        Args:
            config: Alert configuration
            value: Current metric value
            db: Database session
        """
        # Check if there's already an active (unacknowledged) alert for this configuration
        query = select(AlertHistoryModel).where(
            and_(
                AlertHistoryModel.alert_configuration_id == config.id,
                AlertHistoryModel.acknowledged == False
            )
        )
        result = await db.execute(query)
        existing_alert = result.scalars().first()
        
        if existing_alert:
            # Update the existing alert with the new value
            existing_alert.value = value
            existing_alert.timestamp = datetime.utcnow()
            await db.commit()
            logger.info(f"Updated existing alert {existing_alert.id} for configuration {config.id}")
            return
        
        # Create a new alert history record
        message = self._generate_alert_message(config, value)
        alert = AlertHistoryModel(
            alert_configuration_id=config.id,
            timestamp=datetime.utcnow(),
            value=value,
            message=message,
            acknowledged=False,
            metadata={}
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        
        logger.info(f"Created new alert {alert.id} for configuration {config.id}")
        
        # Send notifications
        await self._send_notifications(config, alert)

    def _generate_alert_message(self, config: AlertConfigurationModel, value: float) -> str:
        """
        Generate an alert message.

        Args:
            config: Alert configuration
            value: Current metric value

        Returns:
            Alert message
        """
        comparison_str = {
            ComparisonOperator.GT: "greater than",
            ComparisonOperator.LT: "less than",
            ComparisonOperator.GTE: "greater than or equal to",
            ComparisonOperator.LTE: "less than or equal to",
            ComparisonOperator.EQ: "equal to",
            ComparisonOperator.NEQ: "not equal to"
        }.get(config.comparison, str(config.comparison))
        
        return f"Alert: {config.name} - {config.metric_type.value} is {comparison_str} {config.threshold} (current value: {value})"

    async def _send_notifications(self, config: AlertConfigurationModel, alert: AlertHistoryModel):
        """
        Send notifications for an alert.

        Args:
            config: Alert configuration
            alert: Alert history record
        """
        if not config.notification_channels:
            return
        
        for channel, channel_config in config.notification_channels.items():
            handler = self._notification_handlers.get(channel)
            if handler:
                try:
                    await handler(config, alert, channel_config)
                except Exception as e:
                    logger.error(f"Error sending notification to channel {channel}: {e}")
            else:
                logger.warning(f"No handler registered for notification channel: {channel}")

    def register_notification_handler(self, channel: str, handler: Callable):
        """
        Register a notification handler.

        Args:
            channel: Notification channel name
            handler: Notification handler function
        """
        self._notification_handlers[channel] = handler
        logger.info(f"Registered notification handler for channel: {channel}")

    async def create_alert_configuration(
        self,
        name: str,
        metric_type: MetricType,
        threshold: float,
        comparison: ComparisonOperator,
        severity: AlertSeverity,
        description: Optional[str] = None,
        enabled: bool = True,
        notification_channels: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AlertConfigurationModel:
        """
        Create a new alert configuration.

        Args:
            name: Alert name
            metric_type: Type of metric to monitor
            threshold: Threshold value
            comparison: Comparison operator
            severity: Severity level
            description: Alert description
            enabled: Whether the alert is enabled
            notification_channels: Notification channels configuration
            metadata: Additional metadata

        Returns:
            Created alert configuration
        """
        async with self.db_factory() as db:
            config = AlertConfigurationModel(
                name=name,
                description=description,
                metric_type=metric_type,
                threshold=threshold,
                comparison=comparison,
                severity=severity,
                enabled=enabled,
                notification_channels=notification_channels or {},
                metadata=metadata or {}
            )
            db.add(config)
            await db.commit()
            await db.refresh(config)
            
            logger.info(f"Created alert configuration: {config.id}")
            return config

    async def update_alert_configuration(
        self,
        alert_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metric_type: Optional[MetricType] = None,
        threshold: Optional[float] = None,
        comparison: Optional[ComparisonOperator] = None,
        severity: Optional[AlertSeverity] = None,
        enabled: Optional[bool] = None,
        notification_channels: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[AlertConfigurationModel]:
        """
        Update an alert configuration.

        Args:
            alert_id: Alert configuration ID
            name: Alert name
            description: Alert description
            metric_type: Type of metric to monitor
            threshold: Threshold value
            comparison: Comparison operator
            severity: Severity level
            enabled: Whether the alert is enabled
            notification_channels: Notification channels configuration
            metadata: Additional metadata

        Returns:
            Updated alert configuration, or None if not found
        """
        async with self.db_factory() as db:
            query = select(AlertConfigurationModel).where(AlertConfigurationModel.id == alert_id)
            result = await db.execute(query)
            config = result.scalars().first()
            
            if not config:
                logger.warning(f"Alert configuration not found: {alert_id}")
                return None
            
            if name is not None:
                config.name = name
            if description is not None:
                config.description = description
            if metric_type is not None:
                config.metric_type = metric_type
            if threshold is not None:
                config.threshold = threshold
            if comparison is not None:
                config.comparison = comparison
            if severity is not None:
                config.severity = severity
            if enabled is not None:
                config.enabled = enabled
            if notification_channels is not None:
                config.notification_channels = notification_channels
            if metadata is not None:
                config.metadata = metadata
            
            await db.commit()
            await db.refresh(config)
            
            logger.info(f"Updated alert configuration: {config.id}")
            return config

    async def delete_alert_configuration(self, alert_id: UUID) -> bool:
        """
        Delete an alert configuration.

        Args:
            alert_id: Alert configuration ID

        Returns:
            True if the alert configuration was deleted, False otherwise
        """
        async with self.db_factory() as db:
            query = select(AlertConfigurationModel).where(AlertConfigurationModel.id == alert_id)
            result = await db.execute(query)
            config = result.scalars().first()
            
            if not config:
                logger.warning(f"Alert configuration not found: {alert_id}")
                return False
            
            await db.delete(config)
            await db.commit()
            
            logger.info(f"Deleted alert configuration: {alert_id}")
            return True

    async def get_alert_configuration(self, alert_id: UUID) -> Optional[AlertConfigurationModel]:
        """
        Get an alert configuration by ID.

        Args:
            alert_id: Alert configuration ID

        Returns:
            Alert configuration, or None if not found
        """
        async with self.db_factory() as db:
            query = select(AlertConfigurationModel).where(AlertConfigurationModel.id == alert_id)
            result = await db.execute(query)
            config = result.scalars().first()
            
            if not config:
                logger.warning(f"Alert configuration not found: {alert_id}")
                return None
            
            return config

    async def get_alert_configurations(
        self,
        metric_type: Optional[MetricType] = None,
        severity: Optional[AlertSeverity] = None,
        enabled: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AlertConfigurationModel]:
        """
        Get alert configurations.

        Args:
            metric_type: Filter by metric type
            severity: Filter by severity
            enabled: Filter by enabled status
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of alert configurations
        """
        async with self.db_factory() as db:
            query = select(AlertConfigurationModel)
            
            if metric_type is not None:
                query = query.where(AlertConfigurationModel.metric_type == metric_type)
            if severity is not None:
                query = query.where(AlertConfigurationModel.severity == severity)
            if enabled is not None:
                query = query.where(AlertConfigurationModel.enabled == enabled)
            
            query = query.limit(limit).offset(offset)
            result = await db.execute(query)
            configs = result.scalars().all()
            
            return configs

    async def acknowledge_alert(
        self,
        alert_id: UUID,
        acknowledged_by: Optional[UUID] = None
    ) -> Optional[AlertHistoryModel]:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert ID
            acknowledged_by: User who acknowledged the alert

        Returns:
            Updated alert history record, or None if not found
        """
        async with self.db_factory() as db:
            query = select(AlertHistoryModel).where(AlertHistoryModel.id == alert_id)
            result = await db.execute(query)
            alert = result.scalars().first()
            
            if not alert:
                logger.warning(f"Alert not found: {alert_id}")
                return None
            
            alert.acknowledged = True
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(alert)
            
            logger.info(f"Acknowledged alert: {alert.id}")
            return alert

    async def get_alert_history(
        self,
        alert_configuration_id: Optional[UUID] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AlertHistoryModel]:
        """
        Get alert history.

        Args:
            alert_configuration_id: Filter by alert configuration ID
            start_time: Filter by start time
            end_time: Filter by end time
            acknowledged: Filter by acknowledged status
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of alert history records
        """
        async with self.db_factory() as db:
            query = select(AlertHistoryModel)
            
            if alert_configuration_id is not None:
                query = query.where(AlertHistoryModel.alert_configuration_id == alert_configuration_id)
            if start_time is not None:
                query = query.where(AlertHistoryModel.timestamp >= start_time)
            if end_time is not None:
                query = query.where(AlertHistoryModel.timestamp <= end_time)
            if acknowledged is not None:
                query = query.where(AlertHistoryModel.acknowledged == acknowledged)
            
            query = query.order_by(AlertHistoryModel.timestamp.desc()).limit(limit).offset(offset)
            result = await db.execute(query)
            alerts = result.scalars().all()
            
            return alerts

    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """
        Get active (unacknowledged) alerts with their configurations.

        Returns:
            List of active alerts with their configurations
        """
        async with self.db_factory() as db:
            # Get unacknowledged alerts with their configurations
            query = select(AlertHistoryModel, AlertConfigurationModel).join(
                AlertConfigurationModel,
                AlertHistoryModel.alert_configuration_id == AlertConfigurationModel.id
            ).where(AlertHistoryModel.acknowledged == False)
            
            result = await db.execute(query)
            rows = result.all()
            
            active_alerts = []
            for alert, config in rows:
                active_alerts.append({
                    "alert": alert.to_dict(),
                    "configuration": config.to_dict()
                })
            
            return active_alerts

    async def get_alert_counts_by_severity(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, int]:
        """
        Get alert counts by severity.

        Args:
            start_time: Filter by start time
            end_time: Filter by end time

        Returns:
            Dictionary mapping severity to count
        """
        async with self.db_factory() as db:
            query = select(
                AlertConfigurationModel.severity,
                func.count(AlertHistoryModel.id)
            ).join(
                AlertHistoryModel,
                AlertHistoryModel.alert_configuration_id == AlertConfigurationModel.id
            ).group_by(AlertConfigurationModel.severity)
            
            if start_time is not None:
                query = query.where(AlertHistoryModel.timestamp >= start_time)
            if end_time is not None:
                query = query.where(AlertHistoryModel.timestamp <= end_time)
            
            result = await db.execute(query)
            rows = result.all()
            
            counts = {}
            for severity, count in rows:
                counts[severity.value] = count
            
            return counts
