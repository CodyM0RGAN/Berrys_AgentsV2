# Service Development Guide

**Last Modified:** 2025-03-29  
**Completion Date:** 2025-03-29  
**Doc Type:** Guide  

---

## Overview

This guide provides comprehensive information on developing services for the Berrys_AgentsV2 platform. It covers service structure, design patterns, communication mechanisms, and integration best practices.

## Service Structure

Each service in Berrys_AgentsV2 follows a standardized structure to ensure consistency and maintainability:

```
service-name/
├── alembic.ini              # Database migration configuration
├── Dockerfile               # Container definition
├── README.md                # Service-specific documentation
├── requirements.txt         # Python dependencies
├── run_tests.sh             # Test runner script
├── logs/                    # Log directory
├── migrations/              # Database migrations
│   └── versions/            # Migration version scripts
├── src/                     # Source code
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── dependencies.py      # Service dependencies
│   ├── exceptions.py        # Custom exceptions
│   ├── main.py              # Application entry point
│   ├── messaging/           # Message handling
│   │   ├── __init__.py
│   │   ├── handlers.py      # Message handlers
│   │   ├── producer.py      # Message producers
│   │   └── schemas.py       # Message schemas
│   ├── models/              # Data models
│   │   ├── __init__.py
│   │   ├── domain.py        # Domain models
│   │   ├── entities.py      # Database entities
│   │   └── schemas.py       # API schemas
│   ├── routers/             # API routes
│   │   ├── __init__.py
│   │   └── v1/              # API version
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   └── core_service.py  # Main service logic
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── common.py        # Common utilities
└── tests/                   # Tests
    ├── __init__.py
    ├── conftest.py          # Test configuration
    ├── integration/         # Integration tests
    └── unit/                # Unit tests
```

### Key Components

1. **Configuration Management**
   - Environment-based configuration using Pydantic settings
   - Secure handling of credentials and secrets
   - Environment variable validation and defaults

2. **API Endpoints**
   - FastAPI-based REST endpoints
   - OpenAPI documentation
   - Versioned API routes

3. **Data Models**
   - Domain models for business logic
   - SQLAlchemy ORM entities for database interaction
   - Pydantic schemas for API validation

4. **Messaging**
   - Redis-based message handling
   - Event production and consumption
   - Message schema validation

5. **Services**
   - Core business logic implementation
   - Service layer pattern for separation of concerns
   - Integration with other system components

## Design Patterns

The Berrys_AgentsV2 platform employs several design patterns to ensure maintainability, extensibility, and scalability:

### Repository Pattern

Used for database interactions to abstract data access:

```python
class AgentRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        
    def get_by_id(self, agent_id: UUID) -> Agent:
        return self.db_session.query(Agent).filter(Agent.id == agent_id).first()
        
    def create(self, agent: Agent) -> Agent:
        self.db_session.add(agent)
        self.db_session.flush()
        return agent
        
    def update(self, agent: Agent) -> Agent:
        self.db_session.merge(agent)
        self.db_session.flush()
        return agent
```

### Factory Pattern

Used for creating objects with complex initialization:

```python
class AgentFactory:
    def __init__(self, template_service, specialization_service):
        self.template_service = template_service
        self.specialization_service = specialization_service
        
    def create_agent(self, agent_type: str, context: dict) -> Agent:
        template = self.template_service.get_template(agent_type)
        agent = Agent(template=template)
        specializations = self.specialization_service.get_specializations(context)
        agent.apply_specializations(specializations)
        return agent
```

### Adapter Pattern

Used for interfacing between services with different data models:

```python
class PlanningToAgentAdapter:
    @classmethod
    def task_to_agent_task(cls, planning_task) -> AgentTask:
        return AgentTask(
            id=planning_task.id,
            title=planning_task.name,
            description=planning_task.description,
            priority=cls._map_priority(planning_task.priority),
            deadline=planning_task.due_date,
            status=cls._map_status(planning_task.status)
        )
        
    @classmethod
    def _map_priority(cls, planning_priority: str) -> str:
        priority_map = {
            "HIGH": "critical",
            "MEDIUM": "normal",
            "LOW": "low"
        }
        return priority_map.get(planning_priority, "normal")
```

### Strategy Pattern

Used for implementing different algorithms or approaches based on context:

```python
class MessageRoutingStrategy(ABC):
    @abstractmethod
    def route_message(self, message: Message) -> List[Agent]:
        pass

class DirectRoutingStrategy(MessageRoutingStrategy):
    def route_message(self, message: Message) -> List[Agent]:
        return [message.recipient]
        
class TopicRoutingStrategy(MessageRoutingStrategy):
    def __init__(self, subscription_service):
        self.subscription_service = subscription_service
        
    def route_message(self, message: Message) -> List[Agent]:
        return self.subscription_service.get_subscribers(message.topic)
```

### Service Locator Pattern

Used for dependency injection and service discovery:

```python
class ServiceLocator:
    _services = {}
    
    @classmethod
    def register(cls, service_name: str, service_instance):
        cls._services[service_name] = service_instance
        
    @classmethod
    def get(cls, service_name: str):
        return cls._services.get(service_name)
```

## Inter-Service Communication

Services in Berrys_AgentsV2 communicate through both synchronous and asynchronous mechanisms:

### Synchronous Communication (REST)

Services expose REST APIs for synchronous communication:

```python
@router.get("/agents/{agent_id}", response_model=AgentSchema)
async def get_agent(agent_id: UUID, agent_service: AgentService = Depends(get_agent_service)):
    agent = await agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
```

Clients use HTTP clients to interact with these APIs:

```python
async def get_agent(agent_id: UUID) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.AGENT_ORCHESTRATOR_URL}/agents/{agent_id}")
        response.raise_for_status()
        return response.json()
```

### Asynchronous Communication (Redis)

For asynchronous communication, services use Redis pub/sub:

Message producer:
```python
class MessageProducer:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        
    async def publish(self, channel: str, message: dict):
        await self.redis_client.publish(channel, json.dumps(message))
```

Message consumer:
```python
class MessageConsumer:
    def __init__(self, redis_client, message_handler):
        self.redis_client = redis_client
        self.message_handler = message_handler
        
    async def start(self, channels: List[str]):
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(*channels)
        
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                await self.message_handler.handle(message["channel"], json.loads(message["data"]))
```

## Database Interaction

Services interact with the PostgreSQL database using SQLAlchemy:

### Entity Definition

```python
class Agent(Base):
    __tablename__ = "agent"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    state = Column(String, nullable=False)
    state_detail = Column(JSONB)
    template_id = Column(UUID, ForeignKey("agent_template.id"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active_at = Column(DateTime)
    
    tasks = relationship("AgentTask", back_populates="agent")
    specializations = relationship("AgentSpecialization", back_populates="agent")
```

