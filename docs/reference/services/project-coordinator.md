# Project Coordinator Service

**Last Modified:** 2025-03-29  
**Completion Date:** 2025-03-29  
**Doc Type:** Reference  

---

## Overview

The Project Coordinator service manages the overall lifecycle of projects in the Berrys_AgentsV2 platform. It handles project creation, coordination, execution tracking, and result aggregation. The service acts as a central orchestrator that connects various services to achieve project objectives.

## Service Responsibilities

- **Project Management**: Creating and managing project metadata and status
- **Planning Coordination**: Initiating and monitoring the planning process
- **Team Assembly**: Coordinating the formation of agent teams
- **Execution Coordination**: Overseeing project execution across services
- **Result Aggregation**: Collecting and organizing project outputs
- **Status Reporting**: Providing project status and progress information
- **Resource Management**: Allocating and tracking project resources

## Service Architecture

The Project Coordinator is built as a FastAPI application with a layered architecture:

```mermaid
graph TD
    subgraph "API Layer"
        API[API Controllers]
    end
    
    subgraph "Service Layer"
        PMS[Project Management Service]
        PCS[Planning Coordination Service]
        TAS[Team Assembly Service]
        ECS[Execution Coordination Service]
        RAS[Result Aggregation Service]
        SRS[Status Reporting Service]
    end
    
    subgraph "Repository Layer"
        PR[Project Repository]
        TR[Team Repository]
        RR[Results Repository]
        SR[Status Repository]
    end
    
    subgraph "External Interfaces"
        WD[Web Dashboard]
        PS[Planning System]
        AO[Agent Orchestrator]
        SI[Service Integration]
    end
    
    API --> PMS
    API --> PCS
    API --> TAS
    API --> ECS
    API --> RAS
    API --> SRS
    
    PMS --> PR
    TAS --> TR
    ECS --> PR
    RAS --> RR
    SRS --> SR
    
    PMS --> PS
    PCS --> PS
    TAS --> AO
    ECS --> SI
    RAS --> SI
    
    WD --> API
    
    style API fill:#d0e0ff,stroke:#0066cc
    style PMS fill:#ffe0d0,stroke:#cc6600
    style PCS fill:#ffe0d0,stroke:#cc6600
    style TAS fill:#ffe0d0,stroke:#cc6600
    style ECS fill:#ffe0d0,stroke:#cc6600
    style RAS fill:#ffe0d0,stroke:#cc6600
    style SRS fill:#ffe0d0,stroke:#cc6600
    style PR fill:#d0ffd0,stroke:#00cc00
    style TR fill:#d0ffd0,stroke:#00cc00
    style RR fill:#d0ffd0,stroke:#00cc00
    style SR fill:#d0ffd0,stroke:#00cc00
    style WD fill:#d0e0ff,stroke:#0066cc
    style PS fill:#d0e0ff,stroke:#0066cc
    style AO fill:#d0e0ff,stroke:#0066cc
    style SI fill:#d0e0ff,stroke:#0066cc
```

## Data Model

### Core Entities

```mermaid
erDiagram
    Project ||--o{ ProjectTeam : has
    Project ||--o{ ProjectPlan : has
    Project ||--o{ ProjectStatus : tracks
    Project ||--o{ ProjectResult : produces
    ProjectTeam ||--o{ TeamMember : includes
    Agent ||--o{ TeamMember : serves_as
    
    Project {
        UUID id
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
        UUID created_by
    }
    
    ProjectTeam {
        UUID id
        UUID project_id
        string name
        string description
        string status
        timestamp created_at
        timestamp updated_at
    }
    
    TeamMember {
        UUID id
        UUID team_id
        UUID agent_id
        string role
        string status
        timestamp joined_at
        timestamp left_at
    }
    
    ProjectPlan {
        UUID id
        UUID project_id
        UUID planning_system_id
        string status
        jsonb plan_data
        timestamp created_at
        timestamp updated_at
    }
    
    ProjectStatus {
        UUID id
        UUID project_id
        string status
        int completion_percentage
        jsonb milestone_status
        string status_detail
        timestamp reported_at
    }
    
    ProjectResult {
        UUID id
        UUID project_id
        string name
        string description
        string type
        string location
        jsonb metadata
        timestamp created_at
    }
```

