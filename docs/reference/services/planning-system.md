# Planning System Service

**Last Modified:** 2025-03-29  
**Completion Date:** 2025-03-29  
**Doc Type:** Reference  

---

## Overview

The Planning System service handles project planning, task decomposition, and execution coordination in the Berrys_AgentsV2 platform. It analyzes project requirements, breaks them down into manageable tasks, establishes dependencies, and coordinates task execution across agents.

## Service Responsibilities

- **Project Planning**: Analyzing project requirements and creating execution plans
- **Task Decomposition**: Breaking down projects into discrete, manageable tasks
- **Dependency Management**: Establishing and tracking task dependencies
- **Task Assignment**: Matching tasks to appropriate agents
- **Progress Tracking**: Monitoring task and project execution progress
- **Plan Adjustment**: Adapting plans based on execution feedback
- **Resource Allocation**: Optimizing the use of available agents and resources

## Service Architecture

The Planning System is built as a FastAPI application with a layered architecture:

```mermaid
graph TD
    subgraph "API Layer"
        API[API Controllers]
    end
    
    subgraph "Service Layer"
        PPS[Project Planning Service]
        TDS[Task Decomposition Service]
        DMS[Dependency Management Service]
        TAS[Task Assignment Service]
        PTS[Progress Tracking Service]
        PAS[Plan Adjustment Service]
    end
    
    subgraph "Repository Layer"
        PR[Project Repository]
        TR[Task Repository]
        DR[Dependency Repository]
        AR[Assignment Repository]
    end
    
    subgraph "External Interfaces"
        PC[Project Coordinator]
        AO[Agent Orchestrator]
        MO[Model Orchestration]
    end
    
    API --> PPS
    API --> TDS
    API --> DMS
    API --> TAS
    API --> PTS
    API --> PAS
    
    PPS --> PR
    TDS --> TR
    DMS --> DR
    TAS --> AR
    PTS --> TR
    PTS --> AR
    PAS --> PR
    PAS --> TR
    PAS --> DR
    
    PPS --> MO
    TDS --> MO
    DMS --> MO
    TAS --> AO
    
    PC --> API
    
    style API fill:#d0e0ff,stroke:#0066cc
    style PPS fill:#ffe0d0,stroke:#cc6600
    style TDS fill:#ffe0d0,stroke:#cc6600
    style DMS fill:#ffe0d0,stroke:#cc6600
    style TAS fill:#ffe0d0,stroke:#cc6600
    style PTS fill:#ffe0d0,stroke:#cc6600
    style PAS fill:#ffe0d0,stroke:#cc6600
    style PR fill:#d0ffd0,stroke:#00cc00
    style TR fill:#d0ffd0,stroke:#00cc00
    style DR fill:#d0ffd0,stroke:#00cc00
    style AR fill:#d0ffd0,stroke:#00cc00
    style PC fill:#d0e0ff,stroke:#0066cc
    style AO fill:#d0e0ff,stroke:#0066cc
    style MO fill:#d0e0ff,stroke:#0066cc
```

## Data Model

### Core Entities

```mermaid
erDiagram
    Project ||--o{ Task : contains
    Task ||--o{ TaskDependency : has
    Task ||--o{ TaskAssignment : assigned_via
    Agent ||--o{ TaskAssignment : works_on
    Task ||--o{ TaskProgress : tracks
    
    Project {
        UUID id
        UUID external_id
        string name
        string description
        string status
        jsonb requirements
        jsonb objectives
        jsonb constraints
        jsonb preferences
        timestamp deadline
        timestamp created_at
        timestamp updated_at
    }
    
    Task {
        UUID id
        UUID project_id
        UUID parent_task_id
        string title
        string description
        string status
        int priority
        string task_type
        jsonb requirements
        jsonb expected_outputs
        float estimated_duration
        timestamp deadline
        timestamp created_at
        timestamp updated_at
    }
    
    TaskDependency {
        UUID id
        UUID task_id
        UUID depends_on_task_id
        string dependency_type
        jsonb conditions
        timestamp created_at
    }
    
    TaskAssignment {
        UUID id
        UUID task_id
        UUID agent_id
        string status
        timestamp assigned_at
        timestamp started_at
        timestamp completed_at
    }
    
    TaskProgress {
        UUID id
        UUID task_id
        int percentage_complete
        string status_detail
        jsonb milestones
        timestamp reported_at
    }
```

## API Endpoints

