# Service Integration Service

**Last Modified:** 2025-03-29  
**Completion Date:** 2025-03-29  
**Doc Type:** Reference  

---

## Overview

The Service Integration service enables cross-service workflows in the Berrys_AgentsV2 platform. It handles workflow orchestration, state management, event processing, and error handling to coordinate complex operations that span multiple services. The service acts as the glue that connects individual services into cohesive business processes.

## Service Responsibilities

- **Workflow Definition**: Creating and managing workflow definitions
- **Workflow Orchestration**: Executing and monitoring workflows
- **State Management**: Maintaining workflow state across service boundaries
- **Event Processing**: Handling events from various services
- **Error Handling**: Managing exceptions and implementing recovery strategies
- **Service Discovery**: Locating and integrating with platform services
- **Correlation Tracking**: Linking related operations across services

## Service Architecture

The Service Integration service is built as a FastAPI application with a layered architecture:

```mermaid
graph TD
    subgraph "API Layer"
        API[API Controllers]
    end
    
    subgraph "Service Layer"
        WDS[Workflow Definition Service]
        WES[Workflow Execution Service]
        SMS[State Management Service]
        EPS[Event Processing Service]
        EHS[Error Handling Service]
        SDS[Service Discovery Service]
    end
    
    subgraph "Repository Layer"
        WDR[Workflow Definition Repository]
        WIR[Workflow Instance Repository]
        WSR[Workflow State Repository]
        EHR[Error History Repository]
        SDR[Service Directory Repository]
    end
    
    subgraph "External Interfaces"
        AO[Agent Orchestrator]
        PC[Project Coordinator]
        PS[Planning System]
        MO[Model Orchestration]
        TI[Tool Integration]
    end
    
    API --> WDS
    API --> WES
    API --> SMS
    API --> EPS
    API --> EHS
    API --> SDS
    
    WDS --> WDR
    WES --> WIR
    SMS --> WSR
    EHS --> EHR
    SDS --> SDR
    
    WES --> AO
    WES --> PC
    WES --> PS
    WES --> MO
    WES --> TI
    
    EPS --> AO
    EPS --> PC
    EPS --> PS
    EPS --> MO
    EPS --> TI
    
    style API fill:#d0e0ff,stroke:#0066cc
    style WDS fill:#ffe0d0,stroke:#cc6600
    style WES fill:#ffe0d0,stroke:#cc6600
    style SMS fill:#ffe0d0,stroke:#cc6600
    style EPS fill:#ffe0d0,stroke:#cc6600
    style EHS fill:#ffe0d0,stroke:#cc6600
    style SDS fill:#ffe0d0,stroke:#cc6600
    style WDR fill:#d0ffd0,stroke:#00cc00
    style WIR fill:#d0ffd0,stroke:#00cc00
    style WSR fill:#d0ffd0,stroke:#00cc00
    style EHR fill:#d0ffd0,stroke:#00cc00
    style SDR fill:#d0ffd0,stroke:#00cc00
    style AO fill:#d0e0ff,stroke:#0066cc
    style PC fill:#d0e0ff,stroke:#0066cc
    style PS fill:#d0e0ff,stroke:#0066cc
    style MO fill:#d0e0ff,stroke:#0066cc
    style TI fill:#d0e0ff,stroke:#0066cc
```

## Data Model

### Core Entities

```mermaid
erDiagram
    WorkflowDefinition ||--o{ WorkflowInstance : instantiated_as
    WorkflowDefinition ||--o{ WorkflowStep : defines
    WorkflowInstance ||--o{ WorkflowExecution : executes
    WorkflowExecution ||--o{ StepExecution : performs
    StepExecution ||--o{ ActivityExecution : consists_of
    WorkflowExecution ||--o{ WorkflowState : records
    
    WorkflowDefinition {
        UUID id
        string name
        string description
        string version
        jsonb definition
        boolean active
        timestamp created_at
        timestamp updated_at
    }
    
    WorkflowStep {
        UUID id
        UUID workflow_definition_id
        string name
        string description
        string step_type
        jsonb configuration
        int sequence
        timestamp created_at
    }
    
    WorkflowInstance {
        UUID id
        UUID workflow_definition_id
        UUID correlation_id
        string name
        string description
        string status
        jsonb context
        timestamp created_at
        timestamp updated_at
        timestamp completed_at
    }
    
    WorkflowExecution {
        UUID id
        UUID workflow_instance_id
        string status
        timestamp started_at
        timestamp completed_at
        jsonb result
        jsonb error_details
    }
    
    StepExecution {
        UUID id
        UUID workflow_execution_id
        UUID step_id
        string status
        int attempt
        timestamp started_at
        timestamp completed_at
        jsonb input
        jsonb output
        jsonb error_details
    }
    
    ActivityExecution {
        UUID id
        UUID step_execution_id
        string activity_type
        string service
        string endpoint
        string status
        timestamp started_at
        timestamp completed_at
        jsonb request
        jsonb response
        jsonb error_details
    }
    
    WorkflowState {
        UUID id
        UUID workflow_execution_id
        jsonb state
        timestamp created_at
    }
```

