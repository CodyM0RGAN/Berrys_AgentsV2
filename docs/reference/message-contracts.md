# Message Contracts

**Last Modified:** 2025-03-29  
**Completion Date:** 2025-03-29  
**Doc Type:** Reference  

---

## Overview

This document defines the standardized message formats used for inter-service communication in the Berrys_AgentsV2 platform. It covers event definitions, message structure, versioning, and validation to ensure consistent and reliable asynchronous communication.

## Message Format

All messages in the system follow a standardized envelope format:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000", 
  "type": "agent.created",
  "source": "agent-orchestrator",
  "timestamp": "2025-03-29T05:43:21.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    // Event-specific payload
  },
  "metadata": {
    // Optional event metadata
  }
}
```

### Message Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| id | UUID | Unique identifier for the message | Yes |
| type | String | Event type in format `domain.action` | Yes |
| source | String | Service that generated the event | Yes |
| timestamp | ISO 8601 | Time when the event was generated | Yes |
| correlation_id | UUID | ID linking related events in a workflow | Yes |
| data | Object | Event-specific payload | Yes |
| metadata | Object | Additional context information | No |

## Message Types

The platform uses the following message domains:

| Domain | Description | Producer Services |
|--------|-------------|-------------------|
| agent | Agent-related events | Agent Orchestrator |
| project | Project-related events | Project Coordinator |
| task | Task-related events | Planning System |
| model | Model execution events | Model Orchestration |
| tool | Tool execution events | Tool Integration |
| workflow | Workflow orchestration events | Service Integration |
| system | System-level events | All services |

## Agent Domain Events

### agent.created

Generated when a new agent is created.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "agent.created",
  "source": "agent-orchestrator",
  "timestamp": "2025-03-29T05:43:21.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "Task Agent",
    "template_id": "550e8400-e29b-41d4-a716-446655440000",
    "specializations": ["task_execution", "data_analysis"],
    "state": "initializing"
  }
}
```

### agent.initialized

Generated when an agent has completed initialization.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "type": "agent.initialized",
  "source": "agent-orchestrator",
  "timestamp": "2025-03-29T05:43:25.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "state": "ready",
    "capabilities": ["text_generation", "task_planning", "data_analysis"]
  }
}
```

### agent.state_changed

Generated when an agent's state changes.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "type": "agent.state_changed",
  "source": "agent-orchestrator",
  "timestamp": "2025-03-29T05:45:10.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "previous_state": "ready",
    "new_state": "active",
    "reason": "task_assignment"
  }
}
```

### agent.task_assigned

Generated when a task is assigned to an agent.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "type": "agent.task_assigned",
  "source": "agent-orchestrator",
  "timestamp": "2025-03-29T05:45:05.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
    "priority": "high",
    "deadline": "2025-03-29T06:45:05.123456Z"
  }
}
```

### agent.task_completed

Generated when an agent completes a task.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "type": "agent.task_completed",
  "source": "agent-orchestrator",
  "timestamp": "2025-03-29T05:50:15.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
    "status": "success",
    "result_summary": "Analysis completed successfully",
    "result_location": "s3://results-bucket/task-results/a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d"
  }
}
```

## Project Domain Events

### project.created

Generated when a new project is created.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440005",
  "type": "project.created",
  "source": "project-coordinator",
  "timestamp": "2025-03-29T05:40:00.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "project_id": "b9a8c7d6-e5f4-4g3h-2i1j-0k9l8m7n6o5p",
    "name": "Data Analysis Project",
    "description": "Analyze customer data for trends",
    "requirements": ["data_analysis", "visualization", "report_generation"],
    "created_by": "user-123"
  }
}
```

### project.updated

Generated when a project is updated.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440006",
  "type": "project.updated",
  "source": "project-coordinator",
  "timestamp": "2025-03-29T05:41:30.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "project_id": "b9a8c7d6-e5f4-4g3h-2i1j-0k9l8m7n6o5p",
    "updated_fields": ["description", "requirements"],
    "description": "Analyze customer data for trends and pattern recognition",
    "requirements": ["data_analysis", "visualization", "report_generation", "pattern_recognition"]
  }
}
```

