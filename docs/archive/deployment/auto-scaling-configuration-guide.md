# Auto-scaling Configuration Guide

This document provides guidance for implementing auto-scaling capabilities in the Berrys_AgentsV2 platform as part of the Production Deployment and Scaling milestone. It covers horizontal pod autoscaling, database connection pooling, and resource-based scaling strategies.

## Overview

Auto-scaling enables the platform to dynamically adjust resource allocation based on workload demands. This improves resource utilization efficiency, ensures consistent performance under varying loads, and optimizes infrastructure costs. The Berrys_AgentsV2 platform implements multi-layered scaling:

1. **Application Layer Scaling**: Horizontal Pod Autoscaling (HPA) for Kubernetes deployments
2. **Database Layer Scaling**: Connection pooling and query optimization
3. **Infrastructure Layer Scaling**: Cluster autoscaling and resource quotas

## Horizontal Pod Autoscaling

### Core Services Configuration

#### Agent Orchestrator

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-orchestrator-hpa
  namespace: berrys-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-orchestrator
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 20
        periodSeconds: 60
```

#### Model Orchestration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: model-orchestration-hpa
  namespace: berrys-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: model-orchestration
  minReplicas: 3
  maxReplicas: 15
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 65
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  # Custom metrics for model request rate
  - type: Pods
    pods:
      metric:
        name: model_requests_per_second
      target:
        type: AverageValue
        averageValue: 20
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 20
        periodSeconds: 60
```

#### API Gateway

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
  namespace: berrys-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: 100
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 20
        periodSeconds: 60
```

#### Web Dashboard

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-dashboard-hpa
  namespace: berrys-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-dashboard
  minReplicas: 2
  maxReplicas: 6
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 20
        periodSeconds: 60
```

### Custom Metrics Configuration

To enable scaling based on business-specific metrics, we use the Prometheus Adapter for Kubernetes Metrics API. This allows Kubernetes to scale based on metrics like request rate, queue length, and other application-specific metrics.

#### Prometheus Adapter ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-adapter-config
  namespace: monitoring
data:
  config.yaml: |
    rules:
    # Model request rate for model-orchestration service
    - seriesQuery: 'model_requests_total{service="model-orchestration",namespace="berrys-production"}'
      resources:
        overrides:
          namespace: {resource: "namespace"}
          pod: {resource: "pod"}
          service: {resource: "service"}
      name:
        matches: "model_requests_total"
        as: "model_requests_per_second"
      metricsQuery: 'sum(rate(model_requests_total{service="model-orchestration",namespace="berrys-production"}[2m])) by (pod)'
    
    # HTTP request rate for api-gateway service
    - seriesQuery: 'http_requests_total{service="api-gateway",namespace="berrys-production"}'
      resources:
        overrides:
          namespace: {resource: "namespace"}
          pod: {resource: "pod"}
          service: {resource: "service"}
      name:
        matches: "http_requests_total"
        as: "http_requests_per_second"
      metricsQuery: 'sum(rate(http_requests_total{service="api-gateway",namespace="berrys-production"}[2m])) by (pod)'
    
    # Agent creation rate for agent-orchestrator service
    - seriesQuery: 'agent_created_total{service="agent-orchestrator",namespace="berrys-production"}'
      resources:
        overrides:
          namespace: {resource: "namespace"}
          pod: {resource: "pod"}
          service: {resource: "service"}
      name:
        matches: "agent_created_total"
        as: "agent_creation_rate"
      metricsQuery: 'sum(rate(agent_created_total{service="agent-orchestrator",namespace="berrys-production"}[5m])) by (pod)'
```

### Service Metrics Configuration

Each service should expose metrics for auto-scaling. Here's an example of how to configure metrics in Python services:

```python
from prometheus_client import Counter, Histogram, start_http_server
import time