## API Endpoints

### Project Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /projects | Create project |
| GET | /projects | List projects |
| GET | /projects/{project_id} | Get project details |
| PUT | /projects/{project_id} | Update project |
| DELETE | /projects/{project_id} | Delete project |
| PUT | /projects/{project_id}/status | Update project status |
| GET | /projects/{project_id}/status/history | Get project status history |

### Team Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /projects/{project_id}/teams | Create team |
| GET | /projects/{project_id}/teams | List teams for project |
| GET | /teams/{team_id} | Get team details |
| PUT | /teams/{team_id} | Update team |
| DELETE | /teams/{team_id} | Delete team |
| POST | /teams/{team_id}/members | Add team member |
| DELETE | /teams/{team_id}/members/{member_id} | Remove team member |
| GET | /teams/{team_id}/members | List team members |

### Planning Coordination

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /projects/{project_id}/planning | Initiate planning |
| GET | /projects/{project_id}/planning/status | Get planning status |
| PUT | /projects/{project_id}/planning/cancel | Cancel planning |
| GET | /projects/{project_id}/plans | Get project plans |
| PUT | /projects/{project_id}/plans/{plan_id}/approve | Approve plan |
| PUT | /projects/{project_id}/plans/{plan_id}/reject | Reject plan |

### Execution Coordination

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /projects/{project_id}/execution | Start execution |
| PUT | /projects/{project_id}/execution/pause | Pause execution |
| PUT | /projects/{project_id}/execution/resume | Resume execution |
| PUT | /projects/{project_id}/execution/cancel | Cancel execution |
| GET | /projects/{project_id}/execution/status | Get execution status |
| GET | /projects/{project_id}/milestones | Get project milestones |
| PUT | /projects/{project_id}/milestones/{milestone_id}/status | Update milestone status |

### Result Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /projects/{project_id}/results | Add project result |
| GET | /projects/{project_id}/results | Get project results |
| GET | /projects/{project_id}/results/{result_id} | Get result details |
| DELETE | /projects/{project_id}/results/{result_id} | Delete result |
| POST | /projects/{project_id}/results/aggregate | Aggregate project results |
| GET | /projects/{project_id}/summary | Get project summary |

## Request/Response Examples

### Create Project

Request:

```http
POST /projects HTTP/1.1
Content-Type: application/json

{
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
  "id": "b9a8c7d6-e5f4-4g3h-2i1j-0k9l8m7n6o5p",
  "name": "Customer Data Analysis",
  "description": "Analyze customer data for purchasing patterns and create visualizations",
  "status": "created",
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
  "created_at": "2025-03-29T06:00:00.123456Z",
  "updated_at": "2025-03-29T06:00:00.123456Z",
  "created_by": "user-123"
}
```

### Start Project Execution

Request:

```http
POST /projects/b9a8c7d6-e5f4-4g3h-2i1j-0k9l8m7n6o5p/execution HTTP/1.1
Content-Type: application/json

{
  "plan_id": "c1d2e3f4-5g6h-7i8j-9k0l-1m2n3o4p5q6r",
  "team_id": "d1e2f3g4-5h6i-7j8k-9l0m-1n2o3p4q5r6s",
  "execution_parameters": {
    "priority": "normal",
    "execution_mode": "sequential",
    "monitoring_level": "detailed"
  }
}
```

