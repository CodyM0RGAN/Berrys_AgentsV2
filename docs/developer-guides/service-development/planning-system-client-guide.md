# Planning System Client Guide

> **Draft-of-Thought Documentation**: This document provides guidance on using the Planning System Client to interact with the Planning System service. It covers client initialization, available methods, error handling, and best practices.

## Overview

The Planning System Client provides a standardized way to interact with the Planning System service. It handles communication details, error handling, and includes retry mechanisms with exponential backoff to handle transient failures.

The client is implemented in `shared/utils/src/clients/planning_system.py` and can be imported from the shared package:

```python
from shared.utils.src.clients import PlanningSystemClient
```

## Client Initialization

The client can be initialized with the base URL of the Planning System service and an optional timeout value:

```python
# Initialize with default timeout
client = PlanningSystemClient(base_url="http://localhost:8004/api")

# Initialize with custom timeout
client = PlanningSystemClient(base_url="http://localhost:8004/api", timeout=30)
```

In the web dashboard, you can get a pre-configured client using the `get_planning_system_client` function:

```python
from app.api.clients import get_planning_system_client

client = get_planning_system_client()
```

## Available Methods

The Planning System Client provides the following methods:

### Plan Management

#### Create a Plan

```python
plan = await client.create_plan(
    name="website-development",
    description="Develop a company website",
    project_id="123",
    objectives=[
        "Create a responsive website",
        "Implement a contact form",
        "Optimize for SEO"
    ],
    constraints=[
        "Must be completed within 2 weeks",
        "Must use React for frontend"
    ],
    metadata={
        "priority": "high",
        "client": "Acme Corp"
    }
)
```

#### Update a Plan

```python
updated_plan = await client.update_plan(
    plan_id="456",
    name="website-development-v2",
    description="Develop an improved company website",
    objectives=[
        "Create a responsive website",
        "Implement a contact form",
        "Optimize for SEO",
        "Add a blog section"
    ],
    status="IN_PROGRESS"
)
```

#### Delete a Plan

```python
result = await client.delete_plan(plan_id="456")
```

#### Get Plan Details

```python
plan = client.get_plan(plan_id="456")
```

#### List Plans

```python
# Get all plans
plans = client.get_plans()

# Filter by project ID
project_plans = client.get_plans(project_id="123")

# Filter by status
active_plans = client.get_plans(status="IN_PROGRESS")

# Pagination
plans_page_2 = client.get_plans(page=2, per_page=10)
```

### Task Management

#### Create a Task

```python
task = await client.create_task(
    title="Design homepage",
    description="Create a responsive design for the homepage",
    plan_id="456",
    priority="HIGH",
    estimated_hours=8,
    dependencies=["task-789"],
    assigned_to="agent-123",
    metadata={
        "skills_required": ["UI/UX", "HTML", "CSS"],
        "resources": ["design-system.pdf"]
    }
)
```

#### Update a Task

```python
updated_task = await client.update_task(
    task_id="789",
    title="Design homepage and about page",
    description="Create responsive designs for homepage and about page",
    priority="MEDIUM",
    status="IN_PROGRESS",
    progress=50,
    actual_hours=4
)
```

#### Delete a Task

```python
result = await client.delete_task(task_id="789")
```

#### Get Task Details

```python
task = client.get_task(task_id="789")
```

#### List Tasks

```python
# Get all tasks for a plan
plan_tasks = client.get_tasks(plan_id="456")

# Filter by status
in_progress_tasks = client.get_tasks(plan_id="456", status="IN_PROGRESS")

# Filter by assigned agent
agent_tasks = client.get_tasks(assigned_to="agent-123")

# Filter by priority
high_priority_tasks = client.get_tasks(priority="HIGH")

# Pagination
tasks_page_2 = client.get_tasks(plan_id="456", page=2, per_page=10)
```

### Planning Operations

#### Generate Plan

