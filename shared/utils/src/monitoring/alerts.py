"""
Alerting system for the Berrys_AgentsV2 platform.

This module provides utilities for creating, managing, and sending alerts based on
monitoring data. It supports threshold-based alerts, anomaly detection, and
multiple notification channels.

Usage:
    from shared.utils.src.monitoring.alerts import trigger_alert, AlertSeverity

    # Trigger a simple alert
    trigger_alert(
        "High CPU Usage",
        "CPU usage is above 90%",
        AlertSeverity.WARNING,
        {"service": "api-gateway", "cpu_usage": "95%"}
    )
"""

import json
import logging
import smtplib
import threading
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast

# Configure basic logging
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Severity levels for alerts."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertState(Enum):
    """States for alerts."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class NotificationChannel(Enum):
    """Available notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    CONSOLE = "console"
    SMS = "sms"


# Global alert configuration
_alert_config = {
    "enabled": True,
    "min_severity": AlertSeverity.INFO,
    "channels": {
        NotificationChannel.CONSOLE: {
            "enabled": True
        },
        NotificationChannel.EMAIL: {
            "enabled": False,
            "smtp_server": "",
            "smtp_port": 587,
            "smtp_username": "",
            "smtp_password": "",
            "from_email": "",
            "to_emails": []
        },
        NotificationChannel.SLACK: {
            "enabled": False,
            "webhook_url": ""
        },
        NotificationChannel.WEBHOOK: {
            "enabled": False,
            "url": ""
        },
        NotificationChannel.SMS: {
            "enabled": False,
            "api_key": "",
            "from_number": "",
            "to_numbers": []
        }
    },
    "deduplication_window": 300,  # seconds
    "rate_limit": 10,  # alerts per minute
}

# In-memory store for active alerts
_alerts: Dict[str, Dict[str, Any]] = {}
_alerts_lock = threading.Lock()

# In-memory store for alert history (for deduplication)
_alert_history: List[Dict[str, Any]] = []
_alert_history_lock = threading.Lock()


def configure_alerts(
    enabled: bool = True,
    min_severity: AlertSeverity = AlertSeverity.INFO,
    channels: Optional[Dict[NotificationChannel, Dict[str, Any]]] = None,
    deduplication_window: int = 300,
    rate_limit: int = 10
) -> None:
    """
    Configure the alerting system.
    
    Args:
        enabled: Whether alerting is enabled
        min_severity: The minimum severity level for alerts
        channels: Configuration for notification channels
        deduplication_window: Window for deduplicating alerts (in seconds)
        rate_limit: Maximum rate of alerts (per minute)
    """
    global _alert_config
    
    _alert_config["enabled"] = enabled
    _alert_config["min_severity"] = min_severity
    _alert_config["deduplication_window"] = deduplication_window
    _alert_config["rate_limit"] = rate_limit
    
    if channels:
        for channel, config in channels.items():
            if channel in _alert_config["channels"]:
                _alert_config["channels"][channel].update(config)
    
    logger.info(f"Alerts configured: {_alert_config}")