## API Endpoints

### Workflow Definition Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /workflows | Create workflow definition |
| GET | /workflows | List workflow definitions |
| GET | /workflows/{workflow_id} | Get workflow definition |
| PUT | /workflows/{workflow_id} | Update workflow definition |
| DELETE | /workflows/{workflow_id} | Delete workflow definition |
| POST | /workflows/{workflow_id}/versions | Create new workflow version |
| GET | /workflows/{workflow_id}/versions | List workflow versions |
| POST | /workflows/{workflow_id}/validate | Validate workflow definition |

### Workflow Execution

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /executions | Start workflow execution |
| GET | /executions | List workflow executions |
| GET | /executions/{execution_id} | Get execution details |
| PUT | /executions/{execution_id}/cancel | Cancel execution |
| PUT | /executions/{execution_id}/pause | Pause execution |
| PUT | /executions/{execution_id}/resume | Resume execution |
| GET | /executions/{execution_id}/state | Get execution state |
| GET | /executions/{execution_id}/history | Get execution history |

### Step Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /steps | List steps |
| GET | /steps/{step_id} | Get step details |
| GET | /workflows/{workflow_id}/steps | List steps for workflow |
| GET | /executions/{execution_id}/steps | List steps for execution |
| GET | /executions/{execution_id}/steps/{step_id}/retries | Get step retry history |
| POST | /executions/{execution_id}/steps/{step_id}/retry | Retry failed step |

### Event Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /events | Process event |
| GET | /events | List events |
| GET | /events/{event_id} | Get event details |
| GET | /correlations/{correlation_id}/events | List events by correlation |

### Service Discovery

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /services | List registered services |
| GET | /services/{service_id} | Get service details |
| POST | /services | Register service |
| PUT | /services/{service_id} | Update service |
| DELETE | /services/{service_id} | Deregister service |
| GET | /services/{service_id}/health | Check service health |

## Request/Response Examples

### Create Workflow Definition

Request:

```http
POST /workflows HTTP/1.1
Content-Type: application/json

{
  "name": "Agent Task Execution",
  "description": "Workflow for agent task execution process",
  "version": "1.0.0",
  "definition": {
    "steps": [
      {
        "name": "task_preparation",
        "description": "Prepare task for execution",
        "step_type": "service_call",
        "service": "planning-system",
        "endpoint": "/tasks/{task_id}/prepare",
        "sequence": 1,
        "retry_policy": {
          "max_attempts": 3,
          "backoff_base": 2,
          "backoff_multiplier": 1000
        }
      },
      {
        "name": "agent_assignment",
        "description": "Assign task to agent",
        "step_type": "service_call",
        "service": "agent-orchestrator",
        "endpoint": "/agents/{agent_id}/tasks",
        "sequence": 2,
        "depends_on": ["task_preparation"],
        "retry_policy": {
          "max_attempts": 3,
          "backoff_base": 2,
          "backoff_multiplier": 1000
        }
      },
      {
        "name": "execution_monitoring",
        "description": "Monitor task execution",
        "step_type": "event_wait",
        "event_type": "agent.task_completed",
        "event_filter": {
          "task_id": "${context.task_id}",
          "agent_id": "${context.agent_id}"
        },
        "timeout": 3600000,
        "sequence": 3,
        "depends_on": ["agent_assignment"]
      },
      {
        "name": "result_processing",
        "description": "Process task results",
        "step_type": "service_call",
        "service": "planning-system",
        "endpoint": "/tasks/{task_id}/results",
        "sequence": 4,
        "depends_on": ["execution_monitoring"],
        "retry_policy": {
          "max_attempts": 3,
          "backoff_base": 2,
          "backoff_multiplier": 1000
        }
      }
    ],
    "error_handlers": [
      {
        "step": "agent_assignment",
        "on_error": {
          "action": "retry",
          "max_retries": 3,
          "backoff_seconds": 60
        }
      },
      {
        "step": "execution_monitoring",
        "on_error": {
          "action": "notify",
          "target": "project-coordinator",
          "endpoint": "/projects/{project_id}/notifications"
        }
      }
    ]
  }
}
```

