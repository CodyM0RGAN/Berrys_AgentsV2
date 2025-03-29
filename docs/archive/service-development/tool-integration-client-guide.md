# Tool Integration Client Guide

> **Draft-of-Thought Documentation**: This document provides guidance on using the Tool Integration Client to interact with the Tool Integration service. It covers client initialization, available methods, error handling, and best practices.

## Overview

The Tool Integration Client provides a standardized way to interact with the Tool Integration service. It handles communication details, error handling, and includes retry mechanisms with exponential backoff to handle transient failures.

The client is implemented in `shared/utils/src/clients/tool_integration.py` and can be imported from the shared package:

```python
from shared.utils.src.clients import ToolIntegrationClient
```

## Client Initialization

The client can be initialized with the base URL of the Tool Integration service and an optional timeout value:

```python
# Initialize with default timeout
client = ToolIntegrationClient(base_url="http://localhost:8006/api")

# Initialize with custom timeout
client = ToolIntegrationClient(base_url="http://localhost:8006/api", timeout=30)
```

In the web dashboard, you can get a pre-configured client using the `get_tool_integration_client` function:

```python
from app.api.clients import get_tool_integration_client

client = get_tool_integration_client()
```

## Available Methods

The Tool Integration Client provides the following methods:

### Tool Management

#### Register a Tool

```python
tool = await client.register_tool(
    name="code-generator",
    tool_type="code",
    description="Generates code based on natural language descriptions",
    capabilities=["python", "javascript", "typescript"],
    config_schema={
        "type": "object",
        "properties": {
            "model": {
                "type": "string",
                "description": "Model to use for code generation"
            },
            "temperature": {
                "type": "number",
                "description": "Temperature for code generation",
                "minimum": 0,
                "maximum": 1
            }
        },
        "required": ["model"]
    },
    metadata={
        "version": "1.0.0",
        "author": "Berry's Agents Team"
    }
)
```

#### Update a Tool

```python
updated_tool = await client.update_tool(
    tool_id="123",
    name="code-generator-v2",
    description="Improved code generator with better error handling",
    capabilities=["python", "javascript", "typescript", "go"],
    status="ACTIVE"
)
```

#### Deregister a Tool

```python
result = await client.deregister_tool(tool_id="123")
```

#### Get Tool Details

```python
tool = client.get_tool(tool_id="123")
```

#### List Tools

```python
# Get all tools
tools = client.get_tools()

# Filter by tool type
code_tools = client.get_tools(tool_type="code")

# Filter by capability
python_tools = client.get_tools(capability="python")

# Filter by status
active_tools = client.get_tools(status="ACTIVE")

# Pagination
tools_page_2 = client.get_tools(page=2, per_page=10)
```

### Tool Instance Management

#### Create a Tool Instance

```python
instance = await client.create_tool_instance(
    tool_id="123",
    name="Python Code Generator",
    config={
        "model": "gpt-4",
        "temperature": 0.7
    },
    description="Instance of code generator for Python code",
    metadata={
        "project_id": "456",
        "created_by": "user123"
    }
)
```

#### Update a Tool Instance

```python
updated_instance = await client.update_tool_instance(
    instance_id="789",
    name="Python Code Generator (Low Temperature)",
    config={
        "model": "gpt-4",
        "temperature": 0.2
    },
    status="ACTIVE"
)
```

#### Delete a Tool Instance

```python
result = await client.delete_tool_instance(instance_id="789")
```

#### Get Tool Instance Details

```python
instance = client.get_tool_instance(instance_id="789")
```

#### List Tool Instances

```python
# Get all instances
instances = client.get_tool_instances()

# Filter by tool ID
code_generator_instances = client.get_tool_instances(tool_id="123")

# Filter by status
active_instances = client.get_tool_instances(status="ACTIVE")

# Pagination
instances_page_2 = client.get_tool_instances(page=2, per_page=10)
```

### Tool Execution

#### Execute a Tool

```python
result = await client.execute_tool(
    instance_id="789",
    action="generate",
    parameters={
        "prompt": "Create a Python function to calculate Fibonacci numbers",
        "language": "python",
        "comments": True
    },
    context={
        "project_id": "456",
        "request_id": "req-123"
    }
)
```

### Tool Schema and Validation

#### Get Tool Schema

```python
schema = await client.get_tool_schema(tool_id="123")
```

#### Validate Tool Configuration

```python
validation_result = await client.validate_tool_config(
    tool_id="123",
    config={
        "model": "gpt-4",
        "temperature": 0.7
    }
)
```

## Error Handling

The Tool Integration Client includes built-in error handling with retry mechanisms for transient failures. However, you should still handle exceptions in your code:

```python
from shared.utils.src.exceptions import (
    ServiceUnavailableError,
    ResourceNotFoundError,
    ValidationError,
    MaxRetriesExceededError
)

try:
    tool = await client.register_tool(
        name="code-generator",
        tool_type="code",
        description="Generates code based on natural language descriptions",
        capabilities=["python", "javascript", "typescript"],
        config_schema={...}
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

The Tool Integration Client includes retry mechanisms with exponential backoff for handling transient failures. The retry policy is configured differently for different operation types:

- **Create operations**: 3 retries with base delay of 0.5 seconds and max delay of 4 seconds
- **Update operations**: 3 retries with base delay of 0.5 seconds and max delay of 4 seconds
- **Delete operations**: 2 retries with base delay of 1 second and max delay of 4 seconds
- **Read operations**: 2 retries with base delay of 0.5 seconds and max delay of 2 seconds

The retry mechanism automatically handles `ServiceUnavailableError` exceptions and will retry the operation with exponential backoff. If the operation still fails after the maximum number of retries, a `MaxRetriesExceededError` exception is raised.

## Circuit Breaker Pattern

The Tool Integration Client also includes a circuit breaker pattern to prevent cascading failures when the Tool Integration service is unavailable. The circuit breaker is implemented using the `CircuitBreaker` class from `shared/utils/src/circuit_breaker.py`.

When the circuit breaker is open, all requests to the Tool Integration service will be rejected without attempting to call the service. This prevents overwhelming the service with requests when it's already struggling.

## Best Practices

### Use Async Methods

Most methods in the Tool Integration Client are asynchronous and should be used with `await`:

```python
# Good
tool = await client.register_tool(...)

# Bad
tool = client.register_tool(...)  # This will return a coroutine, not the actual result
```

### Handle Exceptions

Always handle exceptions when calling methods on the Tool Integration Client:

```python
# Good
try:
    tool = await client.register_tool(...)
except Exception as e:
    # Handle the exception
    print(f"Error: {str(e)}")

# Bad
tool = await client.register_tool(...)  # No exception handling
```

### Use Pagination for Large Result Sets

When retrieving large lists of tools or tool instances, use pagination to avoid performance issues:

```python
# Good
page = 1
per_page = 10
while True:
    tools = client.get_tools(page=page, per_page=per_page)
    if not tools["items"]:
        break
    
    # Process tools
    for tool in tools["items"]:
        process_tool(tool)
    
    page += 1

# Bad
all_tools = client.get_tools(per_page=1000)  # Retrieving too many items at once
```

### Use Context Information

When executing tools, provide context information to help with debugging and tracing:

```python
# Good
result = await client.execute_tool(
    instance_id="789",
    action="generate",
    parameters={...},
    context={
        "project_id": "456",
        "request_id": get_request_id()
    }
)

# Bad
result = await client.execute_tool(
    instance_id="789",
    action="generate",
    parameters={...}
)
```

### Validate Tool Configurations

Before creating a tool instance, validate the configuration against the tool's schema:

```python
# Good
validation_result = await client.validate_tool_config(
    tool_id="123",
    config={
        "model": "gpt-4",
        "temperature": 0.7
    }
)

if validation_result["valid"]:
    instance = await client.create_tool_instance(
        tool_id="123",
        name="Python Code Generator",
        config={
            "model": "gpt-4",
            "temperature": 0.7
        }
    )
else:
    # Handle validation errors
    print(f"Validation errors: {validation_result['errors']}")

# Bad
instance = await client.create_tool_instance(
    tool_id="123",
    name="Python Code Generator",
    config={
        "model": "gpt-4",
        "temperature": 0.7
    }
)
```

## Example: Complete Tool Registration and Execution

Here's a complete example of registering a tool, creating an instance, and executing it:

```python
from shared.utils.src.clients import ToolIntegrationClient
from shared.utils.src.exceptions import (
    ServiceUnavailableError,
    ResourceNotFoundError,
    ValidationError,
    MaxRetriesExceededError
)
from shared.utils.src.request_id import get_request_id

async def register_and_execute_code_generator():
    client = ToolIntegrationClient(base_url="http://localhost:8006/api")
    
    try:
        # Register the tool
        tool = await client.register_tool(
            name="code-generator",
            tool_type="code",
            description="Generates code based on natural language descriptions",
            capabilities=["python", "javascript", "typescript"],
            config_schema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Model to use for code generation"
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Temperature for code generation",
                        "minimum": 0,
                        "maximum": 1
                    }
                },
                "required": ["model"]
            }
        )
        
        print(f"Registered tool with ID: {tool['id']}")
        
        # Create a tool instance
        instance = await client.create_tool_instance(
            tool_id=tool["id"],
            name="Python Code Generator",
            config={
                "model": "gpt-4",
                "temperature": 0.7
            }
        )
        
        print(f"Created tool instance with ID: {instance['id']}")
        
        # Execute the tool
        result = await client.execute_tool(
            instance_id=instance["id"],
            action="generate",
            parameters={
                "prompt": "Create a Python function to calculate Fibonacci numbers",
                "language": "python",
                "comments": True
            },
            context={
                "request_id": get_request_id()
            }
        )
        
        print("Tool execution result:")
        print(result["output"])
        
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

- [Tool Integration Service](tool-integration-standardization-implementation.md)
- [Cross-Service Communication Improvements](cross-service-communication-improvements.md)
- [Error Handling Best Practices](error-handling-best-practices.md)
- [Service Integration Workflow Guide](service-integration-workflow-guide.md)