### Project Planning

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /projects | Create project plan |
| GET | /projects | List projects |
| GET | /projects/{project_id} | Get project details |
| PUT | /projects/{project_id} | Update project |
| DELETE | /projects/{project_id} | Delete project |
| GET | /projects/{project_id}/plan | Get project execution plan |
| PUT | /projects/{project_id}/plan | Update project execution plan |

### Task Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /tasks | List tasks |
| GET | /tasks/{task_id} | Get task details |
| POST | /tasks | Create task |
| PUT | /tasks/{task_id} | Update task |
| DELETE | /tasks/{task_id} | Delete task |
| GET | /projects/{project_id}/tasks | List tasks for project |
| GET | /tasks/{task_id}/dependencies | Get task dependencies |
| POST | /tasks/{task_id}/dependencies | Add task dependency |
| DELETE | /tasks/{task_id}/dependencies/{dependency_id} | Remove task dependency |

### Task Assignment

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /tasks/{task_id}/assign | Assign task to agent |
| GET | /tasks/{task_id}/assignments | Get task assignments |
| DELETE | /tasks/{task_id}/assignments/{assignment_id} | Remove task assignment |
| GET | /agents/{agent_id}/assignments | Get agent assignments |
| POST | /projects/{project_id}/assign | Batch assign project tasks |

### Progress Tracking

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /projects/{project_id}/progress | Get project progress |
| GET | /tasks/{task_id}/progress | Get task progress |
| POST | /tasks/{task_id}/progress | Update task progress |
| GET | /projects/{project_id}/status | Get project status |
| PUT | /tasks/{task_id}/status | Update task status |

## Request/Response Examples

### Create Project Plan

Request:

```http
POST /projects HTTP/1.1
Content-Type: application/json

{
  "external_id": "b9a8c7d6-e5f4-4g3h-2i1j-0k9l8m7n6o5p",
  "name": "Customer Data Analysis",
  "description": "Analyze customer data for purchasing patterns and create visualizations",
  "objectives": [
    "Identify key customer segments",
    "Analyze purchasing patterns",
    "Create visualizations of findings",
    "Generate recommendations"
  ],
  "requirements": {
    "data_sources": [
      {
        "name": "customer_data.csv",
        "type": "dataset",
        "location": "s3://data-bucket/customer_data.csv"
      }
    ],
    "deliverables": [
      {
        "name": "analysis_report.md",
        "description": "Markdown report with findings",
        "required": true
      },
      {
        "name": "visualizations.pdf",
        "description": "PDF with key visualizations",
        "required": true
      }
    ]
  },
  "constraints": {
    "deadline": "2025-04-15T00:00:00Z",
    "max_agents": 3
  },
  "preferences": {
    "agent_types": ["data_analysis", "visualization"],
    "output_formats": ["markdown", "pdf"]
  }
}
```

