# Service Boundary Adapter Usage Examples

This document provides examples of how to use the service boundary adapters in your services. These adapters facilitate the conversion of entities between different service representations, ensuring consistent data flow across service boundaries.

## Available Adapters

The following adapters are available in the `shared/models/src/adapters` package:

1. **WebToCoordinatorAdapter**: Converts between Web Dashboard and Project Coordinator representations
2. **CoordinatorToAgentAdapter**: Converts between Project Coordinator and Agent Orchestrator representations
3. **AgentToModelAdapter**: Converts between Agent Orchestrator and Model Orchestration representations

## Basic Usage

### Converting a Project

```python
from shared.models.src.adapters import (
    WebToCoordinatorAdapter,
    CoordinatorToAgentAdapter,
    AgentToModelAdapter
)

# Web Dashboard → Project Coordinator
web_project = {
    "id": project_id,
    "name": "My Project",
    "description": "A sample project",
    "status": "draft",
    "owner_id": owner_id,
    "metadata": {"key": "value"}
}
coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(web_project)

# Project Coordinator → Agent Orchestrator
agent_project = CoordinatorToAgentAdapter.project_to_agent(coordinator_project)

# Agent Orchestrator → Model Orchestration
model_project = AgentToModelAdapter.project_to_model(agent_project)
```

### Converting an Agent

```python
# Web Dashboard → Project Coordinator
web_agent = {
    "id": agent_id,
    "name": "My Agent",
    "type": "developer",
    "status": "active",
    "project_id": project_id,
    "metadata": {"key": "value"}
}
coordinator_agent = WebToCoordinatorAdapter.agent_to_coordinator(web_agent)

# Project Coordinator → Agent Orchestrator
agent_orchestrator_agent = CoordinatorToAgentAdapter.agent_to_agent_orchestrator(coordinator_agent)

# Agent Orchestrator → Model Orchestration
model_agent = AgentToModelAdapter.agent_to_model(agent_orchestrator_agent)

# The model_agent now includes:
# - agent_id: The agent's ID
# - name: The agent's name
# - type: "DEVELOPER"
# - status: "ACTIVE"
# - project_id: The project ID
# - capabilities: ["CHAT", "COMPLETION"]
# - settings: {
#     "key": "value",
#     "capability_config": {
#         "chat": {
#             "max_tokens": 4000,
#             "temperature": 0.7,
#             "top_p": 0.95
#         },
#         "completion": {
#             "max_tokens": 2000,
#             "temperature": 0.5,
#             "top_p": 0.9
#         }
#     }
# }
```

### Working with Agent Capabilities

The `AgentToModelAdapter` now automatically maps agent types to appropriate capabilities and adds detailed capability configuration:

```python
from shared.models.src.enums import AgentType, ModelCapability
from shared.models.src.adapters import AgentToModelAdapter

# Create a designer agent
designer_agent = {
    "id": agent_id,
    "name": "Design Assistant",
    "agent_type": AgentType.DESIGNER,
    "status": "active",
    "project_id": project_id,
    "config": {"theme": "modern", "style_preference": "minimalist"}
}

# Convert to Model Orchestration representation
model_agent = AgentToModelAdapter.agent_to_model(designer_agent)

# The model_agent now includes:
# - capabilities: ["IMAGE_GENERATION"]
# - settings: {
#     "theme": "modern", 
#     "style_preference": "minimalist",
#     "capability_config": {
#         "image_generation": {
#             "size": "1024x1024",
#             "quality": "standard",
#             "style": "natural"
#         }
#     }
# }

# Create a researcher agent
researcher_agent = {
    "id": agent_id,
    "name": "Research Assistant",
    "agent_type": AgentType.RESEARCHER,
    "status": "active",
    "project_id": project_id,
    "config": {"research_depth": "comprehensive"}
}

# Convert to Model Orchestration representation
model_agent = AgentToModelAdapter.agent_to_model(researcher_agent)

# The model_agent now includes:
# - capabilities: ["CHAT", "COMPLETION", "EMBEDDING"]
# - settings: {
#     "research_depth": "comprehensive",
#     "capability_config": {
#         "chat": { ... },
#         "completion": { ... },
#         "embedding": {
#             "dimensions": 1536,
#             "model": "text-embedding-3-large"
#         }
#     }
# }
```

### Converting a Task

