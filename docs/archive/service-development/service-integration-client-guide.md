# Service Integration Client Guide

> **Draft-of-Thought Documentation**: This document provides guidance on using the Service Integration Client to interact with the Service Integration service. It covers client initialization, available methods, error handling, and best practices.

## Overview

The Service Integration Client provides a standardized way to interact with the Service Integration service. It handles communication details, error handling, and includes retry mechanisms with exponential backoff to handle transient failures.

The client is implemented in `shared/utils/src/clients/service_integration.py` and can be imported from the shared package:

```python
from shared.utils.src.clients import ServiceIntegrationClient
```

## Client Initialization

The client can be initialized with the base URL of the Service Integration service and an optional timeout value:

```python
# Initialize with default timeout
client = ServiceIntegrationClient(base_url="http://localhost:8005/api")

# Initialize with custom timeout
client = ServiceIntegrationClient(base_url="http://localhost:8005/api", timeout=30)
```

In the web dashboard, you can get a pre-configured client using the `get_service_integration_client` function:

```python
from app.api.clients import get_service_integration_client

client = get_service_integration_client()
```

## Available Methods

The Service Integration Client provides the following methods:

### Workflow Management

#### Create a Workflow

```python
workflow = await client.create_workflow(
    name="document-processing",
    description="Process documents through multiple services",
    steps=[
        {
            "id": "extract-text",
            "service": "text-extraction",
            "action": "extract",
            "next": "analyze-sentiment"
        },
        {
            "id": "analyze-sentiment",
            "service": "sentiment-analysis",
            "action": "analyze",
            "next": "generate-summary"
        },
        {
            "id": "generate-summary",
            "service": "text-summarization",
            "action": "summarize",
            "next": None
        }
    ],
    metadata={
        "version": "1.0.0",
        "author": "Berry's Agents Team"
    }
)
```

#### Update a Workflow

```python
updated_workflow = await client.update_workflow(
    workflow_id="123",
    name="document-processing-v2",
    description="Improved document processing workflow",
    steps=[
        {
            "id": "extract-text",
            "service": "text-extraction-v2",
            "action": "extract",
            "next": "analyze-sentiment"
        },
        {
            "id": "analyze-sentiment",
            "service": "sentiment-analysis",
            "action": "analyze",
            "next": "generate-summary"
        },
        {
            "id": "generate-summary",
            "service": "text-summarization",
            "action": "summarize",
            "next": "translate"
        },
        {
            "id": "translate",
            "service": "translation",
            "action": "translate",
            "next": None
        }
    ],
    status="ACTIVE"
)
```

#### Delete a Workflow

```python
result = await client.delete_workflow(workflow_id="123")
```

#### Get Workflow Details

```python
workflow = client.get_workflow(workflow_id="123")
```

#### List Workflows

```python
# Get all workflows
workflows = client.get_workflows()

# Filter by status
active_workflows = client.get_workflows(status="ACTIVE")

# Pagination
workflows_page_2 = client.get_workflows(page=2, per_page=10)
```

### Workflow Execution

#### Execute a Workflow

```python
result = await client.execute_workflow(
    workflow_id="123",
    input_data={
        "document_url": "https://example.com/document.pdf",
        "language": "en"
    },
    context={
        "project_id": "456",
        "request_id": "req-123"
    }
)
```

#### Get Workflow Execution Status

```python
status = client.get_workflow_execution_status(execution_id="789")
```

#### List Workflow Executions

```python
# Get all executions for a workflow
executions = client.get_workflow_executions(workflow_id="123")

# Filter by status
completed_executions = client.get_workflow_executions(
    workflow_id="123",
    status="COMPLETED"
)

# Pagination
executions_page_2 = client.get_workflow_executions(
    workflow_id="123",
    page=2,
    per_page=10
)
```

### Service Registration

#### Register a Service

```python
service = await client.register_service(
    name="text-extraction",
    description="Extract text from documents",
    endpoint="http://text-extraction-service:8000/api",
    actions=[
        {
            "name": "extract",
            "description": "Extract text from a document",
            "input_schema": {
                "type": "object",
                "properties": {
                    "document_url": {
                        "type": "string",
                        "format": "uri",
                        "description": "URL of the document to extract text from"
                    },
                    "language": {
                        "type": "string",
                        "description": "Language of the document"
                    }
                },
                "required": ["document_url"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Extracted text"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Metadata about the extraction"
                    }
                },
                "required": ["text"]
            }
        }
    ],
    metadata={
        "version": "1.0.0",
        "provider": "Berry's Agents Team"
    }
)
```

