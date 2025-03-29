# Monitoring and Observability Guide

This guide provides detailed information about the monitoring and observability system for the Berrys_AgentsV2 platform. It explains how to use the monitoring system to gain insights into service health, performance, and behavior.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Metrics Collection](#metrics-collection)
- [Structured Logging](#structured-logging)
- [Distributed Tracing](#distributed-tracing)
- [Health Checks](#health-checks)
- [Alerting](#alerting)
- [Dashboard Integration](#dashboard-integration)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)

## Overview

The Berrys_AgentsV2 monitoring and observability system provides comprehensive visibility into the platform's operation, including:

- Service health and performance metrics
- Structured logging with context
- Distributed tracing across service boundaries
- Health checks and alerting
- Integration with CI/CD for deployment verification
- Dashboards for visualizing metrics and logs

The system is designed to be:

- **Modular**: Each component can be used independently
- **Extensible**: New metrics, exporters, and visualizations can be added
- **Low-overhead**: Minimal performance impact on services
- **Framework-agnostic**: Works with FastAPI, Flask, and other frameworks
- **Integration-ready**: Exports metrics to Prometheus and other monitoring tools

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Access to the shared utilities package

### Basic Integration

To add monitoring to a service, follow these steps:

#### 1. Add dependencies to your service's `requirements.txt`:

```
requests>=2.28.0
prometheus-client>=0.15.0
```

#### 2. For FastAPI services:

```python
from fastapi import FastAPI
from shared.utils.src.monitoring.middleware.fastapi import setup_monitoring

app = FastAPI()

# Set up monitoring with default settings
setup_monitoring(app, service_name="your-service-name")
```

This will:
- Add `/health` and `/metrics` endpoints
- Add middleware for request tracking and metrics collection
- Configure structured logging with request context

#### 3. For Flask services:

```python
from flask import Flask
from shared.utils.src.monitoring.middleware.flask import setup_monitoring

app = Flask(__name__)

# Set up monitoring with default settings
setup_monitoring(app, service_name="your-service-name")
```

## Metrics Collection

The metrics system provides utilities for collecting and reporting metrics about service performance, application behavior, and business KPIs.

### Basic Usage

```python
from shared.utils.src.monitoring.metrics import (
    increment_counter,
    gauge,
    histogram,
    record_timer,
)

# Increment a counter
increment_counter("api_requests_total", {"endpoint": "/users", "method": "GET"})

# Record a gauge value
gauge("active_connections", 42, {"service": "api-gateway"})

# Record a value in a histogram
histogram("response_size_bytes", 1024, {"endpoint": "/users", "method": "GET"})

# Time a function execution
@record_timer("function_execution_time", {"function": "process_data"})
def process_data():
    # Function implementation
    pass
```

### Configuration

```python
from shared.utils.src.monitoring.metrics import configure_metrics, MetricsBackend

# Configure metrics collection
configure_metrics(
    backend=MetricsBackend.PROMETHEUS,  # Or STATSD, CONSOLE
    prefix="berrys_agents",
    default_tags={"environment": "production", "service": "api-gateway"},
    enabled=True,
)
```

## Structured Logging

The logging system provides consistent, structured logging across all services with JSON formatting, context enrichment, and correlation IDs.

### Basic Usage

```python
from shared.utils.src.monitoring.logging import get_logger, LogLevel, configure_logging

# Configure logging
configure_logging(
    level=LogLevel.INFO,
    json_format=True,
    log_to_console=True,
    log_file="service.log",
    service_name="api-gateway",
)

# Get a logger
logger = get_logger(__name__)

# Log messages with context
logger.info("Processing request", extra={"request_id": "123", "user_id": "456"})

# Log at different levels
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)
logger.critical("Critical message", exc_info=True)
```

### Request Context Logging

```python
from shared.utils.src.monitoring.logging import get_request_logger

# Get a logger with request context
logger = get_request_logger(
    request_id="request-123",
    user_id="user-456",
    session_id="session-789",
    ip_address="192.168.1.1",
)

# Log with request context
logger.info("Processing request")
```

## Distributed Tracing

The tracing system allows tracking requests as they flow through the system, measuring performance, and diagnosing issues across service boundaries.

### Basic Usage

```python
from shared.utils.src.monitoring.tracing import trace, tracer, SpanKind

# Trace a function
@trace("process_request")
def process_request(request_data):
    # Function implementation
    pass

# Manually create and manage spans
with tracer.start_as_current_span("operation_name", kind=SpanKind.SERVER) as span:
    span.set_attribute("key", "value")
    # Operation implementation
```

### Cross-Service Tracing

```python
from shared.utils.src.monitoring.tracing import inject_context_into_headers, extract_context_from_headers

# In the calling service
headers = {}
inject_context_into_headers(headers)
response = requests.get("https://other-service/endpoint", headers=headers)

# In the called service
trace_context = extract_context_from_headers(request.headers)
```

## Health Checks

The health check system provides a standard way to check the health of services and their dependencies.

### Basic Usage

```python
from shared.utils.src.monitoring.health import register_health_check, check_health

# Register a health check
@register_health_check("database")
def check_database_connection():
    # Check if database is accessible
    return True, "Database connection is healthy"

# Check health of all registered components
health_status = check_health()

# Get health status for specific component
db_status = check_health("database")
```

### Common Health Checks

```python
from shared.utils.src.monitoring.health import (
    check_database_connection,
    check_redis_connection,
    check_external_service,
)

# Register health checks
register_health_check("database")(check_database_connection("postgresql://localhost/db"))
register_health_check("redis")(check_redis_connection("redis://localhost:6379"))
register_health_check("api")(check_external_service("https://api.example.com/health"))
```

## Alerting

The alerting system provides utilities for detecting, managing, and sending alerts based on monitoring data.

### Basic Usage

```python
from shared.utils.src.monitoring.alerts import (
    trigger_alert,
    AlertSeverity,
    update_alert,
    resolve_alert,
)

# Trigger an alert
alert_id = trigger_alert(
    "High CPU Usage",
    "CPU usage is above 90%",
    AlertSeverity.WARNING,
    {"service": "api-gateway", "cpu_usage": "95%"},
)

# Update an alert
update_alert(alert_id, state=AlertState.ACKNOWLEDGED, 
             message="Working on CPU issue")

# Resolve an alert
resolve_alert(alert_id, resolution_message="CPU usage returned to normal")
```

### Alert Rules

```python
from shared.utils.src.monitoring.alerts import (
    AlertRule,
    threshold_above,
    threshold_below,
    threshold_outside_range,
)

# Create an alert rule for CPU usage
cpu_rule = AlertRule(
    name="high_cpu_usage",
    metric_name="cpu_usage_percent",
    condition=threshold_above(90),
    alert_title="High CPU Usage",
    alert_message="CPU usage is above 90%",
    severity=AlertSeverity.WARNING,
    context={"service": "api-gateway"},
    cooldown_period=300,
)

# Check the rule against a metric value
alert_id = cpu_rule.check(95)
```

## Dashboard Integration

The monitoring system integrates with the Web Dashboard to provide visualizations of metrics, logs, and traces.

### Available Dashboards

- **System Overview**: High-level view of all services
- **Service Dashboard**: Detailed view of a specific service
- **Request Tracing**: Visualization of request traces
- **Log Explorer**: Search and filter logs
- **Alerts Dashboard**: View and manage alerts

### Custom Dashboards

To create a custom dashboard:

1. Create a new dashboard definition in the Web Dashboard
2. Define panels to visualize specific metrics
3. Configure refresh intervals and time ranges
4. Save and share the dashboard

## CI/CD Integration

The monitoring system integrates with the CI/CD pipeline to verify deployments and detect performance regressions.

### Deployment Verification

```yaml
# Example workflow for a service
name: Deploy Service

on:
  push:
    branches: [ main ]

jobs:
  build:
    uses: ./.github/workflows/templates/build.yml
    with:
      service_name: api-gateway

  test:
    needs: build
    uses: ./.github/workflows/templates/test.yml
    with:
      service_name: api-gateway

  deploy:
    needs: test
    uses: ./.github/workflows/templates/deploy.yml
    with:
      service_name: api-gateway
      environment: development

  monitor:
    needs: deploy
    uses: ./.github/workflows/templates/monitoring.yml
    with:
      service_name: api-gateway
      environment: development
      deploy_url: https://dev-api.example.com
      verify_health: true
      verify_metrics: true
      verify_performance: true
```

### Canary Deployments

```yaml
monitor-canary:
  uses: ./.github/workflows/templates/monitoring.yml
  with:
    service_name: api-gateway
    environment: production
    deploy_url: https://canary-api.example.com
    enable_canary: true
    canary_url: https://canary-api.example.com
    production_url: https://api.example.com
    performance_threshold: 1.2  # Allow 20% performance degradation
    monitor_duration: 300  # Monitor for 5 minutes
```

## Best Practices

### Metrics

- Use consistent naming conventions for metrics
- Add relevant tags to metrics for filtering and aggregation
- Focus on actionable metrics that help identify issues
- Avoid high-cardinality tags that can cause performance issues

### Logging

- Use structured logging with context for easier querying
- Include request IDs in logs for correlation
- Log at appropriate levels to avoid noise
- Redact sensitive information from logs

### Tracing

- Use tracing for complex flows across multiple services
- Add relevant attributes to spans for context
- Keep trace sample rate reasonable to avoid performance impact
- Use trace IDs in logs for correlation

### Health Checks

- Keep health checks lightweight and fast
- Return detailed information about failures
- Check all critical dependencies
- Include meaningful status messages

### Alerting

- Define meaningful alert thresholds
- Avoid alert noise by using appropriate severity levels
- Set up proper escalation paths
- Document alert response procedures

### CI/CD

- Verify deployments before exposing them to users
- Use canary deployments for high-risk changes
- Monitor deployment verification results
- Set up automatic rollbacks for failed deployments
