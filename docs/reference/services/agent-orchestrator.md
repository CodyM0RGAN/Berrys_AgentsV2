# Agent Orchestrator Service

**Last Modified:** 2025-03-29  
**Completion Date:** 2025-03-29  
**Doc Type:** Reference  

---

## Overview

The Agent Orchestrator service manages the lifecycle of intelligent agents in the Berrys_AgentsV2 platform. It handles agent creation, initialization, state management, task assignment, and termination.

## Service Responsibilities

- **Agent Lifecycle Management**: Creating, initializing, and terminating agents
- **State Management**: Tracking and updating agent states
- **Template Management**: Managing agent templates and specializations
- **Task Assignment**: Assigning tasks to agents and tracking execution
- **Agent Coordination**: Facilitating agent collaboration
- **Resource Management**: Optimizing agent resource utilization

## Service Architecture

The Agent Orchestrator is built as a FastAPI application with a layered architecture:

```mermaid
graph TD
    subgraph "API Layer"
        API[API Controllers]
    end
    
    subgraph "Service Layer"
        ALS[Agent Lifecycle Service]
        ATS[Agent Template Service]
        ASS[Agent Specialization Service]
        ACS[Agent Collaboration Service]
        AMS[Agent Monitoring Service]
    end
    
    subgraph "Repository Layer"
        AR[Agent Repository]
        ATR[Agent Template Repository]
        ASR[Agent State Repository]
        ASP[Agent Specialization Repository]
    end
    
    subgraph "External Interfaces"
        MO[Model Orchestration]
        TI[Tool Integration]
        PS[Planning System]
        PC[Project Coordinator]
    end
    
    API --> ALS
    API --> ATS
    API --> ASS
    API --> ACS
    API --> AMS
    
    ALS --> AR
    ALS --> ASR
    ATS --> ATR
    ASS --> ASP
    ACS --> AR
    AMS --> AR
    AMS --> ASR
    
    ALS --> MO
    ALS --> TI
    ALS --> PS
    ALS --> PC
    
    style API fill:#d0e0ff,stroke:#0066cc
    style ALS fill:#ffe0d0,stroke:#cc6600
    style ATS fill:#ffe0d0,stroke:#cc6600
    style ASS fill:#ffe0d0,stroke:#cc6600
    style ACS fill:#ffe0d0,stroke:#cc6600
    style AMS fill:#ffe0d0,stroke:#cc6600
    style AR fill:#d0ffd0,stroke:#00cc00
    style ATR fill:#d0ffd0,stroke:#00cc00
    style ASR fill:#d0ffd0,stroke:#00cc00
    style ASP fill:#d0ffd0,stroke:#00cc00
    style MO fill:#d0e0ff,stroke:#0066cc
    style TI fill:#d0e0ff,stroke:#0066cc
    style PS fill:#d0e0ff,stroke:#0066cc
    style PC fill:#d0e0ff,stroke:#0066cc
```

## Data Model

### Core Entities

```mermaid
erDiagram
    Agent ||--o{ AgentState : has
    Agent }o--|| AgentTemplate : based_on
    Agent ||--o{ AgentSpecialization : has
    Agent ||--o{ AgentTask : executes
    
    Agent {
        UUID id
        string name
        string description
        UUID template_id
        string state
        jsonb state_detail
        timestamp created_at
        timestamp updated_at
        timestamp last_active_at
    }
    
    AgentState {
        UUID id
        UUID agent_id
        string previous_state
        string new_state
        string transition_reason
        timestamp created_at
    }
    
    AgentTemplate {
        UUID id
        string name
        string description
        jsonb parameters
        jsonb capabilities
        timestamp created_at
        timestamp updated_at
    }
    
    AgentSpecialization {
        UUID id
        UUID agent_id
        string name
        jsonb capabilities
        jsonb configuration
        timestamp created_at
    }
    
    AgentTask {
        UUID id
        UUID agent_id
        UUID task_id
        string status
        timestamp assigned_at
        timestamp completed_at
        jsonb results
    }
```