```python
# Web Dashboard → Project Coordinator
web_task = {
    "id": task_id,
    "name": "My Task",
    "description": "A sample task",
    "status": "pending",
    "priority": 3,
    "assigned_to": agent_id,
    "project_id": project_id,
    "metadata": {"key": "value"}
}
coordinator_task = WebToCoordinatorAdapter.task_to_coordinator(web_task)

# Project Coordinator → Agent Orchestrator
agent_task = CoordinatorToAgentAdapter.task_to_agent(coordinator_task)
```

## Working with Pydantic Models

The adapters also support Pydantic models as input:

```python
from shared.models.src.project import Project
from shared.models.src.agent import Agent
from shared.models.src.task import Task

# Create a Pydantic model
project_model = Project(
    id=project_id,
    name="My Project",
    description="A sample project",
    status=ProjectStatus.DRAFT,
    owner_id=owner_id,
    metadata={"key": "value"}
)

# Convert to Project Coordinator representation
coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(project_model)
```

## Enhanced Error Handling

The adapters provide detailed error messages and specific exception types, now with improved error handling based on our standardized error handling best practices:

```python
from shared.models.src.adapters.exceptions import AdapterValidationError, EntityConversionError
from shared.models.src.api.errors import ErrorResponse
import logging

logger = logging.getLogger(__name__)

def convert_project_with_error_handling(web_project, request_id):
    try:
        coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(web_project)
        return coordinator_project, None
    except AdapterValidationError as e:
        # Log with structured context
        logger.error("Project validation error during conversion", extra={
            "request_id": request_id,
            "service": "web-dashboard",
            "operation": "convert_project",
            "error_code": "PROJECT_VALIDATION_ERROR",
            "source_data": str(e.source_data),
            "exception": str(e)
        })
        
        # Create standardized error response
        error = ErrorResponse(
            code="PROJECT_VALIDATION_ERROR",
            message="Invalid project data",
            details={"validation_error": str(e), "field": e.field_name} if hasattr(e, 'field_name') else {"error": str(e)},
            request_id=request_id,
            timestamp=datetime.utcnow()
        )
        return None, error
    except EntityConversionError as e:
        # Log with structured context
        logger.error("Project conversion error", extra={
            "request_id": request_id,
            "service": "web-dashboard",
            "operation": "convert_project",
            "error_code": "PROJECT_CONVERSION_ERROR",
            "source_entity": str(e.source_entity),
            "error_details": str(e.error_details),
            "exception": str(e)
        })
        
        # Create standardized error response
        error = ErrorResponse(
            code="PROJECT_CONVERSION_ERROR",
            message="Failed to convert project data",
            details={"conversion_error": str(e), "details": e.error_details},
            request_id=request_id,
            timestamp=datetime.utcnow()
        )
        return None, error
```

## Retry Mechanisms

When working with adapters in cross-service communication, implement retry mechanisms for transient failures:

```python
import asyncio
import random
from shared.models.src.adapters.exceptions import TransientAdapterError

async def convert_project_with_retry(web_project, max_retries=3, base_delay=0.5):
    """Convert a project with retry for transient errors."""
    retries = 0
    while True:
        try:
            return WebToCoordinatorAdapter.project_to_coordinator(web_project)
        except TransientAdapterError as e:
            if retries >= max_retries:
                logger.error(f"Failed to convert project after {max_retries} retries", extra={
                    "project_id": web_project.get("id"),
                    "error": str(e)
                })
                raise
                
            delay = base_delay * (2 ** retries)
            jitter = random.uniform(0, 0.1 * delay)
            total_delay = delay + jitter
            
            logger.warning(f"Transient error during project conversion, retrying in {total_delay:.2f}s", extra={
                "project_id": web_project.get("id"),
                "retry_count": retries + 1,
                "delay": total_delay,
                "error": str(e)
            })
            
            await asyncio.sleep(total_delay)
            retries += 1
```

## Fallback Mechanisms

Implement fallback mechanisms for when services are unavailable:

```python
from shared.models.src.adapters.exceptions import ServiceUnavailableError
import redis

# Initialize Redis client for caching
redis_client = redis.Redis(host='localhost', port=6379, db=0)

async def get_project_with_fallback(project_id, request_id):
    """Get a project with fallback to cache if service is unavailable."""
    try:
        # Try to get fresh data from the service
        project = await project_coordinator_client.get_project(project_id)
        
        # Convert to agent representation
        agent_project = CoordinatorToAgentAdapter.project_to_agent(project)
        
        # Cache the result for fallback
        cache_key = f"project:{project_id}"
        redis_client.setex(cache_key, 3600, json.dumps(agent_project))
        
        return agent_project, None
    except ServiceUnavailableError as e:
        logger.warning("Project Coordinator service unavailable, using cached data", extra={
            "request_id": request_id,
            "project_id": project_id,
            "error": str(e)
        })
        
        # Try to get from cache
        cache_key = f"project:{project_id}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            logger.info("Using cached project data", extra={
                "request_id": request_id,
                "project_id": project_id,
                "cache_age": redis_client.ttl(cache_key)
            })
            return json.loads(cached_data), None
        
        # No cached data available
        error = ErrorResponse(
            code="PROJECT_SERVICE_UNAVAILABLE",
            message="Project service is unavailable and no cached data exists",
            details={"project_id": str(project_id)},
            request_id=request_id,
            timestamp=datetime.utcnow()
        )
        return None, error
```

## Circuit Breaker Pattern

Use the circuit breaker pattern to prevent cascading failures when using adapters:

```python
from shared.utils.src.circuit_breaker import CircuitBreaker

# Create circuit breakers for each service
project_coordinator_cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
agent_orchestrator_cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30)

async def convert_project_with_circuit_breaker(web_project):
    """Convert a project using circuit breaker pattern."""
    async def operation():
        coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(web_project)
        return coordinator_project
    
    try:
        return await project_coordinator_cb.execute(operation)
    except CircuitBreakerOpenException:
        logger.warning("Circuit breaker open for Project Coordinator service", extra={
            "project_id": web_project.get("id")
        })
        raise ServiceUnavailableError("Project Coordinator service is unavailable")
```

## Request Validation

Implement comprehensive validation before using adapters:

```python
from pydantic import BaseModel, validator, ValidationError
from typing import Optional, Dict, Any
from uuid import UUID
from shared.models.src.enums import ProjectStatus

class ProjectCreateRequest(BaseModel):
    """Validated request model for creating a project."""
    name: str
    description: Optional[str] = None
    status: Optional[ProjectStatus] = ProjectStatus.DRAFT
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('name')
    def name_must_be_valid(cls, v):
        if len(v) < 3:
            raise ValueError('Project name must be at least 3 characters')
        if len(v) > 100:
            raise ValueError('Project name must be at most 100 characters')
        return v
    
    @validator('description')
    def description_must_be_valid(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError('Description must be at most 1000 characters')
        return v

def validate_and_convert_project(request_data, request_id):
    """Validate request data and convert to coordinator format."""
    try:
        # Validate using Pydantic model
        validated_data = ProjectCreateRequest(**request_data)
        
        # Convert to dictionary for adapter
        project_dict = validated_data.dict(exclude_none=True)
        
        # Convert to coordinator format
        coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(project_dict)
        return coordinator_project, None
    except ValidationError as e:
        # Create standardized error response
        error = ErrorResponse(
            code="PROJECT_VALIDATION_ERROR",
            message="Project validation failed",
            details={"validation_errors": e.errors()},
            request_id=request_id,
            timestamp=datetime.utcnow()
        )
        return None, error
```

## Integration with Services

### Web Dashboard Service with Enhanced Error Handling

```python
from shared.models.src.adapters import WebToCoordinatorAdapter
from shared.utils.src.circuit_breaker import CircuitBreaker

class ProjectService:
    def __init__(self):
        self.project_coordinator_cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
        
    async def create_project(self, web_project, request_id):
        # Validate and convert to Project Coordinator representation
        coordinator_project, error = validate_and_convert_project(web_project, request_id)
        if error:
            return None, error
        
        try:
            # Use circuit breaker for service call
            async def operation():
                return await self.project_coordinator_client.create_project(coordinator_project)
            
            response = await self.project_coordinator_cb.execute(operation)
            
            # Convert response back to Web Dashboard representation
            web_response = WebToCoordinatorAdapter.project_from_coordinator(response)
            return web_response, None
        except CircuitBreakerOpenException:
            logger.warning("Circuit breaker open for Project Coordinator service", extra={
                "request_id": request_id
            })
            return None, ErrorResponse(
                code="PROJECT_SERVICE_UNAVAILABLE",
                message="Project service is temporarily unavailable",
                request_id=request_id,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error("Error creating project", extra={
                "request_id": request_id,
                "error": str(e)
            })
            return None, ErrorResponse(
                code="PROJECT_CREATION_ERROR",
                message="Failed to create project",
                details={"error": str(e)},
                request_id=request_id,
                timestamp=datetime.utcnow()
            )
```