def trigger_alert(
    title: str,
    message: str,
    severity: AlertSeverity = AlertSeverity.INFO,
    context: Optional[Dict[str, Any]] = None,
    notification_channels: Optional[List[NotificationChannel]] = None,
    alert_id: Optional[str] = None,
    group_by: Optional[str] = None
) -> Optional[str]:
    """
    Trigger an alert.
    
    Args:
        title: The title of the alert
        message: The alert message
        severity: The severity level of the alert
        context: Additional context for the alert
        notification_channels: Channels to notify (defaults to all enabled channels)
        alert_id: Optional ID for the alert (for updating existing alerts)
        group_by: Optional key for grouping similar alerts
        
    Returns:
        The ID of the triggered alert, or None if the alert was not triggered
    """
    if not _alert_config["enabled"]:
        logger.debug(f"Alerting is disabled. Skipping alert: {title}")
        return None
    
    if severity.value not in [s.value for s in AlertSeverity]:
        logger.warning(f"Invalid severity level: {severity}. Using INFO.")
        severity = AlertSeverity.INFO
    
    if _alert_config["min_severity"].value != AlertSeverity.INFO.value:
        # Check if the alert severity is below the minimum
        severity_values = [s.value for s in AlertSeverity]
        if severity_values.index(severity.value) < severity_values.index(_alert_config["min_severity"].value):
            logger.debug(f"Alert severity ({severity.value}) is below minimum ({_alert_config['min_severity'].value}). Skipping.")
            return None
    
    # Generate a unique ID if one is not provided
    if not alert_id:
        import uuid
        alert_id = str(uuid.uuid4())
    
    # Create the alert object
    alert = {
        "id": alert_id,
        "title": title,
        "message": message,
        "severity": severity.value,
        "state": AlertState.ACTIVE.value,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "context": context or {},
        "group_by": group_by
    }
    
    # Check for duplicates
    if _is_duplicate_alert(alert):
        logger.debug(f"Duplicate alert: {title}. Skipping.")
        return None
    
    # Check rate limit
    if _is_rate_limited():
        logger.warning(f"Alert rate limit exceeded. Skipping alert: {title}")
        return None
    
    # Store the alert
    with _alerts_lock:
        _alerts[alert_id] = alert
    
    # Add to alert history for deduplication
    with _alert_history_lock:
        _alert_history.append(alert)
        # Trim history to the deduplication window
        _trim_alert_history()
    
    # Send notifications
    _send_notifications(alert, notification_channels)
    
    logger.info(f"Alert triggered: {title} (id={alert_id}, severity={severity.value})")
    
    return alert_id