Response:

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": "g1h2i3j4-5k6l-7m8n-9o0p-1q2r3s4t5u6v",
  "name": "Agent Task Execution",
  "description": "Workflow for agent task execution process",
  "version": "1.0.0",
  "definition": {
    "steps": [
      {
        "id": "h1i2j3k4-5l6m-7n8o-9p0q-1r2s3t4u5v6w",
        "name": "task_preparation",
        "description": "Prepare task for execution",
        "step_type": "service_call",
        "service": "planning-system",
        "endpoint": "/tasks/{task_id}/prepare",
        "sequence": 1,
        "retry_policy": {
          "max_attempts": 3,
          "backoff_base": 2,
          "backoff_multiplier": 1000
        }
      },
      // Additional steps omitted for brevity
    ],
    "error_handlers": [
      // Error handlers omitted for brevity
    ]
  },
  "active": true,
  "created_at": "2025-03-29T06:00:00.123456Z",
  "updated_at": "2025-03-29T06:00:00.123456Z"
}
```

### Start Workflow Execution

Request:

```http
POST /executions HTTP/1.1
Content-Type: application/json

{
  "workflow_id": "g1h2i3j4-5k6l-7m8n-9o0p-1q2r3s4t5u6v",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "context": {
    "project_id": "b9a8c7d6-e5f4-4g3h-2i1j-0k9l8m7n6o5p",
    "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
    "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
  }
}
```

Response:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "execution_id": "i1j2k3l4-5m6n-7o8p-9q0r-1s2t3u4v5w6x",
  "workflow_id": "g1h2i3j4-5k6l-7m8n-9o0p-1q2r3s4t5u6v",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "status": "started",
  "started_at": "2025-03-29T06:15:00.123456Z",
  "current_step": "task_preparation",
  "context": {
    "project_id": "b9a8c7d6-e5f4-4g3h-2i1j-0k9l8m7n6o5p",
    "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
    "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
  }
}
```

## Event Publishing

The Service Integration service publishes events to the message queue:

| Event Type | Description | Triggered By |
|------------|-------------|--------------|
| workflow.started | Workflow execution started | Execution start |
| workflow.step_started | Workflow step started | Step start |
| workflow.step_completed | Workflow step completed | Step completion |
| workflow.step_failed | Workflow step failed | Step failure |
| workflow.paused | Workflow execution paused | Execution pause |
| workflow.resumed | Workflow execution resumed | Execution resume |
| workflow.completed | Workflow execution completed | Execution completion |
| workflow.failed | Workflow execution failed | Execution failure |
| workflow.cancelled | Workflow execution cancelled | Execution cancellation |

Example event:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440019",
  "type": "workflow.started",
  "source": "service-integration",
  "timestamp": "2025-03-29T06:15:00.123456Z",
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

## Integration Points

### Agent Orchestrator

- **Agent Task Execution**: Coordinate agent task execution process
- **Agent Collaboration**: Orchestrate agent collaboration workflows
- **Agent Lifecycle**: Manage agent lifecycle events
- **Agent Monitoring**: Track agent activity and status

### Planning System

- **Task Coordination**: Coordinate task assignment and execution
- **Plan Execution**: Orchestrate plan execution across agents
- **Progress Tracking**: Monitor and report on task progress
- **Dependency Management**: Ensure tasks are executed in proper order

### Project Coordinator

- **Project Execution**: Orchestrate project execution workflows
- **Team Coordination**: Coordinate team activities
- **Status Reporting**: Aggregate and report on workflow status
- **Result Aggregation**: Coordinate result collection and processing

### Model Orchestration