Response:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "execution_id": "e1f2g3h4-5i6j-7k8l-9m0n-1o2p3q4r5s6t",
  "project_id": "b9a8c7d6-e5f4-4g3h-2i1j-0k9l8m7n6o5p",
  "plan_id": "c1d2e3f4-5g6h-7i8j-9k0l-1m2n3o4p5q6r",
  "team_id": "d1e2f3g4-5h6i-7j8k-9l0m-1n2o3p4q5r6s",
  "status": "started",
  "started_at": "2025-03-29T06:30:00.123456Z",
  "estimated_completion": "2025-04-14T18:00:00.000000Z",
  "first_tasks": [
    {
      "task_id": "f1g2h3i4-5j6k-7l8m-9n0o-1p2q3r4s5t6u",
      "title": "Data Preparation",
      "agent_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
      "status": "assigned"
    }
  ]
}
```

## Event Publishing

The Project Coordinator publishes events to the message queue:

| Event Type | Description | Triggered By |
|------------|-------------|--------------|
| project.created | New project created | Project creation |
| project.updated | Project updated | Project update |
| project.deleted | Project deleted | Project deletion |
| project.status_changed | Project status changed | Status update |
| project.planning_requested | Planning requested | Planning initiation |
| project.planning_completed | Planning completed | Planning completion |
| project.execution_started | Execution started | Execution start |
| project.execution_paused | Execution paused | Execution pause |
| project.execution_resumed | Execution resumed | Execution resume |
| project.execution_completed | Execution completed | Execution completion |
| project.team_created | Team created | Team creation |
| project.team_updated | Team updated | Team update |
| project.result_added | Result added | Result addition |
| project.completed | Project completed | Project completion |

Example event:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440005",
  "type": "project.created",
  "source": "project-coordinator",
  "timestamp": "2025-03-29T06:00:00.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "project_id": "b9a8c7d6-e5f4-4g3h-2i1j-0k9l8m7n6o5p",
    "name": "Customer Data Analysis",
    "description": "Analyze customer data for purchasing patterns and create visualizations",
    "status": "created",
    "created_by": "user-123"
  }
}
```

## Integration Points

### Planning System

- **Plan Generation**: Request and receive project plans
- **Task Management**: Monitor task creation and execution
- **Progress Tracking**: Receive task progress updates
- **Plan Adjustment**: Request plan adjustments as needed

### Agent Orchestrator

- **Team Formation**: Request agent teams based on project requirements
- **Agent Coordination**: Coordinate agent collaboration
- **Agent Status**: Monitor agent status and activity
- **Resource Management**: Manage agent resources for projects

### Service Integration

- **Workflow Orchestration**: Coordinate cross-service workflows
- **State Management**: Track workflow state across services
- **Event Handling**: Process events from various services
- **Error Recovery**: Handle errors and exceptions in workflows

### Web Dashboard

- **User Interface**: Provide data for user interface
- **Command Handling**: Process user commands
- **Visualization**: Supply data for project visualizations
- **Reporting**: Generate project reports and summaries

## Project Lifecycle Management

The service manages the complete project lifecycle:

```mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Planning
    Planning --> PlanReview
    PlanReview --> Rejected: Plan Rejected
    Rejected --> Planning: Revise Plan
    PlanReview --> Ready: Plan Approved
    Ready --> TeamAssembly
    TeamAssembly --> Executing
    Executing --> Paused: Pause Request
    Paused --> Executing: Resume Request
    Executing --> Completed: All Tasks Complete
    Executing --> Failed: Critical Failure
    Paused --> Cancelled: Cancel Request
    TeamAssembly --> Cancelled: Cancel Request
    Ready --> Cancelled: Cancel Request
    Planning --> Cancelled: Cancel Request
    Created --> Cancelled: Cancel Request
    Completed --> [*]
    Failed --> [*]
    Cancelled --> [*]
```

### State Transition Rules

| Current State | Valid Next States | Transition Triggers |
|---------------|-------------------|---------------------|
| Created | Planning, Cancelled | Planning initiation, cancellation |
| Planning | PlanReview, Cancelled | Planning completion, cancellation |
| PlanReview | Ready, Rejected, Cancelled | Plan approval, plan rejection, cancellation |
| Rejected | Planning, Cancelled | Plan revision, cancellation |
| Ready | TeamAssembly, Cancelled | Team assembly initiation, cancellation |
| TeamAssembly | Executing, Cancelled | Team assembly completion, cancellation |
| Executing | Paused, Completed, Failed | Pause request, task completion, critical failure |
| Paused | Executing, Cancelled | Resume request, cancellation |
| Completed | (Terminal state) | N/A |
| Failed | (Terminal state) | N/A |
| Cancelled | (Terminal state) | N/A |

## Team Assembly Process

