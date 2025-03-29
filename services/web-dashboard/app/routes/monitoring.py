"""
Monitoring routes for the web dashboard application.

This module handles the routes for the monitoring dashboard, including
service health, metrics, alerts, and logs.
"""

from datetime import datetime, timedelta
import random
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required

# Create blueprint
monitoring = Blueprint('monitoring', __name__, url_prefix='/monitoring')


@monitoring.route('/')
@login_required
def index():
    """
    Render the monitoring dashboard home page.
    """
    # In a real implementation, we would fetch this data from the monitoring system
    # This is just placeholder data for demonstration purposes
    
    # Service data
    services = [
        {
            "name": "api-gateway",
            "status": "healthy",
            "uptime": "5d 14h 23m",
            "cpu_usage": 32,
            "memory_usage": 45,
            "last_response_time": 87,
        },
        {
            "name": "agent-orchestrator",
            "status": "healthy",
            "uptime": "5d 13h 42m",
            "cpu_usage": 28,
            "memory_usage": 42,
            "last_response_time": 63,
        },
        {
            "name": "model-orchestration",
            "status": "degraded",
            "uptime": "3d 8h 12m",
            "cpu_usage": 76,
            "memory_usage": 82,
            "last_response_time": 215,
        },
        {
            "name": "planning-system",
            "status": "healthy",
            "uptime": "5d 14h 10m",
            "cpu_usage": 35,
            "memory_usage": 48,
            "last_response_time": 92,
        },
        {
            "name": "tool-integration",
            "status": "healthy",
            "uptime": "5d 14h 5m",
            "cpu_usage": 22,
            "memory_usage": 38,
            "last_response_time": 75,
        },
        {
            "name": "project-coordinator",
            "status": "unhealthy",
            "uptime": "0d 1h 32m",
            "cpu_usage": 95,
            "memory_usage": 91,
            "last_response_time": 487,
        },
        {
            "name": "web-dashboard",
            "status": "healthy",
            "uptime": "5d 14h 22m",
            "cpu_usage": 25,
            "memory_usage": 39,
            "last_response_time": 43,
        },
    ]
    
    # Alerts
    alerts = [
        {
            "id": 1,
            "service": "model-orchestration",
            "title": "High Response Time",
            "severity": "warning",
            "time": (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "status": "active",
            "description": "Response time exceeded 200ms threshold for 10 minutes.",
        },
        {
            "id": 2,
            "service": "project-coordinator",
            "title": "Service Restart",
            "severity": "error",
            "time": (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "status": "active",
            "description": "Service restarted unexpectedly and is not fully recovered.",
        },
        {
            "id": 3,
            "service": "project-coordinator",
            "title": "High CPU Usage",
            "severity": "critical",
            "time": (datetime.now() - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
            "status": "active",
            "description": "CPU usage has been above 90% for 30 minutes.",
        },
        {
            "id": 4,
            "service": "api-gateway",
            "title": "Multiple Authentication Failures",
            "severity": "warning",
            "time": (datetime.now() - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S"),
            "status": "acknowledged",
            "description": "Multiple failed authentication attempts from the same IP address.",
        },
        {
            "id": 5,
            "service": "tool-integration",
            "title": "Database Connection Issue",
            "severity": "error",
            "time": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "status": "resolved",
            "description": "Intermittent database connection failures were observed.",
        },
    ]
    
    # Generate time series data for charts
    now = datetime.now()
    time_points = 12
    
    # Request rate data
    request_rate_labels = [(now - timedelta(hours=i)).strftime("%H:%M") for i in range(time_points)]
    request_rate_labels.reverse()
    
    request_rate_data = []
    base_value = 120
    for i in range(time_points):
        # Add some random variation
        request_rate_data.append(base_value + random.randint(-20, 30))
    
    # Request distribution data
    request_distribution_labels = [
        "API Gateway", "Agent Orchestrator", "Model Orchestration", 
        "Planning System", "Tool Integration", "Project Coordinator"
    ]
    
    request_distribution_data = [
        random.randint(100, 500),
        random.randint(50, 200),
        random.randint(200, 400),
        random.randint(100, 300),
        random.randint(50, 150),
        random.randint(75, 225),
    ]
    
    # Response time data
    response_time_labels = request_rate_labels
    
    response_time_datasets = [
        {
            "name": "API Gateway",
            "color": "78, 115, 223",
            "data": [random.randint(50, 100) for _ in range(time_points)],
        },
        {
            "name": "Agent Orchestrator",
            "color": "28, 200, 138",
            "data": [random.randint(40, 90) for _ in range(time_points)],
        },
        {
            "name": "Model Orchestration",
            "color": "246, 194, 62",
            "data": [random.randint(150, 250) for _ in range(time_points)],
        },
        {
            "name": "Planning System",
            "color": "54, 185, 204",
            "data": [random.randint(70, 120) for _ in range(time_points)],
        },
        {
            "name": "Project Coordinator",
            "color": "231, 74, 59",
            "data": [random.randint(200, 500) for _ in range(time_points)],
        },
    ]
    
    # Summary stats
    service_count = len(services)
    healthy_service_count = sum(1 for service in services if service["status"] == "healthy")
    active_alert_count = sum(1 for alert in alerts if alert["status"] in ["active", "acknowledged"])
    request_count_24h = sum(request_rate_data) * 24
    
    return render_template(
        'monitoring/index.html',
        services=services,
        alerts=alerts,
        service_count=service_count,
        healthy_service_count=healthy_service_count,
        active_alert_count=active_alert_count,
        request_count_24h=request_count_24h,
        request_rate_labels=request_rate_labels,
        request_rate_data=request_rate_data,
        request_distribution_labels=request_distribution_labels,
        request_distribution_data=request_distribution_data,
        response_time_labels=response_time_labels,
        response_time_datasets=response_time_datasets,
    )


@monitoring.route('/service/<service_name>')
@login_required
def service_detail(service_name):
    """
    Render the service detail page.
    """
    # In a real implementation, we would fetch data for the specific service
    return render_template('monitoring/service_detail.html', service_name=service_name)


@monitoring.route('/alert/<int:alert_id>')
@login_required
def alert_detail(alert_id):
    """
    Render the alert detail page.
    """
    # In a real implementation, we would fetch data for the specific alert
    return render_template('monitoring/alert_detail.html', alert_id=alert_id)


@monitoring.route('/acknowledge_alert/<int:alert_id>')
@login_required
def acknowledge_alert(alert_id):
    """
    Acknowledge an alert.
    """
    # In a real implementation, we would update the alert status in the database
    flash(f"Alert {alert_id} acknowledged", "success")
    return redirect(url_for('monitoring.index'))


@monitoring.route('/resolve_alert/<int:alert_id>')
@login_required
def resolve_alert(alert_id):
    """
    Resolve an alert.
    """
    # In a real implementation, we would update the alert status in the database
    flash(f"Alert {alert_id} resolved", "success")
    return redirect(url_for('monitoring.index'))


@monitoring.route('/metrics')
@login_required
def metrics():
    """
    Return metrics for all services.
    """
    # In a real implementation, we would fetch metrics from the monitoring system
    return jsonify({
        "metrics": [
            {"name": "cpu_usage", "value": 45.2, "service": "api-gateway"},
            {"name": "memory_usage", "value": 62.7, "service": "api-gateway"},
            {"name": "request_count", "value": 1245, "service": "api-gateway"},
            # More metrics...
        ]
    })


@monitoring.route('/logs')
@login_required
def logs():
    """
    Return logs for all services.
    """
    # In a real implementation, we would fetch logs from the logging system
    return render_template('monitoring/logs.html')