# Initialize metrics
http_requests_total = Counter(
    'http_requests_total', 
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration_seconds = Histogram(
    'request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Example FastAPI middleware to record metrics
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    http_requests_total.labels(
        method=request.method, 
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

# Start metrics server on port 8000
start_http_server(8000)
```

## Database Connection Pooling

### Connection Pool Configuration

Configure database connection pooling in all services to efficiently manage database connections. Here's an example configuration for SQLAlchemy:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Configure the connection pool
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,               # Number of connections to keep open
    max_overflow=20,            # Maximum number of connections to create beyond pool_size
    pool_timeout=30,            # Seconds to wait before giving up on getting a connection
    pool_recycle=1800,          # Recycle connections after 30 minutes (1800 seconds)
    pool_pre_ping=True          # Verify connections before using them
)

Session = sessionmaker(bind=engine)
```

### Connection Pool Monitoring

To monitor connection pool usage, add the following metrics:

```python
from prometheus_client import Gauge

db_connections_total = Gauge(
    'database_connections_total',
    'Total number of database connections',
    ['database', 'status']  # status can be 'used', 'available', 'overflow'
)

def update_connection_metrics():
    status = engine.pool.status()
    db_connections_total.labels(database='postgres', status='used').set(status['checkedout'])
    db_connections_total.labels(database='postgres', status='available').set(status['checkedin'])
    db_connections_total.labels(database='postgres', status='overflow').set(status['overflow'])

# Update metrics periodically
import threading
def metrics_worker():
    while True:
        update_connection_metrics()
        time.sleep(15)  # Update every 15 seconds

metrics_thread = threading.Thread(target=metrics_worker)
metrics_thread.daemon = True
metrics_thread.start()
```

### Connection Pool Best Practices

1. **Size Appropriately**: Set pool size based on service needs and database limits
2. **Recycle Connections**: Set appropriate pool_recycle to avoid stale connections
3. **Health Checks**: Use pool_pre_ping to verify connections before use
4. **Timeout Configuration**: Set appropriate timeout values to avoid hanging
5. **Monitoring**: Monitor connection usage to detect leaks or inadequate sizing

## Resource-based Scaling

### Resource Quotas

Implement resource quotas for each namespace to prevent resource exhaustion:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: berrys-production-quota
  namespace: berrys-production
spec:
  hard:
    requests.cpu: "24"          # Maximum CPU request for all pods
    requests.memory: "48Gi"     # Maximum memory request for all pods
    limits.cpu: "32"           # Maximum CPU limit for all pods
    limits.memory: "64Gi"      # Maximum memory limit for all pods
    pods: "100"                # Maximum number of pods
    persistentvolumeclaims: "25" # Maximum number of PVCs
    services: "40"             # Maximum number of services
```

### Pod Resource Configuration

Configure resource requests and limits for all containers to ensure appropriate resource allocation:

#### Agent Orchestrator

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-orchestrator
  namespace: berrys-production
spec:
  # ... other configuration ...
  template:
    spec:
      containers:
      - name: agent-orchestrator
        image: berrys/agent-orchestrator:latest
        resources:
          requests:
            cpu: "500m"      # Request 0.5 CPU cores
            memory: "512Mi"  # Request 512 MB of memory
          limits:
            cpu: "1"         # Limit to 1 CPU core
            memory: "1Gi"    # Limit to 1 GB of memory
```

#### Model Orchestration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: model-orchestration
  namespace: berrys-production
spec:
  # ... other configuration ...
  template:
    spec:
      containers:
      - name: model-orchestration
        image: berrys/model-orchestration:latest
        resources:
          requests:
            cpu: "1"         # Request 1 CPU core
            memory: "1Gi"    # Request 1 GB of memory
          limits:
            cpu: "2"         # Limit to 2 CPU cores
            memory: "2Gi"    # Limit to 2 GB of memory
```

### Pod Disruption Budgets

Configure Pod Disruption Budgets to ensure service availability during node maintenance:

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: agent-orchestrator-pdb
  namespace: berrys-production
spec:
  minAvailable: 2  # At least 2 pods must be available
  selector:
    matchLabels:
      app: agent-orchestrator
```

### Cluster Autoscaling

Configure Kubernetes cluster autoscaling to automatically adjust the number of nodes based on resource demand:

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: ClusterAutoscaler
metadata:
  name: berrys-cluster-autoscaler
spec:
  scaleDown:
    enabled: true
    delayAfterAdd: 10m
    delayAfterDelete: 10m
    delayAfterFailure: 3m
    unneededTime: 10m
  scaleUp:
    enabled: true
    skipNodesWithLocalStorage: true
    skipNodesWithSystemPods: true
  nodeGroups:
  - name: default-node-group
    minSize: 3
    maxSize: 10
```

## Implementation Plan

### Phase 1: Metrics Collection Setup

1. Configure Prometheus and metrics collection for all services
2. Test and validate metric collection
3. Create dashboards for monitoring metrics

### Phase 2: HPA Configuration

1. Deploy HPA configurations for core services
2. Test automatic scaling under load
3. Fine-tune scaling parameters based on testing results

### Phase 3: Database Connection Pooling

1. Implement connection pooling in all services
2. Configure connection pool monitoring
3. Test database performance under varying loads

### Phase 4: Resource Quotas and Limits

1. Define resource quotas for all namespaces
2. Configure appropriate resource requests and limits for all containers
3. Implement Pod Disruption Budgets for critical services

### Phase 5: Cluster Autoscaling

1. Configure cluster autoscaler
2. Test node scaling under load
3. Verify node scaling policies

## Testing and Validation

### Load Testing

1. **Gradual Load Increase**: Start with baseline load and gradually increase
2. **Sustained Peak Load**: Maintain peak load for extended period
3. **Rapid Spike Testing**: Simulate sudden traffic spikes
4. **Long-running Load**: Test behavior over extended periods (8+ hours)

### Metrics to Monitor

1. **Pod Scale Events**: Frequency and timing of scale up/down events
2. **Resource Utilization**: CPU, memory, and network usage before, during, and after scaling
3. **Response Times**: API response times under different load conditions
4. **Database Connections**: Connection pool utilization and query performance
5. **Error Rates**: Changes in error rates during scaling events

### Validation Criteria

1. **Scaling Responsiveness**: Time to scale up in response to increased load
2. **Stability**: No thrashing (rapid scale up/down cycles)
3. **Resource Efficiency**: Efficient resource usage after scaling
4. **Performance Consistency**: Consistent response times before, during, and after scaling
5. **Error Rate Stability**: No increase in error rates during scaling operations

## Best Practices

### Scaling Thresholds

1. **Conservative Thresholds**: Start with conservative thresholds (e.g., 70% CPU, 80% memory)
2. **Asymmetric Policies**: Use different thresholds for scaling up vs. scaling down
3. **Stabilization Windows**: Configure appropriate stabilization windows to prevent thrashing
4. **Business-Specific Metrics**: Use custom metrics for better alignment with business requirements

### Monitoring and Alerting

1. **Scale Event Logging**: Record all scaling events for analysis
2. **Proactive Alerts**: Set up alerts for unusual scaling patterns
3. **Capacity Warnings**: Configure alerts for approaching resource limits
4. **Correlation Analysis**: Correlate scaling events with performance metrics

### Resource Management

1. **Accurate Resource Requests**: Set resource requests based on actual usage patterns
2. **Reasonable Limits**: Configure limits to prevent resource hogging
3. **Quality of Service**: Use appropriate QoS classes for different workloads
4. **Prioritization**: Configure Pod Priority and Preemption for critical services

## Troubleshooting

### Common Issues and Solutions

1. **Scaling Too Slowly**
   - Reduce stabilization windows
   - Lower CPU/memory thresholds
   - Check HPA metrics for accuracy

2. **Scaling Too Frequently (Thrashing)**
   - Increase stabilization windows
   - Adjust scaling policies to be less aggressive
   - Check for oscillating load patterns

3. **Not Scaling When Expected**
   - Verify metrics are being collected correctly
   - Check HPA configuration for errors
   - Ensure custom metrics are properly defined
   - Verify no resource quotas are blocking scaling

4. **Database Connection Issues**
   - Check connection pool configuration
   - Verify connection leak detection
   - Monitor connection utilization
   - Test database performance under load

## Future Enhancements

1. **Predictive Scaling**: Implement algorithms to predict scaling needs before they occur
2. **Machine Learning-based Scaling**: Use ML to optimize scaling decisions based on historical patterns
3. **Multi-dimensional Scaling**: Scale based on combinations of metrics
4. **Cost-Based Scaling**: Optimize scaling decisions based on infrastructure costs
5. **Geographic Load Balancing**: Distribute load across regions based on regional demand patterns