Response:

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": "c1d2e3f4-5g6h-7i8j-9k0l-1m2n3o4p5q6r",
  "external_id": "b9a8c7d6-e5f4-4g3h-2i1j-0k9l8m7n6o5p",
  "name": "Customer Data Analysis",
  "description": "Analyze customer data for purchasing patterns and create visualizations",
  "status": "planning",
  "objectives": [
    "Identify key customer segments",
    "Analyze purchasing patterns",
    "Create visualizations of findings",
    "Generate recommendations"
  ],
  "requirements": {
    "data_sources": [
      {
        "name": "customer_data.csv",
        "type": "dataset",
        "location": "s3://data-bucket/customer_data.csv"
      }
    ],
    "deliverables": [
      {
        "name": "analysis_report.md",
        "description": "Markdown report with findings",
        "required": true
      },
      {
        "name": "visualizations.pdf",
        "description": "PDF with key visualizations",
        "required": true
      }
    ]
  },
  "constraints": {
    "deadline": "2025-04-15T00:00:00Z",
    "max_agents": 3
  },
  "preferences": {
    "agent_types": ["data_analysis", "visualization"],
    "output_formats": ["markdown", "pdf"]
  },
  "created_at": "2025-03-29T06:30:00.123456Z",
  "updated_at": "2025-03-29T06:30:00.123456Z",
  "tasks": [
    {
      "id": "d1e2f3g4-5h6i-7j8k-9l0m-1n2o3p4q5r6s",
      "title": "Data Preparation",
      "description": "Clean and prepare customer data for analysis",
      "status": "pending",
      "priority": 1,
      "task_type": "data_processing",
      "deadline": "2025-04-05T00:00:00Z"
    },
    {
      "id": "e2f3g4h5-6i7j-8k9l-0m1n-2o3p4q5r6s7t",
      "title": "Customer Segmentation Analysis",
      "description": "Identify key customer segments based on purchasing behavior",
      "status": "pending",
      "priority": 2,
      "task_type": "analysis",
      "deadline": "2025-04-08T00:00:00Z"
    },
    {
      "id": "f3g4h5i6-7j8k-9l0m-1n2o-3p4q5r6s7t8u",
      "title": "Purchasing Pattern Analysis",
      "description": "Analyze patterns in customer purchasing behavior",
      "status": "pending",
      "priority": 2,
      "task_type": "analysis",
      "deadline": "2025-04-10T00:00:00Z"
    },
    {
      "id": "g4h5i6j7-8k9l-0m1n-2o3p-4q5r6s7t8u9v",
      "title": "Data Visualization",
      "description": "Create visualizations of customer segments and purchasing patterns",
      "status": "pending",
      "priority": 3,
      "task_type": "visualization",
      "deadline": "2025-04-12T00:00:00Z"
    },
    {
      "id": "h5i6j7k8-9l0m-1n2o-3p4q-5r6s7t8u9v0w",
      "title": "Report Generation",
      "description": "Compile findings into final report with recommendations",
      "status": "pending",
      "priority": 4,
      "task_type": "reporting",
      "deadline": "2025-04-14T00:00:00Z"
    }
  ],
  "dependencies": [
    {
      "task_id": "e2f3g4h5-6i7j-8k9l-0m1n-2o3p4q5r6s7t",
      "depends_on_task_id": "d1e2f3g4-5h6i-7j8k-9l0m-1n2o3p4q5r6s",
      "dependency_type": "completion"
    },
    {
      "task_id": "f3g4h5i6-7j8k-9l0m-1n2o-3p4q5r6s7t8u",
      "depends_on_task_id": "d1e2f3g4-5h6i-7j8k-9l0m-1n2o3p4q5r6s",
      "dependency_type": "completion"
    },
    {
      "task_id": "g4h5i6j7-8k9l-0m1n-2o3p-4q5r6s7t8u9v",
      "depends_on_task_id": "e2f3g4h5-6i7j-8k9l-0m1n-2o3p4q5r6s7t",
      "dependency_type": "completion"
    },
    {
      "task_id": "g4h5i6j7-8k9l-0m1n-2o3p-4q5r6s7t8u9v",
      "depends_on_task_id": "f3g4h5i6-7j8k-9l0m-1n2o-3p4q5r6s7t8u",
      "dependency_type": "completion"
    },
    {
      "task_id": "h5i6j7k8-9l0m-1n2o-3p4q-5r6s7t8u9v0w",
      "depends_on_task_id": "g4h5i6j7-8k9l-0m1n-2o3p-4q5r6s7t8u9v",
      "dependency_type": "completion"
    }
  ]
}
```

### Assign Task

Request:

```http
POST /tasks/e2f3g4h5-6i7j-8k9l-0m1n-2o3p4q5r6s7t/assign HTTP/1.1
Content-Type: application/json