### Database Session Management

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(settings.DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Database Migrations

Database schema migrations are managed using Alembic:

```bash
# Generate a new migration
alembic revision --autogenerate -m "Add agent state history table"

# Apply migrations
alembic upgrade head

# Rollback a migration
alembic downgrade -1
```

## Error Handling

Comprehensive error handling is essential for building robust services:

### Custom Exceptions

```python
class ServiceException(Exception):
    """Base exception for service errors"""
    
class ResourceNotFoundException(ServiceException):
    """Raised when a requested resource is not found"""
    
class ValidationException(ServiceException):
    """Raised when validation fails"""
    
class IntegrationException(ServiceException):
    """Raised when an integration with another service fails"""
```

### Exception Handling Middleware

```python
@app.exception_handler(ServiceException)
async def service_exception_handler(request: Request, exc: ServiceException):
    if isinstance(exc, ResourceNotFoundException):
        return JSONResponse(
            status_code=404,
            content={"message": str(exc)}
        )
    elif isinstance(exc, ValidationException):
        return JSONResponse(
            status_code=400,
            content={"message": str(exc)}
        )
    elif isinstance(exc, IntegrationException):
        return JSONResponse(
            status_code=502,
            content={"message": str(exc)}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"}
        )
```

### Error Logging

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = operation_that_might_fail()
except Exception as e:
    logger.error(f"Operation failed: {str(e)}", exc_info=True)
    raise ServiceException(f"Operation failed: {str(e)}")
```

## Testing Strategies

Comprehensive testing ensures service reliability and correctness:

### Unit Testing

```python
def test_agent_creation():
    # Arrange
    template_service = MagicMock()
    specialization_service = MagicMock()
    template_service.get_template.return_value = MockTemplate()
    specialization_service.get_specializations.return_value = [MockSpecialization()]
    
    factory = AgentFactory(template_service, specialization_service)
    
    # Act
    agent = factory.create_agent("assistant", {"domain": "customer_support"})
    
    # Assert
    assert agent.template is not None
    assert len(agent.specializations) == 1
    assert template_service.get_template.called_with("assistant")
    assert specialization_service.get_specializations.called_with({"domain": "customer_support"})
```

### Integration Testing

```python
async def test_agent_api_integration():
    # Arrange
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        # Act
        response = await client.post("/agents", json={
            "name": "Test Agent",
            "template_id": "550e8400-e29b-41d4-a716-446655440000",
            "specializations": ["customer_support", "technical"]
        })
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Agent"
        assert data["state"] == "initializing"
        
        # Verify in database
        async with async_session() as session:
            agent = await session.query(Agent).filter(Agent.id == data["id"]).first()
            assert agent is not None
            assert agent.name == "Test Agent"
```

### End-to-End Testing

```python
async def test_agent_task_workflow():
    # Arrange - Create agent and task
    agent_id = await create_test_agent()
    task_id = await create_test_task()
    
    # Act - Assign task to agent
    await assign_task_to_agent(task_id, agent_id)
    
    # Assert - Verify task assignment
    agent_task = await get_agent_task(agent_id, task_id)
    assert agent_task is not None
    assert agent_task["status"] == "assigned"
    
    # Act - Complete task
    await complete_agent_task(agent_id, task_id, {"result": "success"})
    
    # Assert - Verify task completion
    agent_task = await get_agent_task(agent_id, task_id)
    assert agent_task["status"] == "completed"
    assert agent_task["result"]["result"] == "success"
```

## Monitoring and Logging

Effective monitoring and logging are essential for operational visibility:

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

logger.info("Agent created", agent_id=str(agent.id), template_id=str(agent.template_id))
logger.error("Task execution failed", agent_id=str(agent_id), task_id=str(task_id), error=str(e))
```

### Health Checks

```python
@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Check database connection
        result = await db.execute("SELECT 1")
        assert result.scalar() == 1
        
        # Check Redis connection
        await redis_client.ping()
        
        # Check dependent services
        await check_dependent_services()
        
        return {"status": "healthy"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": str(e)}
        )
```

### Metrics Collection

```python
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP Requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP Request Latency", ["method", "endpoint"])

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration)
    
    return response
```

## Integration Best Practices

When integrating with other services, follow these best practices:

### Resilient Connections

```python
import backoff

@backoff.on_exception(
    backoff.expo,
    (httpx.RequestError, httpx.HTTPStatusError),
    max_tries=5,
    max_time=30
)
async def get_agent_with_retry(agent_id: UUID) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.AGENT_ORCHESTRATOR_URL}/agents/{agent_id}")
        response.raise_for_status()
        return response.json()
```

### Circuit Breaker Pattern

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=30, expected_exception=httpx.HTTPError)
async def get_model_status(model_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.MODEL_ORCHESTRATION_URL}/models/{model_id}/status")
        response.raise_for_status()
        return response.json()
```

### Service Discovery

```python
class ServiceRegistry:
    def __init__(self, config):
        self.services = {}
        self.load_services(config)
        
    def load_services(self, config):
        for service_name, service_config in config.items():
            self.services[service_name] = service_config
            
    def get_service_url(self, service_name: str) -> str:
        service = self.services.get(service_name)
        if not service:
            raise ValueError(f"Service {service_name} not found in registry")
        return service["url"]
```

## Deployment Considerations

When developing services, consider these deployment aspects:

### Containerization

Each service is containerized using Docker:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Configuration

Services should be configurable through environment variables:

```python
from pydantic import BaseSettings, PostgresDsn, RedisDsn

class Settings(BaseSettings):
    APP_NAME: str = "agent-orchestrator"
    APP_VERSION: str = "0.1.0"
    
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn
    
    MODEL_ORCHESTRATION_URL: str
    TOOL_INTEGRATION_URL: str
    PLANNING_SYSTEM_URL: str
    
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### Health Monitoring

Services should expose health check endpoints:

- `/health/liveness`: Indicates if the service is running
- `/health/readiness`: Indicates if the service is ready to handle requests
- `/metrics`: Exposes Prometheus metrics

## References

- [Agent Orchestrator Service](../../reference/services/agent-orchestrator.md) - Example service implementation
- [Database Schema Reference](../../reference/database-schema.md) - Database schema details
- [Message Contracts Reference](../../reference/message-contracts.md) - Message format specifications
- [Service Template](../../reference/service-template.md) - Template for new services
- [Entity Representation Alignment](../developer-guides/service-development/entity-representation-alignment.md) - Guide for cross-service data mapping