### project.planning_started

Generated when project planning begins.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440007",
  "type": "project.planning_started",
  "source": "project-coordinator",
  "timestamp": "2025-03-29T05:42:00.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "project_id": "b9a8c7d6-e5f4-4g3h-2i1j-0k9l8m7n6o5p",
    "planning_id": "c1d2e3f4-5g6h-7i8j-9k0l-1m2n3o4p5q6r"
  }
}
```

### project.execution_started

Generated when project execution begins.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440008",
  "type": "project.execution_started",
  "source": "project-coordinator",
  "timestamp": "2025-03-29T05:44:00.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "project_id": "b9a8c7d6-e5f4-4g3h-2i1j-0k9l8m7n6o5p",
    "execution_id": "d1e2f3g4-5h6i-7j8k-9l0m-1n2o3p4q5r6s",
    "agent_ids": [
      "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "f47ac10b-58cc-4372-a567-0e02b2c3d480"
    ]
  }
}
```

### project.completed

Generated when a project is completed.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440009",
  "type": "project.completed",
  "source": "project-coordinator",
  "timestamp": "2025-03-29T06:30:00.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "project_id": "b9a8c7d6-e5f4-4g3h-2i1j-0k9l8m7n6o5p",
    "status": "success",
    "results_summary": "Project completed successfully with all requirements met",
    "results_location": "s3://results-bucket/project-results/b9a8c7d6-e5f4-4g3h-2i1j-0k9l8m7n6o5p"
  }
}
```

## Task Domain Events

### task.created

Generated when a new task is created.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440010",
  "type": "task.created",
  "source": "planning-system",
  "timestamp": "2025-03-29T05:42:30.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
    "project_id": "b9a8c7d6-e5f4-4g3h-2i1j-0k9l8m7n6o5p",
    "title": "Data Preprocessing",
    "description": "Clean and normalize customer data",
    "priority": "high",
    "required_capabilities": ["data_cleaning", "normalization"],
    "dependencies": []
  }
}
```

### task.updated

Generated when a task is updated.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440011",
  "type": "task.updated",
  "source": "planning-system",
  "timestamp": "2025-03-29T05:42:45.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
    "updated_fields": ["description", "required_capabilities"],
    "description": "Clean, normalize, and validate customer data",
    "required_capabilities": ["data_cleaning", "normalization", "validation"]
  }
}
```

### task.assigned

Generated when a task is assigned to an agent.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440012",
  "type": "task.assigned",
  "source": "planning-system",
  "timestamp": "2025-03-29T05:45:00.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
    "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "assignment_time": "2025-03-29T05:45:00.123456Z",
    "deadline": "2025-03-29T06:45:00.123456Z"
  }
}
```

### task.status_changed

Generated when a task's status changes.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440013",
  "type": "task.status_changed",
  "source": "planning-system",
  "timestamp": "2025-03-29T05:45:30.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
    "previous_status": "pending",
    "new_status": "in_progress",
    "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
  }
}
```

### task.completed

Generated when a task is completed.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440014",
  "type": "task.completed",
  "source": "planning-system",
  "timestamp": "2025-03-29T05:50:00.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
    "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "success",
    "completion_time": "2025-03-29T05:50:00.123456Z",
    "result_summary": "Data preprocessing completed successfully",
    "artifacts": [
      {
        "name": "preprocessed_data.csv",
        "location": "s3://results-bucket/task-results/a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d/preprocessed_data.csv",
        "type": "data_file",
        "size_bytes": 1048576
      }
    ]
  }
}
```

## Model Domain Events

### model.execution_requested

