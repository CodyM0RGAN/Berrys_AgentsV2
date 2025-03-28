# Message Contracts for Berrys_AgentsV2

This document defines the standard message contracts for inter-service communication in the Berrys_AgentsV2 system. These contracts ensure consistent and reliable communication between services using the event bus and command bus.

## Overview

The system uses two primary messaging patterns:

1. **Events**: Asynchronous notifications about something that has happened. Events are published by one service and can be consumed by multiple services.

2. **Commands**: Requests to perform an action. Commands are sent from one service to another specific service and typically expect a response.

## Message Format

All messages follow a standard format with metadata and payload:

### Event Format

```json
{
  "id": "string - Unique event ID (UUID)",
  "timestamp": "string - ISO timestamp",
  "sender": "string - Service that published the event",
  "data": {
    // Event-specific payload
  }
}
```

### Command Format

```json
{
  "command_id": "string - Unique command ID (UUID)",
  "command": "string - Command name",
  "data": {
    // Command-specific payload
  },
  "response_channel": "string - Channel for response (optional)"
}
```

### Response Format

```json
{
  "command_id": "string - Original command ID",
  "success": "boolean - Whether the command succeeded",
  "data": {
    // Response data (if success is true)
  },
  "error": "string - Error message (if success is false)",
  "details": {
    // Error details (if success is false)
  }
}
```

## Event Contracts

### Project Events

#### `project.created`

Published when a new project is created.

```json
{
  "project_id": "string - Project ID (UUID)",
  "name": "string - Project name",
  "owner_id": "string - Owner ID (UUID)",
  "status": "string - Project status"
}
```

#### `project.updated`

Published when a project is updated.

```json
{
  "project_id": "string - Project ID (UUID)",
  "updated_fields": ["string - Names of updated fields"],
  "status": "string - Project status"
}
```

#### `project.deleted`

Published when a project is deleted.

```json
{
  "project_id": "string - Project ID (UUID)"
}
```

### Agent Events

#### `agent.created`

Published when a new agent is created.

```json
{
  "agent_id": "string - Agent ID (UUID)",
  "project_id": "string - Project ID (UUID)",
  "name": "string - Agent name",
  "type": "string - Agent type",
  "status": "string - Agent status"
}
```

#### `agent.updated`

Published when an agent is updated.

```json
{
  "agent_id": "string - Agent ID (UUID)",
  "project_id": "string - Project ID (UUID)",
  "updated_fields": ["string - Names of updated fields"],
  "status": "string - Agent status"
}
```

#### `agent.deleted`

Published when an agent is deleted.

```json
{
  "agent_id": "string - Agent ID (UUID)",
  "project_id": "string - Project ID (UUID)"
}
```

#### `agent.status_changed`

Published when an agent's status changes.

```json
{
  "agent_id": "string - Agent ID (UUID)",
  "project_id": "string - Project ID (UUID)",
  "previous_status": "string - Previous status",
  "new_status": "string - New status",
  "reason": "string - Reason for status change (optional)"
}
```

### Task Events

#### `task.created`

Published when a new task is created.

```json
{
  "task_id": "string - Task ID (UUID)",
  "project_id": "string - Project ID (UUID)",
  "agent_id": "string - Agent ID (UUID, optional)",
  "name": "string - Task name",
  "status": "string - Task status",
  "priority": "integer - Task priority (1-5)"
}
```

#### `task.updated`

Published when a task is updated.

```json
{
  "task_id": "string - Task ID (UUID)",
  "project_id": "string - Project ID (UUID)",
  "updated_fields": ["string - Names of updated fields"],
  "status": "string - Task status"
}
```

#### `task.deleted`

Published when a task is deleted.

```json
{
  "task_id": "string - Task ID (UUID)",
  "project_id": "string - Project ID (UUID)"
}
```

#### `task.assigned`

Published when a task is assigned to an agent.

```json
{
  "task_id": "string - Task ID (UUID)",
  "project_id": "string - Project ID (UUID)",
  "agent_id": "string - Agent ID (UUID)",
  "previous_agent_id": "string - Previous agent ID (UUID, optional)"
}
```

#### `task.completed`

Published when a task is completed.

```json
{
  "task_id": "string - Task ID (UUID)",
  "project_id": "string - Project ID (UUID)",
  "agent_id": "string - Agent ID (UUID, optional)",
  "result": {
    // Task result data
  }
}
```

### Tool Events

#### `tool.discovered`

Published when a new tool is discovered.

```json
{
  "tool_id": "string - Tool ID (UUID)",
  "name": "string - Tool name",
  "capability": "string - Tool capability",
  "source": "string - Tool source"
}
```

#### `tool.integrated`

Published when a tool is integrated into the system.

```json
{
  "tool_id": "string - Tool ID (UUID)",
  "name": "string - Tool name",
  "capability": "string - Tool capability",
  "integration_type": "string - Integration type"
}
```

#### `tool.deprecated`

Published when a tool is deprecated.

```json
{
  "tool_id": "string - Tool ID (UUID)",
  "name": "string - Tool name",
  "reason": "string - Reason for deprecation"
}
```