The service coordinates team assembly:

```mermaid
sequenceDiagram
    participant PC as Project Coordinator
    participant PS as Planning System
    participant AO as Agent Orchestrator
    
    PC->>PS: Get Agent Requirements
    PS->>PC: Return Agent Requirements
    PC->>PC: Create Team Structure
    PC->>AO: Request Agents with Capabilities
    AO->>AO: Search Available Agents
    AO->>AO: Create New Agents if Needed
    AO->>PC: Return Selected Agents
    PC->>PC: Assign Agents to Team Roles
    PC->>PC: Create Team Record
    PC->>AO: Notify Agents of Team Assignment
    PC->>PS: Provide Team Information
```

## Result Aggregation

The service handles project result aggregation:

```mermaid
graph TD
    subgraph "Result Collection"
        RC1[Collect Task Results]
        RC2[Validate Result Formats]
        RC3[Store Raw Results]
    end
    
    subgraph "Result Processing"
        RP1[Merge Related Results]
        RP2[Format Consistent Output]
        RP3[Generate Summary]
    end
    
    subgraph "Result Delivery"
        RD1[Package Deliverables]
        RD2[Apply Formatting Preferences]
        RD3[Store Final Deliverables]
    end
    
    RC1 --> RC2 --> RC3
    RC3 --> RP1 --> RP2 --> RP3
    RP3 --> RD1 --> RD2 --> RD3
    
    style RC1 fill:#ffe0d0,stroke:#cc6600
    style RC2 fill:#ffe0d0,stroke:#cc6600
    style RC3 fill:#ffe0d0,stroke:#cc6600
    style RP1 fill:#ffe0d0,stroke:#cc6600
    style RP2 fill:#ffe0d0,stroke:#cc6600
    style RP3 fill:#ffe0d0,stroke:#cc6600
    style RD1 fill:#ffe0d0,stroke:#cc6600
    style RD2 fill:#ffe0d0,stroke:#cc6600
    style RD3 fill:#ffe0d0,stroke:#cc6600
```

## Configuration

Configuration is managed through environment variables:

```python
# Example environment variables
DATABASE_URL=postgresql://user:password@localhost:5432/project_coordinator
REDIS_URL=redis://localhost:6379
PLANNING_SYSTEM_URL=http://planning-system:8080
AGENT_ORCHESTRATOR_URL=http://agent-orchestrator:8080
SERVICE_INTEGRATION_URL=http://service-integration:8080
STORAGE_BUCKET=project-results-bucket
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
- **active_project_count**: Number of active projects
- **project_completion_rate**: Percentage of successfully completed projects
- **team_size_distribution**: Distribution of team sizes
- **project_duration_seconds**: Project duration histogram
- **api_request_duration_seconds**: API endpoint response times
- **api_request_count**: Count of API requests by endpoint and status

## Common Issues and Troubleshooting

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| Project planning failures | Invalid project requirements, planning service unavailable | Validate requirements, check planning service health |
| Team assembly issues | Agent unavailability, incompatible agent capabilities | Verify agent availability, adjust capability requirements |
| Execution coordination failures | Service integration issues, workflow errors | Check service integration health, implement retry mechanisms |
| Result aggregation failures | Missing or invalid task results, storage issues | Validate task outputs, check storage connectivity |
| Slow project execution | Resource constraints, task bottlenecks | Optimize resource allocation, identify and address bottlenecks |

## Security Considerations

- **Project Data Access**: Project data is accessible only to authorized users
- **Result Protection**: Project results are protected with access controls
- **Audit Logging**: All project management actions are logged
- **Secret Management**: Sensitive configuration is securely stored
- **API Authentication**: All API requests require authentication

## References

- [System Overview](../architecture/system-overview.md)
- [Communication Patterns](../architecture/communication-patterns.md)
- [Data Flow](../architecture/data-flow.md)
- [Project Execution](../../guides/process-flows/project-execution.md)
- [Agent Lifecycle](../../guides/process-flows/agent-lifecycle.md)
- [Planning System Service](planning-system.md)
- [Agent Orchestrator Service](agent-orchestrator.md)