```python
generated_plan = await client.generate_plan(
    project_id="123",
    name="website-development",
    description="Develop a company website",
    requirements=[
        "Responsive design",
        "Contact form",
        "About page",
        "Services page",
        "Blog section"
    ],
    constraints=[
        "Must be completed within 2 weeks",
        "Must use React for frontend"
    ],
    available_agents=[
        {
            "id": "agent-123",
            "name": "UI Designer",
            "capabilities": ["UI/UX", "HTML", "CSS"]
        },
        {
            "id": "agent-456",
            "name": "Frontend Developer",
            "capabilities": ["React", "JavaScript", "TypeScript"]
        },
        {
            "id": "agent-789",
            "name": "Backend Developer",
            "capabilities": ["Node.js", "Express", "MongoDB"]
        }
    ],
    context={
        "project_type": "website",
        "industry": "technology",
        "request_id": "req-123"
    }
)
```

#### Optimize Plan

```python
optimized_plan = await client.optimize_plan(
    plan_id="456",
    optimization_goals=[
        "minimize_duration",
        "balance_workload"
    ],
    constraints=[
        "maintain_dependencies",
        "respect_agent_capabilities"
    ],
    context={
        "request_id": "req-123"
    }
)
```

#### Analyze Plan

```python
analysis = await client.analyze_plan(
    plan_id="456",
    analysis_types=[
        "critical_path",
        "resource_utilization",
        "risk_assessment"
    ],
    context={
        "request_id": "req-123"
    }
)
```

### Task Operations

#### Suggest Next Tasks

```python
next_tasks = await client.suggest_next_tasks(
    plan_id="456",
    agent_id="agent-123",
    count=3,
    context={
        "request_id": "req-123"
    }
)
```

#### Estimate Task Duration

```python
estimate = await client.estimate_task_duration(
    task_description="Create a responsive design for the homepage",
    agent_id="agent-123",
    context={
        "request_id": "req-123"
    }
)
```

#### Decompose Task

```python
subtasks = await client.decompose_task(
    task_id="789",
    decomposition_level="detailed",
    context={
        "request_id": "req-123"
    }
)
```

## Error Handling

The Planning System Client includes built-in error handling with retry mechanisms for transient failures. However, you should still handle exceptions in your code:

```python
from shared.utils.src.exceptions import (
    ServiceUnavailableError,
    ResourceNotFoundError,
    ValidationError,
    MaxRetriesExceededError
)

try:
    plan = await client.create_plan(
        name="website-development",
        description="Develop a company website",
        project_id="123",
        objectives=[
            "Create a responsive website",
            "Implement a contact form",
            "Optimize for SEO"
        ]
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

The Planning System Client includes retry mechanisms with exponential backoff for handling transient failures. The retry policy is configured differently for different operation types:

- **Create operations**: 3 retries with base delay of 0.5 seconds and max delay of 4 seconds
- **Update operations**: 3 retries with base delay of 0.5 seconds and max delay of 4 seconds
- **Delete operations**: 2 retries with base delay of 1 second and max delay of 4 seconds
- **Read operations**: 2 retries with base delay of 0.5 seconds and max delay of 2 seconds

The retry mechanism automatically handles `ServiceUnavailableError` exceptions and will retry the operation with exponential backoff. If the operation still fails after the maximum number of retries, a `MaxRetriesExceededError` exception is raised.

## Circuit Breaker Pattern

The Planning System Client also includes a circuit breaker pattern to prevent cascading failures when the Planning System service is unavailable. The circuit breaker is implemented using the `CircuitBreaker` class from `shared/utils/src/circuit_breaker.py`.

When the circuit breaker is open, all requests to the Planning System service will be rejected without attempting to call the service. This prevents overwhelming the service with requests when it's already struggling.

## Best Practices

### Use Async Methods

Most methods in the Planning System Client are asynchronous and should be used with `await`:

```python
# Good
plan = await client.create_plan(...)

# Bad
plan = client.create_plan(...)  # This will return a coroutine, not the actual result
```

### Handle Exceptions

Always handle exceptions when calling methods on the Planning System Client:

```python
# Good
try:
    plan = await client.create_plan(...)
except Exception as e:
    # Handle the exception
    print(f"Error: {str(e)}")

# Bad
plan = await client.create_plan(...)  # No exception handling
```

### Use Pagination for Large Result Sets

When retrieving large lists of plans or tasks, use pagination to avoid performance issues:

```python
# Good
page = 1
per_page = 10
while True:
    plans = client.get_plans(page=page, per_page=per_page)
    if not plans["items"]:
        break
    
    # Process plans
    for plan in plans["items"]:
        process_plan(plan)
    
    page += 1