#### Update a Service

```python
updated_service = await client.update_service(
    service_id="456",
    name="text-extraction-v2",
    description="Improved text extraction service",
    endpoint="http://text-extraction-service-v2:8000/api",
    status="ACTIVE"
)
```

#### Deregister a Service

```python
result = await client.deregister_service(service_id="456")
```

#### Get Service Details

```python
service = client.get_service(service_id="456")
```

#### List Services

```python
# Get all services
services = client.get_services()

# Filter by status
active_services = client.get_services(status="ACTIVE")

# Pagination
services_page_2 = client.get_services(page=2, per_page=10)
```

### Service Action Execution

#### Execute a Service Action

```python
result = await client.execute_service_action(
    service_id="456",
    action="extract",
    input_data={
        "document_url": "https://example.com/document.pdf",
        "language": "en"
    },
    context={
        "project_id": "789",
        "request_id": "req-123"
    }
)
```

### Integration Monitoring

#### Get Integration Health

```python
health = client.get_integration_health()
```

#### Get Service Health

```python
service_health = client.get_service_health(service_id="456")
```

## Error Handling

The Service Integration Client includes built-in error handling with retry mechanisms for transient failures. However, you should still handle exceptions in your code:

```python
from shared.utils.src.exceptions import (
    ServiceUnavailableError,
    ResourceNotFoundError,
    ValidationError,
    MaxRetriesExceededError
)

try:
    workflow = await client.create_workflow(
        name="document-processing",
        description="Process documents through multiple services",
        steps=[...]
    )
except ValidationError as e:
    # Handle validation errors
    print(f"Validation error: {e.validation_errors}")
except ResourceNotFoundError as e:
    # Handle resource not found errors
    print(f"Resource not found: {e.resource_type} with ID {e.resource_id}")
except ServiceUnavailableError as e:
    # Handle service unavailability
    print(f"Service unavailable: {e.service_name}")
except MaxRetriesExceededError as e:
    # Handle maximum retries exceeded
    print(f"Failed after {e.attempts} attempts: {e.last_error}")
except Exception as e:
    # Handle other exceptions
    print(f"Unexpected error: {str(e)}")
```

## Retry Mechanisms

The Service Integration Client includes retry mechanisms with exponential backoff for handling transient failures. The retry policy is configured differently for different operation types:

- **Create operations**: 3 retries with base delay of 0.5 seconds and max delay of 4 seconds
- **Update operations**: 3 retries with base delay of 0.5 seconds and max delay of 4 seconds
- **Delete operations**: 2 retries with base delay of 1 second and max delay of 4 seconds
- **Read operations**: 2 retries with base delay of 0.5 seconds and max delay of 2 seconds

The retry mechanism automatically handles `ServiceUnavailableError` exceptions and will retry the operation with exponential backoff. If the operation still fails after the maximum number of retries, a `MaxRetriesExceededError` exception is raised.

## Circuit Breaker Pattern

The Service Integration Client also includes a circuit breaker pattern to prevent cascading failures when the Service Integration service is unavailable. The circuit breaker is implemented using the `CircuitBreaker` class from `shared/utils/src/circuit_breaker.py`.

When the circuit breaker is open, all requests to the Service Integration service will be rejected without attempting to call the service. This prevents overwhelming the service with requests when it's already struggling.

## Best Practices

### Use Async Methods

Most methods in the Service Integration Client are asynchronous and should be used with `await`:

```python
# Good
workflow = await client.create_workflow(...)

# Bad
workflow = client.create_workflow(...)  # This will return a coroutine, not the actual result
```

### Handle Exceptions

Always handle exceptions when calling methods on the Service Integration Client:

```python
# Good
try:
    workflow = await client.create_workflow(...)
except Exception as e:
    # Handle the exception
    print(f"Error: {str(e)}")

# Bad
workflow = await client.create_workflow(...)  # No exception handling
```

### Use Pagination for Large Result Sets

When retrieving large lists of workflows or services, use pagination to avoid performance issues:

```python
# Good
page = 1
per_page = 10
while True:
    workflows = client.get_workflows(page=page, per_page=per_page)
    if not workflows["items"]:
        break
    
    # Process workflows
    for workflow in workflows["items"]:
        process_workflow(workflow)
    
    page += 1

# Bad
all_workflows = client.get_workflows(per_page=1000)  # Retrieving too many items at once
```

### Use Context Information

When executing workflows or service actions, provide context information to help with debugging and tracing:

```python
# Good
result = await client.execute_workflow(
    workflow_id="123",
    input_data={...},
    context={
        "project_id": "456",
        "request_id": get_request_id()
    }
)

# Bad
result = await client.execute_workflow(
    workflow_id="123",
    input_data={...}
)
```

### Validate Workflow Steps

Before creating a workflow, validate that all referenced services and actions exist:

```python
# Good
services = client.get_services()
service_map = {service["name"]: service for service in services["items"]}

for step in workflow_steps:
    service_name = step["service"]
    action_name = step["action"]
    
    if service_name not in service_map:
        raise ValueError(f"Service '{service_name}' not found")
    
    service = service_map[service_name]
    action_exists = any(action["name"] == action_name for action in service["actions"])
    
    if not action_exists:
        raise ValueError(f"Action '{action_name}' not found in service '{service_name}'")

workflow = await client.create_workflow(
    name="document-processing",
    description="Process documents through multiple services",
    steps=workflow_steps
)

# Bad
workflow = await client.create_workflow(
    name="document-processing",
    description="Process documents through multiple services",
    steps=workflow_steps
)
```

## Example: Complete Workflow Creation and Execution

Here's a complete example of registering services, creating a workflow, and executing it:

```python
from shared.utils.src.clients import ServiceIntegrationClient
from shared.utils.src.exceptions import (
    ServiceUnavailableError,
    ResourceNotFoundError,
    ValidationError,
    MaxRetriesExceededError
)
from shared.utils.src.request_id import get_request_id

async def create_and_execute_document_workflow():
    client = ServiceIntegrationClient(base_url="http://localhost:8005/api")
    
    try:
        # Register text extraction service
        text_extraction = await client.register_service(
            name="text-extraction",
            description="Extract text from documents",
            endpoint="http://text-extraction-service:8000/api",
            actions=[
                {
                    "name": "extract",
                    "description": "Extract text from a document",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "document_url": {
                                "type": "string",
                                "format": "uri",
                                "description": "URL of the document to extract text from"
                            }
                        },
                        "required": ["document_url"]
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Extracted text"
                            }
                        },
                        "required": ["text"]
                    }
                }
            ]
        )
        
        print(f"Registered text extraction service with ID: {text_extraction['id']}")
        
        # Register sentiment analysis service
        sentiment_analysis = await client.register_service(
            name="sentiment-analysis",
            description="Analyze sentiment of text",
            endpoint="http://sentiment-analysis-service:8000/api",
            actions=[
                {
                    "name": "analyze",
                    "description": "Analyze sentiment of text",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to analyze"
                            }
                        },
                        "required": ["text"]
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "sentiment": {
                                "type": "string",
                                "description": "Sentiment (positive, negative, neutral)"
                            },
                            "score": {
                                "type": "number",
                                "description": "Sentiment score (-1.0 to 1.0)"
                            }
                        },
                        "required": ["sentiment", "score"]
                    }
                }
            ]
        )
        
        print(f"Registered sentiment analysis service with ID: {sentiment_analysis['id']}")
        
        # Create workflow
        workflow = await client.create_workflow(
            name="document-sentiment",
            description="Extract text from a document and analyze sentiment",
            steps=[
                {
                    "id": "extract-text",
                    "service": "text-extraction",
                    "action": "extract",
                    "next": "analyze-sentiment"
                },
                {
                    "id": "analyze-sentiment",
                    "service": "sentiment-analysis",
                    "action": "analyze",
                    "next": None
                }
            ]
        )
        
        print(f"Created workflow with ID: {workflow['id']}")
        
        # Execute workflow
        result = await client.execute_workflow(
            workflow_id=workflow["id"],
            input_data={
                "document_url": "https://example.com/document.pdf"
            },
            context={
                "request_id": get_request_id()
            }
        )
        
        print("Workflow execution result:")
        print(f"Sentiment: {result['sentiment']}")
        print(f"Score: {result['score']}")
        
        return result
    
    except ValidationError as e:
        print(f"Validation error: {e.validation_errors}")
    except ResourceNotFoundError as e:
        print(f"Resource not found: {e.resource_type} with ID {e.resource_id}")
    except ServiceUnavailableError as e:
        print(f"Service unavailable: {e.service_name}")
    except MaxRetriesExceededError as e:
        print(f"Failed after {e.attempts} attempts: {e.last_error}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
```

## Related Documentation

- [Service Integration Service](service-integration-standardization-implementation.md)
- [Cross-Service Communication Improvements](cross-service-communication-improvements.md)
- [Error Handling Best Practices](error-handling-best-practices.md)
- [Service Integration Workflow Guide](service-integration-workflow-guide.md)