- **Model Selection**: Coordinate model selection workflows
- **Execution Monitoring**: Track model execution status
- **Result Processing**: Process and route model outputs
- **Context Management**: Coordinate context sharing between executions

### Tool Integration

- **Tool Selection**: Coordinate tool selection workflows
- **Tool Execution**: Orchestrate tool execution process
- **Result Processing**: Process and route tool outputs
- **Error Handling**: Handle tool execution failures

## Workflow Patterns

The service supports several workflow patterns:

### Sequential Workflow

```mermaid
graph LR
    A[Step 1] --> B[Step 2] --> C[Step 3] --> D[Step 4]
    
    style A fill:#ffe0d0,stroke:#cc6600
    style B fill:#ffe0d0,stroke:#cc6600
    style C fill:#ffe0d0,stroke:#cc6600
    style D fill:#ffe0d0,stroke:#cc6600
```

### Parallel Workflow

```mermaid
graph TD
    A[Start] --> B[Step 1]
    A --> C[Step 2]
    A --> D[Step 3]
    B --> E[Join]
    C --> E
    D --> E
    E --> F[End]
    
    style A fill:#d0e0ff,stroke:#0066cc
    style B fill:#ffe0d0,stroke:#cc6600
    style C fill:#ffe0d0,stroke:#cc6600
    style D fill:#ffe0d0,stroke:#cc6600
    style E fill:#d0e0ff,stroke:#0066cc
    style F fill:#d0e0ff,stroke:#0066cc
```

### Conditional Workflow

```mermaid
graph TD
    A[Start] --> B{Condition}
    B -->|Condition A| C[Path A]
    B -->|Condition B| D[Path B]
    C --> E[Join]
    D --> E
    E --> F[End]
    
    style A fill:#d0e0ff,stroke:#0066cc
    style B fill:#ffffd0,stroke:#cccc00
    style C fill:#ffe0d0,stroke:#cc6600
    style D fill:#ffe0d0,stroke:#cc6600
    style E fill:#d0e0ff,stroke:#0066cc
    style F fill:#d0e0ff,stroke:#0066cc
```

### Event-Based Workflow

```mermaid
graph TD
    A[Start] --> B[Wait for Event 1]
    A --> C[Wait for Event 2]
    B --> D[Event 1 Handler]
    C --> E[Event 2 Handler]
    D --> F[Join]
    E --> F
    F --> G[End]
    
    style A fill:#d0e0ff,stroke:#0066cc
    style B fill:#ffffd0,stroke:#cccc00
    style C fill:#ffffd0,stroke:#cccc00
    style D fill:#ffe0d0,stroke:#cc6600
    style E fill:#ffe0d0,stroke:#cc6600
    style F fill:#d0e0ff,stroke:#0066cc
    style G fill:#d0e0ff,stroke:#0066cc
```

### Error Handling Workflow

```mermaid
graph TD
    A[Start] --> B[Step 1]
    B --> C[Step 2]
    C --> D[Step 3]
    B -->|Error| E[Error Handler 1]
    C -->|Error| F[Error Handler 2]
    D -->|Error| G[Error Handler 3]
    E --> H[Compensation 1]
    F --> I[Compensation 2]
    H --> J[End]
    I --> J
    G --> J
    D --> J
    
    style A fill:#d0e0ff,stroke:#0066cc
    style B fill:#ffe0d0,stroke:#cc6600
    style C fill:#ffe0d0,stroke:#cc6600
    style D fill:#ffe0d0,stroke:#cc6600
    style E fill:#ffd0d0,stroke:#cc0000
    style F fill:#ffd0d0,stroke:#cc0000
    style G fill:#ffd0d0,stroke:#cc0000
    style H fill:#ffffd0,stroke:#cccc00
    style I fill:#ffffd0,stroke:#cccc00
    style J fill:#d0e0ff,stroke:#0066cc
```

## State Management

The service maintains workflow state with the following characteristics:

- **Persistent State**: State is stored in a database
- **Distributed State**: State can be accessed by multiple service instances
- **Event Sourcing**: State changes are recorded as events
- **Consistency**: State is kept consistent across service boundaries
- **Recovery**: State can be reconstructed from event history

### State Machine

Workflow execution follows a state machine pattern:

```mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Running
    Running --> Running: Step Completion
    Running --> Paused: Pause Request
    Paused --> Running: Resume Request
    Running --> Failed: Error
    Failed --> Running: Retry
    Running --> Completed: All Steps Complete
    Paused --> Cancelled: Cancel Request
    Running --> Cancelled: Cancel Request
    Failed --> Cancelled: Cancel Request
    Completed --> [*]
    Cancelled --> [*]
```

## Error Handling Strategies

The service implements several error handling strategies:

- **Retry with Backoff**: Automatically retry failed steps with exponential backoff
- **Circuit Breaker**: Prevent repeated failures to overloaded services
- **Compensation**: Execute compensation steps to undo previous changes
- **Saga Pattern**: Implement distributed transactions with compensation
- **Dead Letter Queue**: Store failed messages for later processing
- **Timeout Handling**: Handle operations that exceed time limits
- **Fallback Mechanisms**: Provide alternative paths for failed operations

## Configuration

Configuration is managed through environment variables:

```python
# Example environment variables
DATABASE_URL=postgresql://user:password@localhost:5432/service_integration
REDIS_URL=redis://localhost:6379
AGENT_ORCHESTRATOR_URL=http://agent-orchestrator:8080
PLANNING_SYSTEM_URL=http://planning-system:8080
PROJECT_COORDINATOR_URL=http://project-coordinator:8080
MODEL_ORCHESTRATION_URL=http://model-orchestration:8080
TOOL_INTEGRATION_URL=http://tool-integration:8080
LOG_LEVEL=INFO
```

## Deployment

The service is deployed as a Docker container:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## Monitoring and Health

### Health Checks

The service provides health check endpoints:

- **GET /health/liveness**: Confirms the service is running
- **GET /health/readiness**: Confirms the service is ready to accept requests
- **GET /health/dependencies**: Checks the status of service dependencies

### Metrics

The service exposes Prometheus metrics at `/metrics`:

- **workflow_execution_count**: Total number of workflow executions
- **workflow_execution_duration_seconds**: Workflow execution time histogram
- **workflow_step_execution_duration_seconds**: Step execution time histogram
- **workflow_error_rate**: Error rate by workflow type
- **step_error_rate**: Error rate by step type
- **workflow_retry_count**: Number of workflow retries
- **api_request_duration_seconds**: API endpoint response times
- **api_request_count**: Count of API requests by endpoint and status

## Common Issues and Troubleshooting

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| Workflow execution failures | Invalid workflow definition, service unavailability | Validate workflow definition, check service health |
| Stuck workflows | Missing events, event delivery failures | Implement timeouts, set up dead letter queues |
| Inconsistent workflow state | Race conditions, concurrent updates | Use optimistic locking, implement event sourcing |
| Performance bottlenecks | Long-running steps, high concurrency | Optimize step execution, implement resource limits |
| Event processing failures | Malformed events, event handling errors | Validate event format, implement error handling |

## Advanced Features

### Workflow Versioning

The service supports workflow versioning to enable safe updates:

- **Multiple Active Versions**: Multiple versions can be active simultaneously
- **Version Selection**: Specific versions can be selected for execution
- **Smooth Transitions**: Running workflows aren't affected by version changes
- **Version History**: Previous versions are maintained for reference

### Dynamic Workflows

The service supports dynamic workflow modification:

- **Dynamic Step Selection**: Steps can be selected based on runtime conditions
- **Dynamic Parameters**: Parameters can be generated dynamically
- **Custom Logic**: Custom logic can be injected into workflows
- **Runtime Adaptation**: Workflows can adapt based on execution context

### Monitoring and Auditing

The service provides extensive monitoring and auditing capabilities:

- **Execution History**: Complete history of workflow executions
- **Step Details**: Detailed information about each step execution
- **Error Analysis**: Comprehensive error information for troubleshooting
- **Performance Metrics**: Metrics for workflow and step performance
- **Audit Logs**: Audit logs for all workflow operations

## References

- [System Overview](../architecture/system-overview.md)
- [Communication Patterns](../architecture/communication-patterns.md)
- [Data Flow](../architecture/data-flow.md)
- [Project Execution](../../guides/process-flows/project-execution.md)
- [Agent Lifecycle](../../guides/process-flows/agent-lifecycle.md)
- [Project Coordinator Service](project-coordinator.md)
- [Agent Orchestrator Service](agent-orchestrator.md)
