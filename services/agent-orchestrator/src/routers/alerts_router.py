"""
Router for alert-related endpoints.

This module provides FastAPI router for managing alert configurations and history.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.dependencies import get_alerting_service
from src.models.metrics import AlertSeverity, ComparisonOperator, MetricType
from src.services.communication.alerting_service import AlertingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])


class NotificationChannel(BaseModel):
    """Base model for notification channel configuration."""
    pass


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel configuration."""
    recipients: List[str] = Field(..., description="List of email recipients")


class DashboardNotificationChannel(NotificationChannel):
    """Dashboard notification channel configuration."""
    enabled: bool = Field(True, description="Whether dashboard notifications are enabled")


class NotificationChannels(BaseModel):
    """Notification channels configuration."""
    email: Optional[EmailNotificationChannel] = Field(None, description="Email notification configuration")
    dashboard: Optional[DashboardNotificationChannel] = Field(None, description="Dashboard notification configuration")


class AlertConfigurationCreate(BaseModel):
    """Model for creating an alert configuration."""
    name: str = Field(..., description="Alert name")
    description: Optional[str] = Field(None, description="Alert description")
    metric_type: MetricType = Field(..., description="Type of metric to monitor")
    threshold: float = Field(..., description="Threshold value")
    comparison: ComparisonOperator = Field(..., description="Comparison operator")
    severity: AlertSeverity = Field(..., description="Severity level")
    enabled: bool = Field(True, description="Whether the alert is enabled")
    notification_channels: Optional[Dict[str, Any]] = Field(None, description="Notification channels configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AlertConfigurationUpdate(BaseModel):
    """Model for updating an alert configuration."""
    name: Optional[str] = Field(None, description="Alert name")
    description: Optional[str] = Field(None, description="Alert description")
    metric_type: Optional[MetricType] = Field(None, description="Type of metric to monitor")
    threshold: Optional[float] = Field(None, description="Threshold value")
    comparison: Optional[ComparisonOperator] = Field(None, description="Comparison operator")
    severity: Optional[AlertSeverity] = Field(None, description="Severity level")
    enabled: Optional[bool] = Field(None, description="Whether the alert is enabled")
    notification_channels: Optional[Dict[str, Any]] = Field(None, description="Notification channels configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AlertConfiguration(BaseModel):
    """Model for an alert configuration."""
    id: UUID = Field(..., description="Alert configuration ID")
    name: str = Field(..., description="Alert name")
    description: Optional[str] = Field(None, description="Alert description")
    metric_type: str = Field(..., description="Type of metric to monitor")
    threshold: float = Field(..., description="Threshold value")
    comparison: str = Field(..., description="Comparison operator")
    severity: str = Field(..., description="Severity level")
    enabled: bool = Field(..., description="Whether the alert is enabled")
    notification_channels: Dict[str, Any] = Field(..., description="Notification channels configuration")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")


class AlertHistory(BaseModel):
    """Model for an alert history record."""
    id: UUID = Field(..., description="Alert history ID")
    alert_configuration_id: Optional[UUID] = Field(None, description="Alert configuration ID")
    timestamp: datetime = Field(..., description="Alert timestamp")
    value: float = Field(..., description="Metric value at the time of the alert")
    message: str = Field(..., description="Alert message")
    acknowledged: bool = Field(..., description="Whether the alert has been acknowledged")
    acknowledged_by: Optional[UUID] = Field(None, description="User who acknowledged the alert")
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledgment timestamp")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")


class AlertWithConfiguration(BaseModel):
    """Model for an alert with its configuration."""
    alert: AlertHistory = Field(..., description="Alert history record")
    configuration: AlertConfiguration = Field(..., description="Alert configuration")


class AlertAcknowledge(BaseModel):
    """Model for acknowledging an alert."""
    acknowledged_by: Optional[UUID] = Field(None, description="User who acknowledged the alert")


class AlertCountsBySeverity(BaseModel):
    """Model for alert counts by severity."""
    INFO: int = Field(0, description="Number of INFO alerts")
    WARNING: int = Field(0, description="Number of WARNING alerts")
    ERROR: int = Field(0, description="Number of ERROR alerts")
    CRITICAL: int = Field(0, description="Number of CRITICAL alerts")


@router.get("/configurations", response_model=List[AlertConfiguration])
async def get_alert_configurations(
    metric_type: Optional[MetricType] = Query(None, description="Filter by metric type"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    limit: int = Query(100, description="Maximum number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    alerting_service: AlertingService = Depends(get_alerting_service)
):
    """
    Get alert configurations.
    """
    configs = await alerting_service.get_alert_configurations(
        metric_type=metric_type,
        severity=severity,
        enabled=enabled,
        limit=limit,
        offset=offset
    )
    return [config.to_dict() for config in configs]


@router.post("/configurations", response_model=AlertConfiguration, status_code=201)
async def create_alert_configuration(
    config: AlertConfigurationCreate,
    alerting_service: AlertingService = Depends(get_alerting_service)
):
    """
    Create a new alert configuration.
    """
    created_config = await alerting_service.create_alert_configuration(
        name=config.name,
        description=config.description,
        metric_type=config.metric_type,
        threshold=config.threshold,
        comparison=config.comparison,
        severity=config.severity,
        enabled=config.enabled,
        notification_channels=config.notification_channels,
        metadata=config.metadata
    )
    return created_config.to_dict()


@router.get("/configurations/{alert_id}", response_model=AlertConfiguration)
async def get_alert_configuration(
    alert_id: UUID,
    alerting_service: AlertingService = Depends(get_alerting_service)
):
    """
    Get an alert configuration by ID.
    """
    config = await alerting_service.get_alert_configuration(alert_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Alert configuration not found: {alert_id}")
    return config.to_dict()


@router.put("/configurations/{alert_id}", response_model=AlertConfiguration)
async def update_alert_configuration(
    alert_id: UUID,
    config: AlertConfigurationUpdate,
    alerting_service: AlertingService = Depends(get_alerting_service)
):
    """
    Update an alert configuration.
    """
    updated_config = await alerting_service.update_alert_configuration(
        alert_id=alert_id,
        name=config.name,
        description=config.description,
        metric_type=config.metric_type,
        threshold=config.threshold,
        comparison=config.comparison,
        severity=config.severity,
        enabled=config.enabled,
        notification_channels=config.notification_channels,
        metadata=config.metadata
    )
    if not updated_config:
        raise HTTPException(status_code=404, detail=f"Alert configuration not found: {alert_id}")
    return updated_config.to_dict()


@router.delete("/configurations/{alert_id}", response_model=Dict[str, bool])
async def delete_alert_configuration(
    alert_id: UUID,
    alerting_service: AlertingService = Depends(get_alerting_service)
):
    """
    Delete an alert configuration.
    """
    deleted = await alerting_service.delete_alert_configuration(alert_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Alert configuration not found: {alert_id}")
    return {"success": True}


@router.get("/history", response_model=List[AlertHistory])
async def get_alert_history(
    alert_configuration_id: Optional[UUID] = Query(None, description="Filter by alert configuration ID"),
    start_time: Optional[datetime] = Query(None, description="Filter by start time"),
    end_time: Optional[datetime] = Query(None, description="Filter by end time"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledged status"),
    limit: int = Query(100, description="Maximum number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    alerting_service: AlertingService = Depends(get_alerting_service)
):
    """
    Get alert history.
    """
    alerts = await alerting_service.get_alert_history(
        alert_configuration_id=alert_configuration_id,
        start_time=start_time,
        end_time=end_time,
        acknowledged=acknowledged,
        limit=limit,
        offset=offset
    )
    return [alert.to_dict() for alert in alerts]


@router.get("/active", response_model=List[AlertWithConfiguration])
async def get_active_alerts(
    alerting_service: AlertingService = Depends(get_alerting_service)
):
    """
    Get active (unacknowledged) alerts with their configurations.
    """
    return await alerting_service.get_active_alerts()


@router.post("/acknowledge/{alert_id}", response_model=AlertHistory)
async def acknowledge_alert(
    alert_id: UUID,
    data: AlertAcknowledge,
    alerting_service: AlertingService = Depends(get_alerting_service)
):
    """
    Acknowledge an alert.
    """
    alert = await alerting_service.acknowledge_alert(
        alert_id=alert_id,
        acknowledged_by=data.acknowledged_by
    )
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")
    return alert.to_dict()


@router.get("/counts/by-severity", response_model=AlertCountsBySeverity)
async def get_alert_counts_by_severity(
    start_time: Optional[datetime] = Query(None, description="Filter by start time"),
    end_time: Optional[datetime] = Query(None, description="Filter by end time"),
    alerting_service: AlertingService = Depends(get_alerting_service)
):
    """
    Get alert counts by severity.
    """
    counts = await alerting_service.get_alert_counts_by_severity(
        start_time=start_time,
        end_time=end_time
    )
    
    # Ensure all severity levels are present in the response
    result = AlertCountsBySeverity()
    for severity, count in counts.items():
        setattr(result, severity, count)
    
    return result