# Bad
all_plans = client.get_plans(per_page=1000)  # Retrieving too many items at once
```

### Use Context Information

When generating plans or performing other operations, provide context information to help with debugging and tracing:

```python
# Good
generated_plan = await client.generate_plan(
    project_id="123",
    name="website-development",
    description="Develop a company website",
    requirements=[...],
    context={
        "project_type": "website",
        "industry": "technology",
        "request_id": get_request_id()
    }
)

# Bad
generated_plan = await client.generate_plan(
    project_id="123",
    name="website-development",
    description="Develop a company website",
    requirements=[...]
)
```

### Validate Dependencies

When creating tasks with dependencies, validate that the dependencies exist:

```python
# Good
dependencies = ["task-789", "task-790"]
for dependency_id in dependencies:
    try:
        dependency = client.get_task(task_id=dependency_id)
    except ResourceNotFoundError:
        raise ValueError(f"Dependency task {dependency_id} not found")

task = await client.create_task(
    title="Design homepage",
    description="Create a responsive design for the homepage",
    plan_id="456",
    dependencies=dependencies
)

# Bad
task = await client.create_task(
    title="Design homepage",
    description="Create a responsive design for the homepage",
    plan_id="456",
    dependencies=["task-789", "task-790"]  # Not validating dependencies
)
```

## Example: Complete Plan and Task Creation

Here's a complete example of creating a plan, generating tasks, and assigning them to agents:

```python
from shared.utils.src.clients import PlanningSystemClient
from shared.utils.src.exceptions import (
    ServiceUnavailableError,
    ResourceNotFoundError,
    ValidationError,
    MaxRetriesExceededError
)
from shared.utils.src.request_id import get_request_id

async def create_website_development_plan():
    client = PlanningSystemClient(base_url="http://localhost:8004/api")
    
    try:
        # Create a plan
        plan = await client.create_plan(
            name="website-development",
            description="Develop a company website",
            project_id="123",
            objectives=[
                "Create a responsive website",
                "Implement a contact form",
                "Optimize for SEO"
            ],
            constraints=[
                "Must be completed within 2 weeks",
                "Must use React for frontend"
            ]
        )
        
        print(f"Created plan with ID: {plan['id']}")
        
        # Generate tasks for the plan
        generated_plan = await client.generate_plan(
            project_id="123",
            name=plan["name"],
            description=plan["description"],
            requirements=[
                "Responsive design",
                "Contact form",
                "About page",
                "Services page",
                "Blog section"
            ],
            available_agents=[
                {
                    "id": "agent-123",
                    "name": "UI Designer",
                    "capabilities": ["UI/UX", "HTML", "CSS"]
                },
                {
                    "id": "agent-456",
                    "name": "Frontend Developer",
                    "capabilities": ["React", "JavaScript", "TypeScript"]
                },
                {
                    "id": "agent-789",
                    "name": "Backend Developer",
                    "capabilities": ["Node.js", "Express", "MongoDB"]
                }
            ],
            context={
                "request_id": get_request_id()
            }
        )
        
        print(f"Generated plan with {len(generated_plan['tasks'])} tasks")
        
        # Create tasks from the generated plan
        for task_data in generated_plan["tasks"]:
            task = await client.create_task(
                title=task_data["title"],
                description=task_data["description"],
                plan_id=plan["id"],
                priority=task_data["priority"],
                estimated_hours=task_data["estimated_hours"],
                dependencies=task_data.get("dependencies", []),
                assigned_to=task_data.get("assigned_to")
            )
            
            print(f"Created task '{task['title']}' with ID: {task['id']}")
        
        # Optimize the plan
        optimized_plan = await client.optimize_plan(
            plan_id=plan["id"],
            optimization_goals=["minimize_duration", "balance_workload"],
            context={
                "request_id": get_request_id()
            }
        )
        
        print(f"Optimized plan: {optimized_plan['name']}")
        print(f"Estimated duration: {optimized_plan['estimated_duration']} hours")
        
        return plan
    
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

- [Planning System Service](planning-system-standardization-implementation.md)
- [Cross-Service Communication Improvements](cross-service-communication-improvements.md)
- [Error Handling Best Practices](error-handling-best-practices.md)
- [Service Integration Workflow Guide](service-integration-workflow-guide.md)
