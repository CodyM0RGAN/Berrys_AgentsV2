# Performance Optimization Guide

This document provides comprehensive guidance for implementing performance optimizations as part of the Production Deployment and Scaling milestone. It covers caching strategies, database optimizations, service resource allocation, and request batching/throttling.

## Overview

Performance optimization is critical for ensuring the Berrys_AgentsV2 platform delivers a responsive user experience, efficiently uses resources, and can handle growing workloads. This guide outlines a systematic approach to identifying and implementing performance optimizations across the platform.

## Table of Contents

1. [Caching Strategies](#caching-strategies)
2. [Database Optimization](#database-optimization)
3. [Service Resource Allocation](#service-resource-allocation)
4. [Request Batching and Throttling](#request-batching-and-throttling)
5. [Implementation Plan](#implementation-plan)
6. [Testing and Validation](#testing-and-validation)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)

## Caching Strategies

### Redis Caching Implementation

#### Redis Configuration

Deploy Redis with the following configuration for production:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: berrys-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7.0-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1
            memory: 2Gi
        args:
        - --appendonly yes
        - --maxmemory 1500mb
        - --maxmemory-policy allkeys-lru
        volumeMounts:
        - name: redis-data
          mountPath: /data
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-data
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: berrys-production
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  clusterIP: None
```

#### Service-level Caching

Implement caching in each service using the following Python Redis client configuration:

```python
import redis
from functools import wraps
import json
import hashlib
import time

# Initialize Redis client
redis_client = redis.Redis(
    host='redis.berrys-production.svc.cluster.local',
    port=6379,
    db=0,
    socket_timeout=5,
    socket_connect_timeout=5
)

# Function to generate cache key
def generate_cache_key(prefix, *args, **kwargs):
    key_parts = [prefix]
    
    if args:
        key_parts.append(hashlib.md5(str(args).encode()).hexdigest())
    
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        key_parts.append(hashlib.md5(str(sorted_kwargs).encode()).hexdigest())
    
    return ":".join(key_parts)

# Decorator for caching function results
def cache(prefix, ttl=300):
    """
    Cache decorator for function results.
    
    Args:
        prefix: Prefix for cache key
        ttl: Time to live in seconds (default 5 minutes)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function if not in cache
            result = await func(*args, **kwargs)
            
            # Store in cache
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator
```

Example usage:

```python
# Caching database query results
@cache(prefix="user_projects", ttl=600)
async def get_user_projects(user_id: str):
    return await db.query(Project).filter(Project.user_id == user_id).all()

# Caching expensive computation results
@cache(prefix="project_analytics", ttl=3600)
async def calculate_project_analytics(project_id: str):
    # Expensive calculations...
    return analytics_result
```

#### Cache Invalidation Strategies

Implement cache invalidation when data changes:

```python
# Function to invalidate specific cache keys
def invalidate_cache(prefix, *args, **kwargs):
    cache_key = generate_cache_key(prefix, *args, **kwargs)
    redis_client.delete(cache_key)

# Function to invalidate cache keys by pattern
def invalidate_cache_pattern(pattern):
    for key in redis_client.scan_iter(f"{pattern}*"):
        redis_client.delete(key)

# Example usage in a service:
@router.post("/projects/")
async def create_project(project: ProjectCreate):
    # Create project in database
    db_project = await project_service.create_project(project)
    
    # Invalidate user projects cache
    invalidate_cache("user_projects", user_id=project.user_id)
    
    return db_project
```

#### API Response Caching

Implement HTTP caching headers for API responses:

```python
from fastapi import FastAPI, Response, Depends
from datetime import datetime, timedelta

app = FastAPI()

# Middleware to add cache control headers
@app.middleware("http")
async def add_cache_control_headers(request, call_next):
    response = await call_next(request)
    
    # Skip non-GET requests
    if request.method != "GET":
        return response
    
    # Add cache control headers based on endpoint
    path = request.url.path
    
    if path.startswith("/api/v1/projects"):
        # Project data: short cache time (1 minute)
        response.headers["Cache-Control"] = "private, max-age=60"
    elif path.startswith("/api/v1/reference-data"):
        # Reference data: longer cache time (1 hour)
        response.headers["Cache-Control"] = "public, max-age=3600"
    elif path.startswith("/api/v1/users/me"):
        # Current user data: very short cache time (10 seconds)
        response.headers["Cache-Control"] = "private, max-age=10"
    else:
        # Default: no caching for most API endpoints
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    
    return response
```

#### ETag Implementation

Add ETag support for conditional requests:

```python
import hashlib

def generate_etag(content):
    if isinstance(content, dict) or isinstance(content, list):
        content = json.dumps(content, sort_keys=True)
    
    if isinstance(content, str):
        content = content.encode()
    
    return hashlib.md5(content).hexdigest()

@app.get("/api/v1/projects/{project_id}")
async def get_project(project_id: str, response: Response):
    # Get project from database or cache
    project = await get_project_by_id(project_id)
    
    # Generate ETag for the project
    etag = generate_etag(project)
    response.headers["ETag"] = f'"{etag}"'
    
    # Check If-None-Match header
    if_none_match = request.headers.get("If-None-Match")
    if if_none_match and if_none_match.strip('"') == etag:
        # Return 304 Not Modified if ETag matches
        return Response(status_code=304)
    
    return project
```

### Distributed Caching

Set up Redis Cluster for distributed caching:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
  namespace: berrys-production
spec:
  serviceName: redis-cluster
  replicas: 6  # 3 masters + 3 replicas
  selector:
    matchLabels:
      app: redis-cluster
  template:
    metadata:
      labels:
        app: redis-cluster
    spec:
      containers:
      - name: redis
        image: redis:7.0-alpine
        ports:
        - containerPort: 6379
          name: client
        - containerPort: 16379
          name: gossip
        command:
        - redis-server
        - /conf/redis.conf
        volumeMounts:
        - name: conf
          mountPath: /conf
        - name: data
          mountPath: /data
      volumes:
      - name: conf
        configMap:
          name: redis-cluster-config
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-cluster-config
  namespace: berrys-production
data:
  redis.conf: |
    cluster-enabled yes
    cluster-config-file nodes.conf
    cluster-node-timeout 5000
    appendonly yes
    maxmemory 2gb
    maxmemory-policy allkeys-lru
```

## Database Optimization

### Query Optimization

#### Slow Query Identification

Implement query performance logging in services:

```python
import time
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

@contextmanager
def query_performance_logging(query_name):
    start_time = time.time()
    try:
        yield
    finally:
        execution_time = time.time() - start_time
        logger.info(f"Query execution time: {query_name}, {execution_time:.4f}s")
        
        # Log slow queries (over 100ms)
        if execution_time > 0.1:
            logger.warning(f"Slow query detected: {query_name}, {execution_time:.4f}s")

# Example usage
async def get_user_projects(user_id: str):
    with query_performance_logging("get_user_projects"):
        return await db.query(Project).filter(Project.user_id == user_id).all()
```

#### Index Creation

Add indexes for common query patterns:

```sql
-- User ID index for projects table
CREATE INDEX idx_project_user_id ON project(user_id);

-- Status index for projects table
CREATE INDEX idx_project_status ON project(status);

-- Composite index for filtering projects by user and status
CREATE INDEX idx_project_user_status ON project(user_id, status);

-- Creation date index for sorting
CREATE INDEX idx_project_created_at ON project(created_at);

-- Agent type index for filtering agents
CREATE INDEX idx_agent_type ON agent(agent_type);

-- Agent project ID index for filtering agents by project
CREATE INDEX idx_agent_project_id ON agent(project_id);
```

Implement these indexes using SQLAlchemy migrations:

```python
"""Add performance optimization indexes

Revision ID: abcdef123456
Revises: previous_revision_id
Create Date: 2025-04-22 10:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'abcdef123456'
down_revision = 'previous_revision_id'
branch_labels = None
depends_on = None


def upgrade():
    # Add indexes
    op.create_index('idx_project_user_id', 'project', ['user_id'])
    op.create_index('idx_project_status', 'project', ['status'])
    op.create_index('idx_project_user_status', 'project', ['user_id', 'status'])
    op.create_index('idx_project_created_at', 'project', ['created_at'])
    op.create_index('idx_agent_type', 'agent', ['agent_type'])
    op.create_index('idx_agent_project_id', 'agent', ['project_id'])


def downgrade():
    # Remove indexes
    op.drop_index('idx_project_user_id', table_name='project')
    op.drop_index('idx_project_status', table_name='project')
    op.drop_index('idx_project_user_status', table_name='project')
    op.drop_index('idx_project_created_at', table_name='project')
    op.drop_index('idx_agent_type', table_name='agent')
    op.drop_index('idx_agent_project_id', table_name='agent')
```

#### Query Caching

Implement query result caching with SQLAlchemy:

```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select

# Create a query cache region
from dogpile.cache import make_region

query_cache_region = make_region().configure(
    'dogpile.cache.redis',
    arguments={
        'host': 'redis.berrys-production.svc.cluster.local',
        'port': 6379,
        'db': 1,
        'redis_expiration_time': 60 * 60,  # 1 hour
        'distributed_lock': True
    }
)

# Use the cache region with SQLAlchemy queries
async def get_projects_by_status(session: AsyncSession, status: str):
    cache_key = f"projects_by_status:{status}"
    
    # Try to get from cache
    cached_result = query_cache_region.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Execute query if not in cache
    stmt = select(Project).where(Project.status == status)
    result = await session.execute(stmt)
    projects = result.scalars().all()
    
    # Store in cache
    query_cache_region.set(cache_key, projects)
    
    return projects
```

### Schema Optimization

#### Table Partitioning

Implement table partitioning for large tables:

```sql
-- Create partitioned table for agent_activity logs
CREATE TABLE agent_activity (
    id UUID PRIMARY KEY,
    agent_id UUID NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    details JSONB
) PARTITION BY RANGE (created_at);

-- Create partitions for different time periods
CREATE TABLE agent_activity_y2025m04 PARTITION OF agent_activity
    FOR VALUES FROM ('2025-04-01') TO ('2025-05-01');
    
CREATE TABLE agent_activity_y2025m05 PARTITION OF agent_activity
    FOR VALUES FROM ('2025-05-01') TO ('2025-06-01');
    
-- Add indexes to the partitioned table
CREATE INDEX idx_agent_activity_agent_id ON agent_activity(agent_id);
CREATE INDEX idx_agent_activity_type ON agent_activity(activity_type);
CREATE INDEX idx_agent_activity_created_at ON agent_activity(created_at);
```

Implement this in SQLAlchemy:

```python
from sqlalchemy import Table, Column, String, DateTime, MetaData, text
from sqlalchemy.dialects.postgresql import UUID, JSONB

metadata = MetaData()

# Define the partitioned table
agent_activity = Table(
    'agent_activity', 
    metadata,
    Column('id', UUID, primary_key=True),
    Column('agent_id', UUID, nullable=False),
    Column('activity_type', String(50), nullable=False),
    Column('created_at', DateTime(timezone=True), nullable=False),
    Column('details', JSONB),
    postgresql_partition_by='RANGE (created_at)'
)

# Migration to create partitioned table and initial partitions
def upgrade():
    # Create the partitioned table
    agent_activity.create(engine)
    
    # Create partitions (requires raw SQL)
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE agent_activity_y2025m04 PARTITION OF agent_activity
            FOR VALUES FROM ('2025-04-01') TO ('2025-05-01')
        """))
        
        conn.execute(text("""
        CREATE TABLE agent_activity_y2025m05 PARTITION OF agent_activity
            FOR VALUES FROM ('2025-05-01') TO ('2025-06-01')
        """))
        
        # Add indexes
        conn.execute(text("CREATE INDEX idx_agent_activity_agent_id ON agent_activity(agent_id)"))
        conn.execute(text("CREATE INDEX idx_agent_activity_type ON agent_activity(activity_type)"))
        conn.execute(text("CREATE INDEX idx_agent_activity_created_at ON agent_activity(created_at)"))
```

#### Connection Optimization

Configure database connection parameters for optimal performance:

```python
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

# Configure database connection parameters
db_params = {
    'drivername': 'postgresql+asyncpg',
    'username': 'postgres',
    'password': '******',
    'host': 'postgres.berrys-production.svc.cluster.local',
    'port': 5432,
    'database': 'berrys_agents',
    'query': {
        'prepared_statement_cache_size': '100',  # Cache size for prepared statements
        'statement_cache_size': '1000',          # Cache size for statements
        'pool_timeout': '30',                    # 30 seconds timeout for getting a connection
        'pool_recycle': '1800',                  # Recycle connections after 30 minutes
        'pool_pre_ping': 'true',                 # Verify connections before use
        'echo': 'false',                         # Disable SQL logging in production
        'max_overflow': '10',                    # Maximum number of overflow connections
        'pool_size': '5',                        # Base pool size
        'connect_timeout': '5'                   # Connection timeout in seconds
    }
}

# Create async engine with optimized parameters
engine = create_engine(URL.create(**db_params))
```

Configure PostgreSQL for production:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-config
  namespace: berrys-production
data:
  postgresql.conf: |
    # Memory settings
    shared_buffers = '1GB'
    work_mem = '32MB'
    maintenance_work_mem = '256MB'
    
    # WAL settings
    wal_level = logical
    min_wal_size = '1GB'
    max_wal_size = '4GB'
    
    # Connection settings
    max_connections = 100
    
    # Query optimization
    random_page_cost = 1.1      # Assumes SSD storage
    effective_cache_size = '3GB'
    
    # Autovacuum settings
    autovacuum = on
    autovacuum_max_workers = 3
    autovacuum_naptime = '1min'
    
    # Logging and statistics
    log_min_duration_statement = 1000   # Log queries taking longer than 1 second
    track_io_timing = on
    track_activities = on
    track_counts = on
```

## Service Resource Allocation

### Resource Profiling

Implement resource monitoring in all services:

```python
import psutil
import logging
from prometheus_client import Gauge

# Set up metrics
cpu_usage = Gauge('service_cpu_usage_percent', 'CPU usage in percent', ['service'])
memory_usage = Gauge('service_memory_usage_bytes', 'Memory usage in bytes', ['service'])
disk_usage = Gauge('service_disk_usage_bytes', 'Disk usage in bytes', ['service', 'path'])

# Configure service name
SERVICE_NAME = "agent-orchestrator"

# Function to collect resource metrics
def collect_resource_metrics():
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_usage.labels(service=SERVICE_NAME).set(cpu_percent)
    
    # Memory usage
    memory_info = psutil.Process().memory_info()
    memory_usage.labels(service=SERVICE_NAME).set(memory_info.rss)
    
    # Disk usage
    disk_info = psutil.disk_usage('/')
    disk_usage.labels(service=SERVICE_NAME, path='/').set(disk_info.used)
    
    # Log resource usage
    logging.info(f"Resource usage - CPU: {cpu_percent}%, Memory: {memory_info.rss / (1024 * 1024):.2f} MB")

# Set up periodic collection (e.g., using APScheduler)
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(collect_resource_metrics, 'interval', seconds=30)
scheduler.start()
```

### Resource Configuration

Configure optimal CPU and memory resources:

```yaml
# Example resource configurations for key services

# Agent Orchestrator
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-orchestrator
  namespace: berrys-production
spec:
  template:
    spec:
      containers:
      - name: agent-orchestrator
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1"
            memory: "1Gi"

# Model Orchestration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: model-orchestration
  namespace: berrys-production
spec:
  template:
    spec:
      containers:
      - name: model-orchestration
        resources:
          requests:
            cpu: "1"
            memory: "1Gi"
          limits:
            cpu: "2"
            memory: "2Gi"

# Web Dashboard
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-dashboard
  namespace: berrys-production
spec:
  template:
    spec:
      containers:
      - name: web-dashboard
        resources:
          requests:
            cpu: "300m"
            memory: "512Mi"
          limits:
            cpu: "800m"
            memory: "1Gi"

# API Gateway
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: berrys-production
spec:
  template:
    spec:
      containers:
      - name: api-gateway
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1"
            memory: "1Gi"
```

Optimize Python application settings:

```python
# Python memory optimization settings
import gc

# Set garbage collection thresholds (tuned for better GC frequency)
gc.set_threshold(700, 10, 5)  # Default is (700, 10, 10)

# Enable tracking of objects (only in debug mode)
# gc.set_debug(gc.DEBUG_STATS)

# Set environment variables for Python optimizations
import os
os.environ["PYTHONMALLOC"] = "malloc"  # Use system malloc
os.environ["PYTHONHASHSEED"] = "0"     # Fix hash seed for reproducibility
```

## Request Batching and Throttling

### API Request Batching

Implement batch endpoints for high-volume operations:

```python
from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# Single-item endpoint
@router.post("/projects/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    return await project_service.create_project(db, project)

# Batch endpoint for creating multiple projects
@router.post("/projects/batch/", response_model=List[ProjectResponse])
async def create_projects_batch(
    projects: List[ProjectCreate],
    db: AsyncSession = Depends(get_db)
):
    # Validate batch size
    if len(projects) > 100:
        raise HTTPException(
            status_code=400,
            detail="Batch size exceeds maximum limit of 100 items"
        )
    
    # Process batch
    results = []
    for project in projects:
        result = await project_service.create_project(db, project)
        results.append(result)
    
    return results
```

Implement asynchronous batch processing for long-running operations:

```python
import asyncio
from fastapi import APIRouter, BackgroundTasks, Depends
from typing import List
import uuid

router = APIRouter()

# In-memory storage for batch job status
# In production, use Redis or database
batch_jobs = {}

# Submit batch job
@router.post("/agents/batch/", response_model=BatchJobResponse)
async def create_agents_batch(
    agents: List[AgentCreate],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # Validate batch size
    if len(agents) > 50:
        raise HTTPException(
            status_code=400,
            detail="Batch size exceeds maximum limit of 50 items"
        )
    
    # Create job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    batch_jobs[job_id] = {
        "status": "pending",
        "total": len(agents),
        "completed": 0,
        "failed": 0,
        "results": []
    }
    
    # Add to background tasks
    background_tasks.add_task(
        process_agent_batch,
        job_id=job_id,
        agents=agents,
        db=db
    )
    
    return {"job_id": job_id, "status": "pending"}

# Process batch job
async def process_agent_batch(job_id: str, agents: List[AgentCreate], db: AsyncSession):
    batch_jobs[job_id]["status"] = "processing"
    
    for agent in agents:
        try:
            # Process with small delay to avoid overloading
            result = await agent_service.create_agent(db, agent)
            batch_jobs[job_id]["results"].append({
                "id": result.id,
                "status": "success",
                "data": result
            })
            batch_jobs[job_id]["completed"] += 1
            
            # Small delay between operations
            await asyncio.sleep(0.1)
        except Exception as e:
            batch_jobs[job_id]["results"].append({
                "id": None,
                "status": "error",
                "error": str(e)
            })
            batch_jobs[job_id]["failed"] += 1
    
    batch_jobs[job_id]["status"] = "completed"

# Get batch job status
@router.get("/batch/{job_id}", response_model=BatchJobStatus)
async def get_batch_job_status(job_id: str):
    if job_id not in batch_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Batch job with ID {job_id} not found"
        )
    
    return batch_jobs[job_id]
```

### Rate Limiting

Implement rate limiting for APIs:

```python
from fastapi import FastAPI, Request, Response, HTTPException, Depends
import time
import redis
import hashlib

# Initialize Redis client
redis_client = redis.Redis(
    host='redis.berrys-production.svc.cluster.local',
    port=6379,
    db=2,  # Separate DB for rate limiting
    socket_timeout=5
)

# Rate limit configuration
rate_limits = {
    "default": {"requests": 100, "window": 60},  # 100 requests per minute
    "model_call": {"requests": 10, "window": 60},  # 10 requests per minute for expensive endpoints
    "critical": {"requests": 300, "window": 60},  # 300 requests per minute for critical endpoints
}

# Function to get rate limit key
def get_rate_limit_key(request: Request, limit_type: str) -> str:
    # Get client IP
    client_ip = request.client.host
    
    # Get endpoint path
    path = request.url.path
    
    # Create rate limit key
    key = f"ratelimit:{limit_type}:{client_ip}:{path}"
    
    return key

# Rate limit middleware
async def rate_limit_middleware(request: Request, call_next, limit_type: str = "default"):
    # Get rate limit configuration
    limit_config = rate_limits.get(limit_type, rate_limits["default"])
    max_requests = limit_config["requests"]
    window = limit_config["window"]
    
    # Generate rate limit key
    key = get_rate_limit_key(request, limit_type)
    
    # Get current timestamp
    now = int(time.time())
    window_start = now - window
    
    # Add current request to sliding window
    pipeline = redis_client.pipeline()
    pipeline.zadd(key, {str(now): now})
    pipeline.zremrangebyscore(key, 0, window_start)
    pipeline.zcard(key)
    pipeline.expire(key, window + 10)  # Add 10 seconds buffer
    _, _, request_count, _ = pipeline.execute()
    
    # Check if rate limit exceeded
    if request_count > max_requests:
        # Calculate reset time
        oldest_request = float(redis_client.zrange(key, 0, 0, withscores=True)[0][1])
        reset_time = int(oldest_request + window - now)
        
        # Return rate limit exceeded response
        headers = {
            "X-RateLimit-Limit": str(max_requests),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_time),
            "Retry-After": str(reset_time)
        }
        return Response(
            content={"detail": "Rate limit exceeded"},
            status_code=429,
            headers=headers
        )
    
    # Add rate limit headers
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(max_requests)
    response.headers["X-RateLimit-Remaining"] = str(max_requests - request_count)
    
    return response

# Create rate limit dependency for specific limit types
def rate_limit(limit_type: str = "default"):
    async def rate_limit_dependency(request: Request):
        # Apply rate limiting
        result = await rate_limit_middleware(request, lambda r: r, limit_type)
        
        # If response is returned (rate limit exceeded), raise exception
        if isinstance(result, Response):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        return True
    
    return Depends(rate_limit_dependency)

# Example usage in an API route
@app.get("/api/v1/models/invoke", dependencies=[rate_limit("model_call")])
async def invoke_model(