def update_alert(
    alert_id: str,
    state: Optional[AlertState] = None,
    message: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Update an existing alert.
    
    Args:
        alert_id: The ID of the alert to update
        state: The new state of the alert
        message: The new message for the alert
        context: Additional context to add to the alert
        
    Returns:
        True if the alert was updated, False otherwise
    """
    with _alerts_lock:
        if alert_id not in _alerts:
            logger.warning(f"Alert not found: {alert_id}")
            return False
        
        alert = _alerts[alert_id]
        
        if state:
            alert["state"] = state.value
        
        if message:
            alert["message"] = message
        
        if context:
            alert["context"].update(context)
        
        alert["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        logger.info(f"Alert updated: {alert['title']} (id={alert_id}, state={alert['state']})")
        
        return True


def resolve_alert(alert_id: str, resolution_message: Optional[str] = None) -> bool:
    """
    Resolve an alert.
    
    Args:
        alert_id: The ID of the alert to resolve
        resolution_message: Optional message explaining the resolution
        
    Returns:
        True if the alert was resolved, False otherwise
    """
    context = {}
    if resolution_message:
        context["resolution_message"] = resolution_message
    
    return update_alert(alert_id, AlertState.RESOLVED, context=context)


def acknowledge_alert(alert_id: str, acknowledged_by: Optional[str] = None) -> bool:
    """
    Acknowledge an alert.
    
    Args:
        alert_id: The ID of the alert to acknowledge
        acknowledged_by: The person or system acknowledging the alert
        
    Returns:
        True if the alert was acknowledged, False otherwise
    """
    context = {}
    if acknowledged_by:
        context["acknowledged_by"] = acknowledged_by
        context["acknowledged_at"] = datetime.utcnow().isoformat() + "Z"
    
    return update_alert(alert_id, AlertState.ACKNOWLEDGED, context=context)


def get_active_alerts(
    severity: Optional[AlertSeverity] = None,
    context_filter: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Get all active alerts, optionally filtered by severity or context.
    
    Args:
        severity: Optional severity filter
        context_filter: Optional context filter
        
    Returns:
        A list of active alerts
    """
    with _alerts_lock:
        active_alerts = [
            alert for alert in _alerts.values()
            if alert["state"] == AlertState.ACTIVE.value
        ]
    
    # Filter by severity if provided
    if severity:
        active_alerts = [
            alert for alert in active_alerts
            if alert["severity"] == severity.value
        ]
    
    # Filter by context if provided
    if context_filter:
        active_alerts = [
            alert for alert in active_alerts
            if all(
                k in alert["context"] and alert["context"][k] == v
                for k, v in context_filter.items()
            )
        ]
    
    return active_alerts


def get_alert(alert_id: str) -> Optional[Dict[str, Any]]:
    """
    Get an alert by ID.
    
    Args:
        alert_id: The ID of the alert to get
        
    Returns:
        The alert object, or None if not found
    """
    with _alerts_lock:
        return _alerts.get(alert_id)


def _is_duplicate_alert(alert: Dict[str, Any]) -> bool:
    """
    Check if an alert is a duplicate of a recent alert.
    
    Args:
        alert: The alert to check
        
    Returns:
        True if the alert is a duplicate, False otherwise
    """
    with _alert_history_lock:
        # Check if there's a similar alert in the history
        for existing_alert in _alert_history:
            # If the alert has a group_by key, use that for deduplication
            if alert["group_by"] and existing_alert.get("group_by") == alert["group_by"]:
                return True
            
            # Otherwise, use title and context for deduplication
            if existing_alert["title"] == alert["title"]:
                # Check if contexts are similar (all shared keys have the same values)
                context_match = True
                for k, v in alert["context"].items():
                    if k in existing_alert["context"] and existing_alert["context"][k] != v:
                        context_match = False
                        break
                
                if context_match:
                    return True
    
    return False


def _is_rate_limited() -> bool:
    """
    Check if the alert rate is currently limited.
    
    Returns:
        True if rate limited, False otherwise
    """
    with _alert_history_lock:
        # Count alerts in the last minute
        now = datetime.utcnow()
        one_minute_ago = (now.timestamp() - 60)
        
        recent_alerts = [
            alert for alert in _alert_history
            if datetime.fromisoformat(alert["created_at"].rstrip("Z")).timestamp() > one_minute_ago
        ]
        
        return len(recent_alerts) >= _alert_config["rate_limit"]


def _trim_alert_history() -> None:
    """Trim the alert history to the deduplication window."""
    now = datetime.utcnow().timestamp()
    dedup_window = _alert_config["deduplication_window"]
    
    # Keep only alerts within the deduplication window
    _alert_history[:] = [
        alert for alert in _alert_history
        if now - datetime.fromisoformat(alert["created_at"].rstrip("Z")).timestamp() < dedup_window
    ]


def _send_notifications(
    alert: Dict[str, Any],
    channels: Optional[List[NotificationChannel]] = None
) -> None:
    """
    Send notifications for an alert.
    
    Args:
        alert: The alert to send notifications for
        channels: The channels to send notifications to
    """
    # Determine which channels to use
    if not channels:
        channels = [
            channel for channel, config in _alert_config["channels"].items()
            if config.get("enabled", False)
        ]
    else:
        # Filter out disabled channels
        channels = [
            channel for channel in channels
            if _alert_config["channels"].get(channel, {}).get("enabled", False)
        ]
    
    # Send notifications to each channel
    for channel in channels:
        try:
            if channel == NotificationChannel.CONSOLE:
                _send_console_notification(alert)
            elif channel == NotificationChannel.EMAIL:
                _send_email_notification(alert)
            elif channel == NotificationChannel.SLACK:
                _send_slack_notification(alert)
            elif channel == NotificationChannel.WEBHOOK:
                _send_webhook_notification(alert)
            elif channel == NotificationChannel.SMS:
                _send_sms_notification(alert)
        except Exception as e:
            logger.error(f"Failed to send {channel.value} notification: {str(e)}")


def _send_console_notification(alert: Dict[str, Any]) -> None:
    """
    Send a notification to the console.
    
    Args:
        alert: The alert to send
    """
    severity = alert["severity"].upper()
    title = alert["title"]
    message = alert["message"]
    
    logger.warning(f"ALERT [{severity}] {title}: {message}")


def _send_email_notification(alert: Dict[str, Any]) -> None:
    """
    Send an email notification.
    
    Args:
        alert: The alert to send
    """
    config = _alert_config["channels"][NotificationChannel.EMAIL]
    
    # Skip if email is not configured
    if not config.get("smtp_server") or not config.get("from_email") or not config.get("to_emails"):
        logger.warning("Email notification channel is not fully configured.")
        return
    
    # Create the email message
    msg = MIMEMultipart()
    msg["From"] = config["from_email"]
    msg["To"] = ", ".join(config["to_emails"])
    msg["Subject"] = f"[{alert['severity'].upper()}] {alert['title']}"
    
    # Create the email body
    body = f"""
    Alert: {alert['title']}
    Severity: {alert['severity'].upper()}
    Time: {alert['created_at']}
    
    Message:
    {alert['message']}
    
    Context:
    {json.dumps(alert['context'], indent=2)}
    
    Alert ID: {alert['id']}
    """
    
    msg.attach(MIMEText(body, "plain"))
    
    # Send the email
    try:
        server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
        server.starttls()
        
        if config.get("smtp_username") and config.get("smtp_password"):
            server.login(config["smtp_username"], config["smtp_password"])
        
        server.send_message(msg)
        server.quit()
        
        logger.debug(f"Email notification sent for alert: {alert['id']}")
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise


def _send_slack_notification(alert: Dict[str, Any]) -> None:
    """
    Send a Slack notification.
    
    Args:
        alert: The alert to send
    """
    config = _alert_config["channels"][NotificationChannel.SLACK]
    
    # Skip if Slack is not configured
    if not config.get("webhook_url"):
        logger.warning("Slack notification channel is not fully configured.")
        return
    
    # Create the Slack message
    slack_message = {
        "attachments": [
            {
                "fallback": f"[{alert['severity'].upper()}] {alert['title']}: {alert['message']}",
                "color": _get_severity_color(alert["severity"]),
                "title": alert["title"],
                "text": alert["message"],
                "fields": [
                    {
                        "title": "Severity",
                        "value": alert["severity"].upper(),
                        "short": True
                    },
                    {
                        "title": "Time",
                        "value": alert["created_at"],
                        "short": True
                    }
                ],
                "footer": f"Alert ID: {alert['id']}"
            }
        ]
    }
    
    # Add context fields
    for key, value in alert["context"].items():
        slack_message["attachments"][0]["fields"].append({
            "title": key,
            "value": str(value),
            "short": True
        })
    
    # Send the Slack message
    try:
        import requests
        response = requests.post(
            config["webhook_url"],
            json=slack_message,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        logger.debug(f"Slack notification sent for alert: {alert['id']}")
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {str(e)}")
        raise


def _send_webhook_notification(alert: Dict[str, Any]) -> None:
    """
    Send a webhook notification.
    
    Args:
        alert: The alert to send
    """
    config = _alert_config["channels"][NotificationChannel.WEBHOOK]
    
    # Skip if webhook is not configured
    if not config.get("url"):
        logger.warning("Webhook notification channel is not fully configured.")
        return
    
    # Send the webhook
    try:
        import requests
        response = requests.post(
            config["url"],
            json=alert,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        logger.debug(f"Webhook notification sent for alert: {alert['id']}")
    except Exception as e:
        logger.error(f"Failed to send webhook notification: {str(e)}")
        raise


def _send_sms_notification(alert: Dict[str, Any]) -> None:
    """
    Send an SMS notification.
    
    Args:
        alert: The alert to send
    """
    config = _alert_config["channels"][NotificationChannel.SMS]
    
    # Skip if SMS is not configured
    if not config.get("api_key") or not config.get("from_number") or not config.get("to_numbers"):
        logger.warning("SMS notification channel is not fully configured.")
        return
    
    # Create the SMS message
    message = f"[{alert['severity'].upper()}] {alert['title']}: {alert['message']}"
    
    # This is a placeholder - in a real implementation, we would use a specific
    # SMS service API (like Twilio, AWS SNS, etc.)
    logger.info(f"Would send SMS: {message}")
    logger.debug(f"SMS notification simulated for alert: {alert['id']}")


def _get_severity_color(severity: str) -> str:
    """
    Get a color corresponding to an alert severity.
    
    Args:
        severity: The severity level
        
    Returns:
        A color hex code
    """
    severity_colors = {
        AlertSeverity.INFO.value: "#2196F3",  # Blue
        AlertSeverity.WARNING.value: "#FF9800",  # Orange
        AlertSeverity.ERROR.value: "#F44336",  # Red
        AlertSeverity.CRITICAL.value: "#9C27B0"  # Purple
    }
    
    return severity_colors.get(severity, "#2196F3")  # Default to blue


class AlertRule:
    """
    A rule for triggering alerts based on metric conditions.
    """
    
    def __init__(
        self,
        name: str,
        metric_name: str,
        condition: Callable[[float], bool],
        alert_title: str,
        alert_message: str,
        severity: AlertSeverity = AlertSeverity.WARNING,
        context: Optional[Dict[str, Any]] = None,
        cooldown_period: int = 300
    ):
        """
        Initialize a new alert rule.
        
        Args:
            name: The name of the rule
            metric_name: The name of the metric to check
            condition: A function that takes the metric value and returns True if an alert should be triggered
            alert_title: The title of the alert to trigger
            alert_message: The message of the alert to trigger
            severity: The severity of the alert to trigger
            context: Additional context for the alert
            cooldown_period: The cooldown period between alerts (in seconds)
        """
        self.name = name
        self.metric_name = metric_name
        self.condition = condition
        self.alert_title = alert_title
        self.alert_message = alert_message
        self.severity = severity
        self.context = context or {}
        self.cooldown_period = cooldown_period
        self.last_triggered = 0
    
    def check(self, metric_value: float) -> Optional[str]:
        """
        Check if an alert should be triggered based on the metric value.
        
        Args:
            metric_value: The value of the metric
            
        Returns:
            The ID of the triggered alert, or None if no alert was triggered
        """
        # Skip if we're in the cooldown period
        if time.time() - self.last_triggered < self.cooldown_period:
            return None
        
        # Check if the condition is met
        if self.condition(metric_value):
            # Update context with metric value
            context = dict(self.context)
            context["metric_name"] = self.metric_name
            context["metric_value"] = metric_value
            
            # Trigger the alert
            alert_id = trigger_alert(
                self.alert_title,
                self.alert_message,
                self.severity,
                context,
                group_by=f"metric_rule:{self.name}"
            )
            
            # Update last triggered time
            self.last_triggered = time.time()
            
            return alert_id
        
        return None


# Factory functions for common conditions

def threshold_above(threshold: float) -> Callable[[float], bool]:
    """
    Create a condition that triggers when a metric is above a threshold.
    
    Args:
        threshold: The threshold value
        
    Returns:
        A condition function
    """
    return lambda value: value > threshold


def threshold_below(threshold: float) -> Callable[[float], bool]:
    """
    Create a condition that triggers when a metric is below a threshold.
    
    Args:
        threshold: The threshold value
        
    Returns:
        A condition function
    """
    return lambda value: value < threshold


def threshold_outside_range(min_value: float, max_value: float) -> Callable[[float], bool]:
    """
    Create a condition that triggers when a metric is outside a range.
    
    Args:
        min_value: The minimum acceptable value
        max_value: The maximum acceptable value
        
    Returns:
        A condition function
    """
    return lambda value: value < min_value or value > max_value