{
  "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "priority": "high",
  "context": {
    "previous_task_outputs": [
      {
        "task_id": "d1e2f3g4-5h6i-7j8k-9l0m-1n2o3p4q5r6s",
        "output_location": "s3://results-bucket/task-results/d1e2f3g4-5h6i-7j8k-9l0m-1n2o3p4q5r6s/cleaned_data.csv"
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
  "assignment_id": "i6j7k8l9-0m1n-2o3p-4q5r-6s7t8u9v0w1x",
  "task_id": "e2f3g4h5-6i7j-8k9l-0m1n-2o3p4q5r6s7t",
  "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "assigned",
  "assigned_at": "2025-03-29T06:45:00.123456Z",
  "estimated_start": "2025-03-29T06:45:05.123456Z",
  "estimated_completion": "2025-03-29T07:15:00.123456Z"
}
```

## Event Publishing

The Planning System publishes events to the message queue:

| Event Type | Description | Triggered By |
|------------|-------------|--------------|
| project.created | New project created | Project creation |
| project.updated | Project updated | Project update |
| project.planning_started | Project planning started | Planning initiation |
| project.planning_completed | Project planning completed | Planning completion |
| task.created | New task created | Task creation |
| task.updated | Task updated | Task update |
| task.assigned | Task assigned to agent | Task assignment |
| task.started | Task execution started | Task start |
| task.status_changed | Task status changed | Status update |
| task.completed | Task completed | Task completion |

Example event:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440010",
  "type": "task.created",
  "source": "planning-system",
  "timestamp": "2025-03-29T06:30:05.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "task_id": "d1e2f3g4-5h6i-7j8k-9l0m-1n2o3p4q5r6s",
    "project_id": "c1d2e3f4-5g6h-7i8j-9k0l-1m2n3o4p5q6r",
    "title": "Data Preparation",
    "description": "Clean and prepare customer data for analysis",
    "status": "pending",
    "priority": 1,
    "task_type": "data_processing",
    "deadline": "2025-04-05T00:00:00Z"
  }
}
```

## Integration Points

### Project Coordinator

- **Project Initialization**: Receive project details for planning
- **Plan Communication**: Send completed project plans
- **Status Updates**: Report on project and task progress
- **Result Integration**: Coordinate task result integration

### Agent Orchestrator

- **Agent Capabilities**: Retrieve agent capabilities for task matching
- **Task Assignment**: Assign tasks to agents
- **Task Status**: Receive task execution status updates
- **Agent Feedback**: Process agent feedback for plan adjustments

### Model Orchestration

- **Plan Generation**: Leverage AI models for plan generation
- **Task Decomposition**: Use AI to break down complex tasks
- **Dependency Analysis**: Identify logical dependencies between tasks
- **Resource Optimization**: Optimize resource allocation

## Planning Strategies

The service implements several planning strategies:

### Task Decomposition

Tasks are broken down using several approaches:

1. **Goal-Based Decomposition**: Break down based on project objectives
2. **Capability-Based Decomposition**: Break down based on required capabilities
3. **Temporal Decomposition**: Break down based on timeline requirements
4. **Resource-Based Decomposition**: Break down based on available resources
5. **Domain-Specific Decomposition**: Use domain knowledge for specialized breakdown

### Dependency Analysis

Task dependencies are established using:

1. **Completion Dependencies**: Task requires completion of another task
2. **Input Dependencies**: Task requires outputs from another task
3. **Resource Dependencies**: Tasks compete for the same resources
4. **Conditional Dependencies**: Task depends on conditions from another task
5. **Temporal Dependencies**: Tasks must occur in specific time relation

### Task Prioritization

Tasks are prioritized based on:

1. **Critical Path Analysis**: Identify tasks on the critical path
2. **Deadline Proximity**: Prioritize tasks with nearer deadlines
3. **Dependency Count**: Consider number of dependent tasks
4. **Value Assessment**: Evaluate business value of task outputs
5. **Resource Availability**: Consider resource constraints

## Configuration

Configuration is managed through environment variables:

```python
# Example environment variables
DATABASE_URL=postgresql://user:password@localhost:5432/planning_system
REDIS_URL=redis://localhost:6379
MODEL_ORCHESTRATION_URL=http://model-orchestration:8080
AGENT_ORCHESTRATOR_URL=http://agent-orchestrator:8080
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

- **project_count**: Total number of projects
- **task_count**: Total number of tasks
- **task_completion_rate**: Percentage of tasks successfully completed
- **planning_duration_seconds**: Time to generate project plans
- **assignment_duration_seconds**: Time to assign tasks
- **api_request_duration_seconds**: API endpoint response times
- **api_request_count**: Count of API requests by endpoint and status

## Common Issues and Troubleshooting

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| Plan generation failures | Invalid project requirements, model service unavailable | Validate requirements, check model service health |
| Task dependency cycles | Circular dependencies in task definitions | Detect and break dependency cycles, enforce DAG validation |
| Resource overallocation | Too many concurrent tasks for available agents | Implement resource capacity planning, adjust task priorities |
| Task assignment failures | Incompatible agent capabilities, agent unavailability | Verify capability requirements, implement fallback assignments |
| Missed deadlines | Inaccurate duration estimates, unexpected blockers | Improve estimation methods, add buffer time, monitor critical path |

## Performance Considerations

- **Plan Generation**: Complex plans are generated asynchronously with status polling
- **Dependency Resolution**: Dependency graphs are cached for efficient traversal
- **Task Assignment**: Batch assignment operations for efficient resource allocation
- **Progress Updates**: Progress updates are batched to reduce message volume
- **Status Propagation**: Status changes are propagated through dependency hierarchy

## References

- [System Overview](../architecture/system-overview.md)
- [Agent Lifecycle](../../guides/process-flows/agent-lifecycle.md)
- [Project Execution](../../guides/process-flows/project-execution.md)
- [Agent Orchestrator Service](agent-orchestrator.md)
- [Model Orchestration Service](model-orchestration.md)