### Model Events

#### `model.request.completed`

Published when a model request is completed.

```json
{
  "request_id": "string - Request ID (UUID)",
  "model_id": "string - Model ID",
  "user_id": "string - User ID (optional)",
  "project_id": "string - Project ID (optional)",
  "task_id": "string - Task ID (optional)",
  "metrics": {
    "latency_ms": "integer - Request latency in milliseconds",
    "tokens": {
      "prompt": "integer - Prompt tokens",
      "completion": "integer - Completion tokens",
      "total": "integer - Total tokens"
    },
    "cost": "float - Cost in USD"
  }
}
```

#### `model.request.failed`

Published when a model request fails.

```json
{
  "request_id": "string - Request ID (UUID)",
  "model_id": "string - Model ID",
  "error": {
    "code": "string - Error code",
    "message": "string - Error message"
  },
  "fallback_attempted": "boolean - Whether fallback was attempted",
  "fallback_succeeded": "boolean - Whether fallback succeeded"
}
```

### Communication Events

#### `communication.sent`

Published when a communication is sent between agents.

```json
{
  "communication_id": "string - Communication ID (UUID)",
  "from_agent_id": "string - Sender agent ID (UUID)",
  "to_agent_id": "string - Recipient agent ID (UUID)",
  "project_id": "string - Project ID (UUID)",
  "type": "string - Communication type",
  "timestamp": "string - ISO timestamp"
}
```

### Audit Events

#### `audit.log_created`

Published when an audit log is created.

```json
{
  "audit_id": "string - Audit ID (UUID)",
  "entity_id": "string - Entity ID (UUID)",
  "entity_type": "string - Entity type",
  "action": "string - Action performed",
  "actor_id": "string - Actor ID (UUID)",
  "timestamp": "string - ISO timestamp"
}
```

## Command Contracts

### Project Commands

#### `project.create`

Create a new project.

Request:
```json
{
  "name": "string - Project name",
  "description": "string - Project description (optional)",
  "owner_id": "string - Owner ID (UUID, optional)"
}
```

Response:
```json
{
  "project_id": "string - Project ID (UUID)",
  "status": "string - 'created'"
}
```

#### `project.update`

Update an existing project.

Request:
```json
{
  "project_id": "string - Project ID (UUID)",
  "name": "string - Project name (optional)",
  "description": "string - Project description (optional)",
  "status": "string - Project status (optional)"
}
```

Response:
```json
{
  "project_id": "string - Project ID (UUID)",
  "status": "string - 'updated'",
  "updated_fields": ["string - Names of updated fields"]
}
```

#### `project.delete`

Delete a project.

Request:
```json
{
  "project_id": "string - Project ID (UUID)"
}
```

Response:
```json
{
  "project_id": "string - Project ID (UUID)",
  "status": "string - 'deleted'"
}
```

### Agent Commands

#### `agent.create`

Create a new agent.

Request:
```json
{
  "project_id": "string - Project ID (UUID)",
  "name": "string - Agent name",
  "type": "string - Agent type",
  "configuration": {
    // Agent configuration
  }
}
```

Response:
```json
{
  "agent_id": "string - Agent ID (UUID)",
  "status": "string - 'created'"
}
```

#### `agent.update`

Update an existing agent.

Request:
```json
{
  "agent_id": "string - Agent ID (UUID)",
  "name": "string - Agent name (optional)",
  "configuration": {
    // Agent configuration (optional)
  },
  "status": "string - Agent status (optional)"
}
```

Response:
```json
{
  "agent_id": "string - Agent ID (UUID)",
  "status": "string - 'updated'",
  "updated_fields": ["string - Names of updated fields"]
}
```

#### `agent.delete`

Delete an agent.

Request:
```json
{
  "agent_id": "string - Agent ID (UUID)"
}
```

Response:
```json
{
  "agent_id": "string - Agent ID (UUID)",
  "status": "string - 'deleted'"
}
```

#### `agent.execute`

Execute an agent on a task.

Request:
```json
{
  "agent_id": "string - Agent ID (UUID)",
  "task_id": "string - Task ID (UUID)",
  "context": [
    // Context items
  ],
  "parameters": {
    // Execution parameters
  }
}
```

Response:
```json
{
  "execution_id": "string - Execution ID (UUID)",
  "status": "string - 'started'"
}
```

### Task Commands

#### `task.create`

Create a new task.

Request:
```json
{
  "project_id": "string - Project ID (UUID)",
  "name": "string - Task name",
  "description": "string - Task description (optional)",
  "agent_id": "string - Agent ID (UUID, optional)",
  "priority": "integer - Task priority (1-5, optional)"
}
```

Response:
```json
{
  "task_id": "string - Task ID (UUID)",
  "status": "string - 'created'"
}
```

#### `task.update`

Update an existing task.

Request:
```json
{
  "task_id": "string - Task ID (UUID)",
  "name": "string - Task name (optional)",
  "description": "string - Task description (optional)",
  "status": "string - Task status (optional)",
  "priority": "integer - Task priority (1-5, optional)"
}
```

