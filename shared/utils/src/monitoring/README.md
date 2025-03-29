# Berrys_AgentsV2 Monitoring and Observability System

This is the core monitoring and observability system for the Berrys_AgentsV2 platform. It provides comprehensive tools for collecting metrics, structured logging, distributed tracing, health checks, alerts, and integration with CI/CD pipelines.

## Features

- **Metrics Collection**: Track service and application performance metrics
- **Structured Logging**: Consistent logging with context across all services
- **Distributed Tracing**: Track requests across service boundaries
- **Health Checks**: Monitor service and dependency health
- **Alerting**: Detect and notify about anomalies and issues
- **CI/CD Integration**: Verify deployments and detect performance regressions
- **Framework Integrations**: Ready-to-use middleware for FastAPI and Flask
- **Exporters**: Export metrics to Prometheus and other monitoring tools

## Getting Started

For detailed information on using the monitoring system, see the [Monitoring and Observability Guide](../../../../docs/developer-guides/monitoring/monitoring-guide.md).

### Quick Start

#### For FastAPI services:

```python
from fastapi import FastAPI
from shared.utils.src.monitoring.middleware.fastapi import setup_monitoring

app = FastAPI()

# Set up monitoring with default settings
setup_monitoring(app, service_name="your-service-name")
```

#### For Flask services:

```python
from flask import Flask
from shared.utils.src.monitoring.middleware.flask import setup_monitoring

app = Flask(__name__)

# Set up monitoring with default settings
setup_monitoring(app, service_name="your-service-name")
```

## Package Structure

- `metrics.py`: Metrics collection and reporting
- `logging.py`: Structured logging system
- `tracing.py`: Distributed tracing system
- `health.py`: Health check system
- `alerts.py`: Alerting system
- `middleware/`: Framework integrations
  - `fastapi.py`: FastAPI middleware
  - `flask.py`: Flask middleware
- `exporters/`: Metric exporters
  - `prometheus.py`: Prometheus exporter
- `ci_cd/`: CI/CD integration
  - `deployment_verification.py`: Deployment verification tools

## Integrating with Services

For a new service, add the following to your service's initialization:

```python
from shared.utils.src.monitoring import configure_logging, configure_metrics
from shared.utils.src.monitoring.middleware.fastapi import setup_monitoring

# Configure logging
configure_logging(
    level="INFO",
    json_format=True,
    service_name="your-service-name",
)

# Configure metrics
configure_metrics(
    backend="prometheus",
    prefix="berrys_agents",
    default_tags={"service": "your-service-name"},
)

# Set up monitoring middleware
setup_monitoring(app, service_name="your-service-name")
```

## Best Practices

- Use consistent naming conventions for metrics and logs
- Add relevant context to logs and spans
- Register health checks for all critical dependencies
- Set appropriate alert thresholds to avoid noise
- Use trace IDs in logs for correlation

## CI/CD Integration

Use the provided monitoring workflow template in your CI/CD pipelines:

```yaml
monitor:
  uses: ./.github/workflows/templates/monitoring.yml
  with:
    service_name: your-service-name
    environment: development
    deploy_url: https://your-service-url
```

## Contributing

When extending the monitoring system:

1. Follow the existing patterns and naming conventions
2. Add comprehensive documentation
3. Write tests for new functionality
4. Ensure backward compatibility
