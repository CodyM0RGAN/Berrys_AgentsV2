# Cross-Service Validation Guide

> **Draft-of-Thought Documentation**: This document provides guidance on using the cross-service validation utilities to ensure data integrity and consistency across service boundaries in the Berrys_AgentsV2 system.

## Overview

Cross-service validation is a critical aspect of maintaining data integrity in a microservices architecture. This guide explains how to use the cross-service validation utilities provided in the `shared/utils/src/cross_service_validation.py` module to validate requests and responses that cross service boundaries.

## Table of Contents

- [Why Cross-Service Validation is Important](#why-cross-service-validation-is-important)
- [Available Validation Utilities](#available-validation-utilities)
- [Validating Cross-Service Requests](#validating-cross-service-requests)
- [Validating Service Responses](#validating-service-responses)
- [Creating Custom Validators](#creating-custom-validators)
- [Common Validation Patterns](#common-validation-patterns)
- [Best Practices](#best-practices)
- [Examples](#examples)

## Why Cross-Service Validation is Important

In a microservices architecture, data often needs to be transformed as it crosses service boundaries. This transformation can introduce inconsistencies or errors if not properly validated. Cross-service validation helps ensure that:

1. **Data Integrity**: Data sent to other services meets their expectations and constraints
2. **Error Detection**: Issues are caught early, before they propagate through the system
3. **Consistent Error Handling**: Validation errors are handled consistently across services
4. **Documentation**: Validation requirements serve as implicit documentation of service contracts

## Available Validation Utilities

The cross-service validation module provides several utilities:

1. **Decorators**:
   - `validate_cross_service_request`: Validates requests before they're sent to another service
   - `validate_service_response`: Validates responses received from other services

2. **Helper Functions**:
   - `create_field_validator`: Creates a validator function for a specific field type
   - `create_validators_from_model`: Creates field validators from a Pydantic model

3. **Common Validators**:
   - `validate_project_id`: Validates project IDs
   - `validate_agent_id`: Validates agent IDs
   - `validate_task_id`: Validates task IDs
   - `validate_model_id`: Validates model IDs
   - `validate_tool_id`: Validates tool IDs
   - `validate_user_id`: Validates user IDs
   - `validate_plan_id`: Validates plan IDs

## Validating Cross-Service Requests

The `validate_cross_service_request` decorator can be used to validate requests before they're sent to another service:

```python
from shared.models.src.project import ProjectCreateRequest
from shared.utils.src.cross_service_validation import validate_cross_service_request

@validate_cross_service_request(
    target_service="project-coordinator",
    request_model=ProjectCreateRequest
)
async def create_project(project_data: Dict[str, Any]) -> Dict[str, Any]:
    # This function will validate project_data against ProjectCreateRequest
    # before proceeding with the actual request
    return await project_coordinator_client.create_project(project_data)
```

You can also provide field-specific validators:

```python
from shared.utils.src.cross_service_validation import (
    validate_cross_service_request,
    validate_string,
    validate_uuid
)

@validate_cross_service_request(
    target_service="project-coordinator",
    field_validators={
        "name": lambda value: validate_string(value, "name", min_length=3, max_length=100),
        "project_id": lambda value: validate_uuid(value, "project_id")
    }
)
async def update_project(project_id: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
    return await project_coordinator_client.update_project(project_id, project_data)
```

## Validating Service Responses

The `validate_service_response` decorator can be used to validate responses received from other services:

```python
from shared.models.src.project import ProjectResponse
from shared.utils.src.cross_service_validation import validate_service_response

@validate_service_response(
    source_service="project-coordinator",
    response_model=ProjectResponse
)
async def get_project(project_id: str) -> Dict[str, Any]:
    return await project_coordinator_client.get_project(project_id)
```

## Creating Custom Validators

You can create custom validators for specific fields:

```python
from shared.utils.src.validation import ValidationException

def validate_project_name(name: Any) -> str:
    if not isinstance(name, str):
        raise ValidationException("Project name must be a string", "name")
    
    if len(name) < 3:
        raise ValidationException("Project name must be at least 3 characters", "name")
    
    if len(name) > 100:
        raise ValidationException("Project name must be at most 100 characters", "name")
    
    # Check for invalid characters
    if not re.match(r'^[a-zA-Z0-9_\- ]+$', name):
        raise ValidationException(
            "Project name can only contain letters, numbers, spaces, hyphens, and underscores",
            "name"
        )
    
    return name
```

## Common Validation Patterns

### 1. Validating IDs

Use the provided ID validators for common entity types:

```python
from shared.utils.src.cross_service_validation import validate_project_id, validate_agent_id

# Validate a project ID
project_id = validate_project_id(request_data.get("project_id"))

# Validate an agent ID
agent_id = validate_agent_id(request_data.get("agent_id"))
```

### 2. Validating Enum Values

Ensure enum values are valid:

```python
from shared.models.src.enums import ProjectStatus
from shared.utils.src.validation import validate_enum

# Validate a project status
status = validate_enum(request_data.get("status"), ProjectStatus, "status")
```

### 3. Validating Nested Models

Validate complex nested structures:

```python
from shared.models.src.project import ProjectSettings
from shared.utils.src.validation import validate_model

# Validate project settings
settings = validate_model(request_data.get("settings"), ProjectSettings, "settings")
```

## Best Practices

1. **Validate Early**: Validate requests as early as possible, ideally before they leave the originating service
2. **Validate Thoroughly**: Validate all fields that are critical for the receiving service
3. **Provide Clear Error Messages**: Make error messages descriptive and actionable
4. **Use Appropriate Validators**: Use the most specific validator for each field type
5. **Handle Validation Errors Gracefully**: Catch and handle validation errors appropriately
6. **Log Validation Failures**: Log validation failures for debugging and monitoring
7. **Test Validation Logic**: Write tests for your validation logic to ensure it works as expected

## Examples

For a complete working example, see [cross_service_validation_example.py](examples/cross_service_validation_example.py).

### Example 1: Project Coordinator Client

```python
from shared.models.src.project import ProjectCreateRequest, ProjectResponse
from shared.utils.src.cross_service_validation import (
    validate_cross_service_request,
    validate_service_response
)

class ProjectCoordinatorClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    @validate_cross_service_request(
        target_service="project-coordinator",
        request_model=ProjectCreateRequest
    )
    @validate_service_response(
        source_service="project-coordinator",
        response_model=ProjectResponse
    )
    async def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation details...
        pass
    
    @validate_cross_service_request(
        target_service="project-coordinator",
        field_validators={
            "project_id": lambda value: validate_uuid(value, "project_id")
        }
    )
    @validate_service_response(
        source_service="project-coordinator",
        response_model=ProjectResponse
    )
    async def get_project(self, project_id: str) -> Dict[str, Any]:
        # Implementation details...
        pass
```

### Example 2: Agent Orchestrator Client

```python
from shared.models.src.agent import AgentCreateRequest, AgentResponse
from shared.utils.src.cross_service_validation import (
    validate_cross_service_request,
    validate_service_response,
    validate_agent_id,
    validate_project_id
)

class AgentOrchestratorClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    @validate_cross_service_request(
        target_service="agent-orchestrator",
        request_model=AgentCreateRequest
    )
    @validate_service_response(
        source_service="agent-orchestrator",
        response_model=AgentResponse
    )
    async def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation details...
        pass
    
    @validate_cross_service_request(
        target_service="agent-orchestrator",
        field_validators={
            "agent_id": lambda value: validate_agent_id(value),
            "project_id": lambda value: validate_project_id(value)
        }
    )
    async def assign_agent_to_project(
        self, agent_id: str, project_id: str
    ) -> Dict[str, Any]:
        # Implementation details...
        pass
```

### Example 3: Using Validators Created from a Model

```python
from shared.models.src.project import ProjectCreateRequest
from shared.utils.src.cross_service_validation import create_validators_from_model

# Create validators from the ProjectCreateRequest model
validators = create_validators_from_model(ProjectCreateRequest)

# Use the validators to validate a dictionary
project_data = {
    "name": "Example Project",
    "description": "This is an example project",
    "status": ProjectStatus.PLANNING,
    "metadata": {"key": "value"}
}

# Validate each field
for field_name, validator in validators.items():
    if field_name in project_data:
        try:
            # Apply the validator
            validator(project_data[field_name])
            print(f"Field {field_name} is valid")
        except Exception as e:
            print(f"Field {field_name} is invalid: {str(e)}")
```

## Related Documentation

- [Error Handling Best Practices](error-handling-best-practices.md)
- [Cross-Service Communication Improvements](cross-service-communication-improvements.md)
- [Entity Representation Alignment](entity-representation-alignment.md)
- [Adapter Usage Examples](adapter-usage-examples.md)
- [Service Integration Workflow Guide](service-integration-workflow-guide.md)