### State Transitions

Agent state transitions follow this pattern:

```mermaid
stateDiagram-v2
    [*] --> Creating
    Creating --> Initializing
    Initializing --> Ready
    Ready --> Active
    Active --> Ready
    Active --> Paused
    Paused --> Active
    Paused --> Ready
    Ready --> Terminating
    Active --> Terminating
    Paused --> Terminating
    Terminating --> [*]
```

## API Endpoints

### Agent Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /agents | List all agents |
| GET | /agents/{agent_id} | Get agent details |
| POST | /agents | Create new agent |
| PUT | /agents/{agent_id} | Update agent |
| DELETE | /agents/{agent_id} | Delete/terminate agent |
| GET | /agents/{agent_id}/state | Get agent state |
| PUT | /agents/{agent_id}/state | Change agent state |
| GET | /agents/{agent_id}/state/history | Get agent state history |

### Template Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /templates | List all agent templates |
| GET | /templates/{template_id} | Get template details |
| POST | /templates | Create new template |
| PUT | /templates/{template_id} | Update template |
| DELETE | /templates/{template_id} | Delete template |

### Specialization Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /specializations | List all specializations |
| GET | /specializations/{specialization_id} | Get specialization details |
| POST | /specializations | Create new specialization |
| PUT | /specializations/{specialization_id} | Update specialization |
| DELETE | /specializations/{specialization_id} | Delete specialization |
| GET | /agents/{agent_id}/specializations | Get agent specializations |
| POST | /agents/{agent_id}/specializations | Add specialization to agent |
| DELETE | /agents/{agent_id}/specializations/{specialization_id} | Remove specialization from agent |

### Task Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /agents/{agent_id}/tasks | List agent tasks |
| GET | /agents/{agent_id}/tasks/{task_id} | Get task details |
| POST | /agents/{agent_id}/tasks | Assign task to agent |
| PUT | /agents/{agent_id}/tasks/{task_id}/status | Update task status |
| DELETE | /agents/{agent_id}/tasks/{task_id} | Unassign task |

## Request/Response Examples

### Create Agent

Request:

```http
POST /agents HTTP/1.1
Content-Type: application/json

{
  "name": "Data Analysis Agent",
  "template_id": "550e8400-e29b-41d4-a716-446655440000",
  "description": "Agent specialized for data analysis tasks",
  "specializations": ["data_analysis", "visualization"],
  "configuration": {
    "max_concurrent_tasks": 3,
    "preferred_model": "gpt-4"
  }
}
```

Response:

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "name": "Data Analysis Agent",
  "description": "Agent specialized for data analysis tasks",
  "template_id": "550e8400-e29b-41d4-a716-446655440000",
  "state": "initializing",
  "specializations": [
    {
      "id": "a1b2c3d4-e5f6-4a2b-8c7d-6e5f4a3b2c1d",
      "name": "data_analysis",
      "capabilities": {
        "data_formats": ["csv", "json", "parquet"],
        "analysis_types": ["statistical", "trend", "correlation"]
      }
    },
    {
      "id": "b2c3d4e5-f6a7-5b3c-9d8e-7f6g5h4i3j2k",
      "name": "visualization",
      "capabilities": {
        "chart_types": ["bar", "line", "scatter", "pie"],
        "libraries": ["matplotlib", "seaborn", "plotly"]
      }
    }
  ],
  "configuration": {
    "max_concurrent_tasks": 3,
    "preferred_model": "gpt-4"
  },
  "created_at": "2025-03-29T05:43:21.123456Z",
  "updated_at": "2025-03-29T05:43:21.123456Z"
}
```

### Assign Task to Agent

Request:

```http
POST /agents/f47ac10b-58cc-4372-a567-0e02b2c3d479/tasks HTTP/1.1
Content-Type: application/json