Generated when a model execution is requested.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440015",
  "type": "model.execution_requested",
  "source": "model-orchestration",
  "timestamp": "2025-03-29T05:46:00.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "execution_id": "e1f2g3h4-5i6j-7k8l-9m0n-1o2p3q4r5s6t",
    "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
    "model_id": "gpt-4",
    "execution_type": "task_planning",
    "priority": "high"
  }
}
```

### model.execution_completed

Generated when a model execution is completed.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440016",
  "type": "model.execution_completed",
  "source": "model-orchestration",
  "timestamp": "2025-03-29T05:46:05.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "execution_id": "e1f2g3h4-5i6j-7k8l-9m0n-1o2p3q4r5s6t",
    "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
    "model_id": "gpt-4",
    "status": "success",
    "execution_time_ms": 1200,
    "token_usage": {
      "prompt_tokens": 512,
      "completion_tokens": 256,
      "total_tokens": 768
    }
  }
}
```

## Tool Domain Events

### tool.execution_requested

Generated when a tool execution is requested.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440017",
  "type": "tool.execution_requested",
  "source": "tool-integration",
  "timestamp": "2025-03-29T05:47:00.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "execution_id": "f1g2h3i4-5j6k-7l8m-9n0o-1p2q3r4s5t6u",
    "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
    "tool_id": "data_cleaner",
    "parameters": {
      "input_file": "s3://data-bucket/raw_data.csv",
      "output_file": "s3://results-bucket/cleaned_data.csv",
      "operations": ["remove_duplicates", "handle_missing_values"]
    }
  }
}
```

### tool.execution_completed

Generated when a tool execution is completed.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440018",
  "type": "tool.execution_completed",
  "source": "tool-integration",
  "timestamp": "2025-03-29T05:48:00.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "execution_id": "f1g2h3i4-5j6k-7l8m-9n0o-1p2q3r4s5t6u",
    "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
    "tool_id": "data_cleaner",
    "status": "success",
    "execution_time_ms": 5000,
    "result": {
      "output_file": "s3://results-bucket/cleaned_data.csv",
      "rows_processed": 10000,
      "duplicates_removed": 120,
      "missing_values_handled": 350
    }
  }
}
```

## Workflow Domain Events

### workflow.started

Generated when a cross-service workflow is started.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440019",
  "type": "workflow.started",
  "source": "service-integration",
  "timestamp": "2025-03-29T05:45:00.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "workflow_id": "g1h2i3j4-5k6l-7m8n-9o0p-1q2r3s4t5u6v",
    "workflow_type": "agent_task_execution",
    "initiated_by": "planning-system",
    "context": {
      "project_id": "b9a8c7d6-e5f4-4g3h-2i1j-0k9l8m7n6o5p",
      "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d"
    }
  }
}
```

### workflow.step_completed

Generated when a workflow step is completed.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440020",
  "type": "workflow.step_completed",
  "source": "service-integration",
  "timestamp": "2025-03-29T05:46:10.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "workflow_id": "g1h2i3j4-5k6l-7m8n-9o0p-1q2r3s4t5u6v",
    "step_id": "step1",
    "step_type": "model_execution",
    "status": "success",
    "result": {
      "execution_id": "e1f2g3h4-5i6j-7k8l-9m0n-1o2p3q4r5s6t"
    },
    "next_step": "step2"
  }
}
```

### workflow.completed

Generated when a workflow is completed.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440021",
  "type": "workflow.completed",
  "source": "service-integration",
  "timestamp": "2025-03-29T05:48:30.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "workflow_id": "g1h2i3j4-5k6l-7m8n-9o0p-1q2r3s4t5u6v",
    "status": "success",
    "execution_time_ms": 210000,
    "result_summary": "Agent task execution workflow completed successfully",
    "steps_completed": 5,
    "steps_failed": 0
  }
}
```

## System Domain Events

### system.service_started

Generated when a service starts.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440022",
  "type": "system.service_started",
  "source": "agent-orchestrator",
  "timestamp": "2025-03-29T05:30:00.123456Z",
  "correlation_id": "system-startup-correlation-id",
  "data": {
    "service_id": "agent-orchestrator",
    "version": "1.5.2",
    "environment": "production",
    "hostname": "agent-orchestrator-pod-7d4f9c8b6a"
  }
}
```

### system.service_health