Response:
```json
{
  "task_id": "string - Task ID (UUID)",
  "status": "string - 'updated'",
  "updated_fields": ["string - Names of updated fields"]
}
```

#### `task.delete`

Delete a task.

Request:
```json
{
  "task_id": "string - Task ID (UUID)"
}
```

Response:
```json
{
  "task_id": "string - Task ID (UUID)",
  "status": "string - 'deleted'"
}
```

#### `task.assign`

Assign a task to an agent.

Request:
```json
{
  "task_id": "string - Task ID (UUID)",
  "agent_id": "string - Agent ID (UUID)"
}
```

Response:
```json
{
  "task_id": "string - Task ID (UUID)",
  "agent_id": "string - Agent ID (UUID)",
  "status": "string - 'assigned'"
}
```

#### `task.complete`

Mark a task as completed.

Request:
```json
{
  "task_id": "string - Task ID (UUID)",
  "result": {
    // Task result data
  }
}
```

Response:
```json
{
  "task_id": "string - Task ID (UUID)",
  "status": "string - 'completed'"
}
```

### Model Commands

#### `model.request`

Send a request to a model.

Request:
```json
{
  "model_id": "string - Model ID (optional)",
  "provider": "string - Provider (optional)",
  "request_type": "string - Request type (e.g., 'completion', 'chat')",
  "content": {
    // Request content
  },
  "parameters": {
    // Request parameters
  }
}
```

Response:
```json
{
  "request_id": "string - Request ID (UUID)",
  "model_id": "string - Model ID used",
  "provider": "string - Provider used",
  "content": {
    // Response content
  },
  "usage": {
    "prompt_tokens": "integer - Prompt tokens",
    "completion_tokens": "integer - Completion tokens",
    "total_tokens": "integer - Total tokens",
    "cost": "float - Cost in USD"
  }
}
```

#### `model.register`

Register a new model with the system.

Request:
```json
{
  "model_id": "string - Model ID",
  "provider": "string - Provider",
  "capabilities": ["string - Capability"],
  "configuration": {
    // Model configuration
  }
}
```

Response:
```json
{
  "model_id": "string - Model ID",
  "status": "string - 'registered'"
}
```

### Tool Commands

#### `tool.discover`

Discover tools based on requirements.

Request:
```json
{
  "requirements": [
    {
      "capability": "string - Required capability",
      "description": "string - Requirement description",
      "priority": "integer - Priority (1-5)"
    }
  ],
  "context": {
    // Discovery context
  }
}
```

Response:
```json
{
  "tools": [
    {
      "tool_id": "string - Tool ID (UUID)",
      "name": "string - Tool name",
      "capability": "string - Tool capability",
      "source": "string - Tool source",
      "score": "float - Match score (0.0-1.0)"
    }
  ]
}
```

#### `tool.integrate`

Integrate a tool into the system.

Request:
```json
{
  "tool_id": "string - Tool ID (UUID)",
  "integration_type": "string - Integration type",
  "configuration": {
    // Integration configuration
  }
}
```

Response:
```json
{
  "tool_id": "string - Tool ID (UUID)",
  "status": "string - 'integrated'"
}
```

#### `tool.execute`

Execute a tool.

Request:
```json
{
  "tool_id": "string - Tool ID (UUID)",
  "parameters": {
    // Tool parameters
  }
}
```

Response:
```json
{
  "execution_id": "string - Execution ID (UUID)",
  "result": {
    // Execution result
  }
}
```

## Message Flow Examples

### Project Creation Flow

1. API Gateway receives a request to create a project
2. API Gateway sends `project.create` command to Project Coordinator
3. Project Coordinator creates the project in the database
4. Project Coordinator publishes `project.created` event
5. Planning System subscribes to `project.created` event and initiates planning
6. Planning System sends `agent.create` commands to Agent Orchestrator to create required agents
7. Agent Orchestrator creates agents and publishes `agent.created` events
8. Planning System creates tasks and publishes `task.created` events
9. Project Coordinator updates project status and publishes `project.updated` event

### Agent Execution Flow

1. API Gateway receives a request to execute an agent on a task
2. API Gateway sends `agent.execute` command to Agent Orchestrator
3. Agent Orchestrator retrieves agent configuration and task details
4. Agent Orchestrator sends `model.request` command to Model Orchestration
5. Model Orchestration processes the request and returns the response
6. Agent Orchestrator updates task status and publishes `task.updated` event
7. If task is completed, Agent Orchestrator publishes `task.completed` event
8. Project Coordinator updates project progress based on completed task

## Implementation Guidelines

1. **Versioning**: Include version information in message schemas to support backward compatibility
2. **Validation**: Validate messages against schemas before processing
3. **Idempotency**: Design handlers to be idempotent to handle duplicate messages
4. **Error Handling**: Include detailed error information in failure responses
5. **Monitoring**: Log all message processing for debugging and monitoring
6. **Testing**: Write tests for message handlers and publishers