{
  "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
  "priority": "high",
  "context": {
    "title": "Analyze Customer Data",
    "description": "Analyze the customer dataset for purchasing patterns and create visualizations",
    "inputs": [
      {
        "name": "customer_data.csv",
        "location": "s3://data-bucket/customer_data.csv",
        "type": "dataset"
      }
    ],
    "expected_outputs": [
      {
        "name": "analysis_report.md",
        "description": "Markdown report with findings"
      },
      {
        "name": "visualizations.pdf",
        "description": "PDF with key visualizations"
      }
    ]
  }
}
```

Response:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
  "status": "assigned",
  "assigned_at": "2025-03-29T05:45:05.123456Z",
  "estimated_completion": "2025-03-29T06:45:05.123456Z"
}
```

## Event Publishing

The Agent Orchestrator publishes events to the message queue:

| Event Type | Description | Triggered By |
|------------|-------------|--------------|
| agent.created | New agent created | Successful agent creation |
| agent.initialized | Agent initialization completed | Agent initialization |
| agent.state_changed | Agent state change | Any state transition |
| agent.task_assigned | Task assigned to agent | Task assignment |
| agent.task_completed | Agent completed task | Task completion |
| agent.task_failed | Agent failed to complete task | Task failure |
| agent.terminated | Agent terminated | Agent termination |

Example event:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "agent.created",
  "source": "agent-orchestrator",
  "timestamp": "2025-03-29T05:43:21.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "Data Analysis Agent",
    "template_id": "550e8400-e29b-41d4-a716-446655440000",
    "specializations": ["data_analysis", "visualization"],
    "state": "initializing"
  }
}
```

## Integration Points

### Model Orchestration Service

- **Initialize Agent**: Configure and initialize agent model
- **Execute Agent Logic**: Process tasks and generate outputs
- **Release Resources**: Release model resources on agent termination

### Tool Integration Service

- **Tool Discovery**: Discover tools available to agent
- **Tool Execution**: Execute tools on behalf of agent
- **Tool Result Processing**: Process tool execution results

### Planning System

- **Task Assignment**: Receive tasks from Planning System
- **Task Status Updates**: Provide task status updates
- **Agent Capability Discovery**: Share agent capabilities for planning

### Project Coordinator

- **Agent Team Assembly**: Participate in team assembly
- **Project Context Sharing**: Receive project context
- **Result Aggregation**: Share task results for aggregation

## Configuration

Configuration is managed through environment variables:

```python
# Example environment variables
DATABASE_URL=postgresql://user:password@localhost:5432/agent_orchestrator
REDIS_URL=redis://localhost:6379
MODEL_ORCHESTRATION_URL=http://model-orchestration:8080
TOOL_INTEGRATION_URL=http://tool-integration:8080
PLANNING_SYSTEM_URL=http://planning-system:8080
PROJECT_COORDINATOR_URL=http://project-coordinator:8080
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

- **agent_count**: Total number of agents
- **agent_state_count**: Count of agents by state
- **agent_task_count**: Count of assigned tasks
- **agent_creation_duration_seconds**: Time to create agents
- **agent_task_completion_duration_seconds**: Time to complete tasks
- **api_request_duration_seconds**: API endpoint response times
- **api_request_count**: Count of API requests by endpoint and status

## Common Issues and Troubleshooting

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| Agent creation failure | Template not found, invalid specializations | Verify template exists, check specialization validity |
| Agent initialization timeout | Model service unavailable, complex initialization | Check model service health, increase timeout, simplify initialization |
| Task assignment failure | Agent not in ready state, incompatible task | Check agent state, verify task compatibility with agent |
| Database connection errors | Invalid connection string, network issues | Verify connection string, check network connectivity |
| High memory usage | Too many concurrent agents, memory leaks | Limit concurrent agents, check for memory leaks |

## References

- [Agent Lifecycle](../../guides/process-flows/agent-lifecycle.md)
- [Project Execution](../../guides/process-flows/project-execution.md)
- [System Overview](../architecture/system-overview.md)
- [Message Contracts](../message-contracts.md)
- [Database Schema](../database-schema.md)