### Project Coordinator Service

```python
from shared.models.src.adapters import WebToCoordinatorAdapter, CoordinatorToAgentAdapter

class ProjectService:
    def create_project(self, coordinator_project):
        # Save to database
        db_project = self.project_repository.create(coordinator_project)
        
        # Convert to Agent Orchestrator representation
        agent_project = CoordinatorToAgentAdapter.project_to_agent(db_project)
        
        # Send to Agent Orchestrator service
        self.agent_orchestrator_client.create_project(agent_project)
        
        return db_project
    
    def handle_web_request(self, web_project):
        # Convert from Web Dashboard representation
        coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(web_project)
        
        # Process the project
        result = self.create_project(coordinator_project)
        
        # Convert back to Web Dashboard representation
        return WebToCoordinatorAdapter.project_from_coordinator(result)
```

### Agent Orchestrator Service

```python
from shared.models.src.adapters import CoordinatorToAgentAdapter, AgentToModelAdapter

class ProjectService:
    def create_project(self, agent_project):
        # Save to database
        db_project = self.project_repository.create(agent_project)
        
        # Convert to Model Orchestration representation
        model_project = AgentToModelAdapter.project_to_model(db_project)
        
        # Send to Model Orchestration service
        self.model_orchestration_client.create_project(model_project)
        
        return db_project
    
    def handle_coordinator_request(self, coordinator_project):
        # Convert from Project Coordinator representation
        agent_project = CoordinatorToAgentAdapter.project_to_agent(coordinator_project)
        
        # Process the project
        result = self.create_project(agent_project)
        
        # Convert back to Project Coordinator representation
        return CoordinatorToAgentAdapter.project_from_agent(result)
```

## Best Practices

1. **Validate Input**: Always validate input before passing it to the adapters
2. **Handle Errors**: Catch and handle adapter exceptions appropriately
3. **Log Transformations**: Log adapter transformations for debugging
4. **Use Consistent Types**: Use consistent types for entity IDs (UUID)
5. **Preserve Metadata**: Ensure metadata is preserved across transformations
6. **Test Conversions**: Write tests for your adapter usage
7. **Implement Retries**: Use retry mechanisms for transient failures
8. **Use Circuit Breakers**: Implement circuit breakers to prevent cascading failures
9. **Provide Fallbacks**: Add fallback mechanisms for service unavailability
10. **Standardize Error Responses**: Use consistent error response formats
11. **Include Request IDs**: Pass request IDs through all service calls for tracing
12. **Add Comprehensive Validation**: Validate all input at service boundaries

## Common Pitfalls

1. **Missing Fields**: Ensure all required fields are present in the input
2. **Enum Handling**: Be aware of enum handling differences between services
3. **ID Field Names**: Pay attention to ID field name differences
4. **Metadata Fields**: Ensure metadata fields are properly handled
5. **None Values**: Handle None values explicitly
6. **Transient Failures**: Distinguish between transient and permanent failures
7. **Timeout Configuration**: Set appropriate timeouts for service calls
8. **Retry Limits**: Configure reasonable retry limits to avoid overwhelming services
9. **Cache Invalidation**: Implement proper cache invalidation strategies for fallbacks
10. **Error Propagation**: Be careful about how errors are propagated across services

## Conclusion

The service boundary adapters provide a consistent way to convert entities between different service representations. By using these adapters with enhanced error handling, retry mechanisms, fallback strategies, and comprehensive validation, you can ensure that data flows correctly and reliably across service boundaries, even in the presence of failures.

## Related Documentation

- [Cross-Service Communication Improvements](./cross-service-communication-improvements.md) - Comprehensive plan for improving cross-service communication
- [Error Handling Best Practices](./error-handling-best-practices.md) - Best practices for error handling across services
- [Entity Representation Alignment](./entity-representation-alignment.md) - Documentation of entity differences and adapters
- [Model Standardization Progress](./model-standardization-progress.md) - Overall progress on model standardization
- [Model Mapping System](./model-mapping-system.md) - Comprehensive overview of the model mapping system
- [Troubleshooting Guide](./troubleshooting-guide.md) - Guide for troubleshooting cross-service issues