Generated periodically for service health monitoring.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440023",
  "type": "system.service_health",
  "source": "agent-orchestrator",
  "timestamp": "2025-03-29T05:35:00.123456Z",
  "correlation_id": "system-health-correlation-id",
  "data": {
    "service_id": "agent-orchestrator",
    "status": "healthy",
    "metrics": {
      "cpu_usage_percent": 45.2,
      "memory_usage_mb": 512.7,
      "active_connections": 25,
      "message_queue_depth": 10
    },
    "dependencies": {
      "database": "healthy",
      "redis": "healthy",
      "model-orchestration": "healthy"
    }
  }
}
```

### system.error

Generated when a service encounters an error.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440024",
  "type": "system.error",
  "source": "agent-orchestrator",
  "timestamp": "2025-03-29T05:47:30.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "error_id": "h1i2j3k4-5l6m-7n8o-9p0q-1r2s3t4u5v6w",
    "error_type": "dependency_error",
    "severity": "error",
    "message": "Failed to connect to model-orchestration service",
    "context": {
      "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
      "operation": "model_execution",
      "dependency": "model-orchestration"
    },
    "stack_trace": "..." // Truncated for brevity
  }
}
```

## Message Versioning

Message formats are versioned to support backward compatibility:

1. **Schema Versioning**: The platform maintains versioned message schemas.
2. **Backward Compatibility**: New versions maintain compatibility with older versions.
3. **Version Identification**: Message schemas include a version identifier.
4. **Version Transitions**: Services can handle multiple versions during transition periods.

### Version Transition Process

When introducing a new message format version:

1. Update producing services to include both old and new format fields
2. Update consuming services to accept both old and new formats
3. After all services are updated, remove old format fields

## Message Validation

All messages are validated against JSON Schema definitions:

1. **Schema Repository**: A central schema repository stores all message schemas.
2. **Validation Process**: Messages are validated both at production and consumption time.
3. **Error Handling**: Invalid messages are rejected and logged.
4. **Schema Discovery**: Services can dynamically discover message schemas.

### Validation Implementation

```python
# Example validation implementation
def validate_message(message, schema_registry):
    message_type = message.get("type")
    if not message_type:
        raise ValidationError("Missing message type")
    
    schema = schema_registry.get_schema(message_type)
    if not schema:
        raise ValidationError(f"Unknown message type: {message_type}")
    
    try:
        jsonschema.validate(message, schema)
        return True
    except jsonschema.exceptions.ValidationError as e:
        raise ValidationError(f"Message validation failed: {str(e)}")
```

## Message Handling Best Practices

### Producer Best Practices

1. **Generate Unique IDs**: Always generate a UUID for each message.
2. **Set Accurate Timestamps**: Use precise ISO 8601 timestamps.
3. **Maintain Correlation IDs**: Propagate correlation IDs across related events.
4. **Validate Before Sending**: Always validate messages against schemas.
5. **Handle Send Failures**: Implement retry mechanisms for message publication.

### Consumer Best Practices

1. **Validate on Receipt**: Validate incoming messages against schemas.
2. **Idempotent Processing**: Handle potential message duplicates.
3. **Order Independence**: Don't assume messages will arrive in any particular order.
4. **Graceful Error Handling**: Log errors but avoid crashing on invalid messages.
5. **Correlation Tracking**: Use correlation IDs to track related messages.

## Message Extensions

The standard message format can be extended for specific use cases:

### Batch Messages

For efficient bulk operations:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440025",
  "type": "batch",
  "source": "agent-orchestrator",
  "timestamp": "2025-03-29T05:55:00.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "batch_size": 3,
    "messages": [
      { /* message 1 */ },
      { /* message 2 */ },
      { /* message 3 */ }
    ]
  }
}
```

### Prioritized Messages

For messages requiring special handling:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440026",
  "type": "agent.created",
  "source": "agent-orchestrator",
  "timestamp": "2025-03-29T05:43:21.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "metadata": {
    "priority": "high",
    "ttl_seconds": 300
  },
  "data": {
    /* Event-specific payload */
  }
}
```

## References

- [Communication Patterns](architecture/communication-patterns.md)
- [Service Integration Service](services/service-integration.md)
- [Database Schema Reference](database-schema.md)
