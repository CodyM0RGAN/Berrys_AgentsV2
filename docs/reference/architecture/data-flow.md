# Data Flow

**Last Modified:** 2025-03-29  
**Completion Date:** 2025-03-29  
**Doc Type:** Reference  

---

## Overview

This document describes the data flow patterns within the Berrys_AgentsV2 platform. It maps how information flows between services, databases, message queues, and external systems throughout various key processes.

## Core Data Entities

The platform operates on these primary data entities:

```mermaid
erDiagram
    Project ||--o{ Task : contains
    Project ||--o{ Agent : employs
    Task }o--o{ Agent : assigned_to
    Agent }o--o{ AgentSpecialization : has
    Agent }o--|| AgentTemplate : based_on
    Task }o--o{ ToolExecution : uses
    Agent }o--o{ ToolExecution : performs
    Agent }o--o{ AgentState : transitions
    
    Project {
        UUID id
        string name
        string description
        string status
        jsonb requirements
        timestamp created_at
        timestamp updated_at
    }
    
    Task {
        UUID id
        UUID project_id
        string title
        string description
        string status
        int priority
        jsonb dependencies
        timestamp deadline
        timestamp created_at
        timestamp updated_at
    }
    
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
    
    AgentTemplate {
        UUID id
        string name
        string description
        jsonb parameters
        timestamp created_at
        timestamp updated_at
    }
    
    AgentSpecialization {
        UUID id
        UUID agent_id
        string name
        jsonb capabilities
        timestamp created_at
    }
    
    ToolExecution {
        UUID id
        UUID tool_id
        UUID agent_id
        UUID task_id
        jsonb input_parameters
        jsonb output_result
        string status
        timestamp created_at
        timestamp completed_at
    }
    
    AgentState {
        UUID id
        UUID agent_id
        string previous_state
        string new_state
        string transition_reason
        timestamp created_at
    }
```

## Service Data Ownership

Each service has primary ownership of specific data entities:

| Service | Primary Data Entities | Secondary Access |
|---------|----------------------|-------------------|
| Project Coordinator | Project | Task, Agent |
| Planning System | Task, Task Dependencies | Project, Agent |
| Agent Orchestrator | Agent, AgentState, AgentSpecialization | Task, AgentTemplate |
| Model Orchestration | Model, ModelExecution | Agent |
| Tool Integration | Tool, ToolExecution | Agent, Task |
| Service Integration | Workflow, WorkflowState | Project, Task, Agent |

## Data Flow Diagrams

### Project Creation and Planning

```mermaid
flowchart TD
    subgraph "User Interaction"
        A[User] -->|Create Project Request| B[Web Dashboard]
    end
    
    subgraph "Project Management"
        B -->|Project Details| C[Project Coordinator]
        C -->|Store Project| D[(Project Database)]
        C -->|Planning Request| E[Planning System]
        E -->|Read Project| D
        E -->|Generate Tasks| F[(Task Database)]
        E -->|Plan Created| C
        C -->|Project Created Event| G[Message Queue]
    end
    
    subgraph "Notification"
        G -->|Project Ready Notification| B
        B -->|Display Project| A
    end
    
    style A fill:#d0e0ff,stroke:#0066cc
    style B fill:#ffe0d0,stroke:#cc6600
    style C fill:#ffe0d0,stroke:#cc6600
    style D fill:#d0ffd0,stroke:#00cc00
    style E fill:#ffe0d0,stroke:#cc6600
    style F fill:#d0ffd0,stroke:#00cc00
    style G fill:#d0ffd0,stroke:#00cc00
```

### Agent Creation and Initialization

```mermaid
flowchart TD
    subgraph "Project Planning"
        A[Planning System] -->|Agent Requirements| B[Project Coordinator]
    end
    
    subgraph "Agent Management"
        B -->|Create Agent Request| C[Agent Orchestrator]
        C -->|Template Request| D[Agent Template Database]
        D -->|Template| C
        C -->|Create Agent Record| E[Agent Database]
        C -->|Specialization Request| F[Agent Specialization]
        F -->|Configure Agent| E
        C -->|Initialization Request| G[Model Orchestration]
        G -->|Model Selection| H[Model Catalog]
        G -->|Initialize Agent Model| I[External AI Models]
        I -->|Model Response| G
        G -->|Initialization Results| C
        C -->|Update Agent State| E
        C -->|Agent Created Event| J[Message Queue]
    end
    
    subgraph "Notification"
        J -->|Agent Ready Notification| B
    end
    
    style A fill:#ffe0d0,stroke:#cc6600
    style B fill:#ffe0d0,stroke:#cc6600
    style C fill:#ffe0d0,stroke:#cc6600
    style D fill:#d0ffd0,stroke:#00cc00
    style E fill:#d0ffd0,stroke:#00cc00
    style F fill:#ffe0d0,stroke:#cc6600
    style G fill:#ffe0d0,stroke:#cc6600
    style H fill:#d0ffd0,stroke:#00cc00
    style I fill:#d0e0ff,stroke:#0066cc
    style J fill:#d0ffd0,stroke:#00cc00
```

### Task Execution Flow

```mermaid
flowchart TD
    subgraph "Task Assignment"
        A[Planning System] -->|Assign Task| B[Agent Orchestrator]
        B -->|Update Agent Task| C[Agent Database]
    end
    
    subgraph "Task Execution"
        B -->|Task Execution Request| D[Model Orchestration]
        D -->|Model Request| E[External AI Models]
        E -->|Model Response| D
        D -->|Execution Results| B
        
        B -->|Tool Request| F[Tool Integration]
        F -->|Tool Catalog Query| G[Tool Catalog]
        G -->|Tool Information| F
        F -->|Execute Tool| H[External Tool]
        H -->|Tool Results| F
        F -->|Tool Execution Results| B
    end
    
    subgraph "Task Completion"
        B -->|Update Task Status| I[Task Database]
        B -->|Task Completed Event| J[Message Queue]
        J -->|Task Update Notification| A
    end
    
    style A fill:#ffe0d0,stroke:#cc6600
    style B fill:#ffe0d0,stroke:#cc6600
    style C fill:#d0ffd0,stroke:#00cc00
    style D fill:#ffe0d0,stroke:#cc6600
    style E fill:#d0e0ff,stroke:#0066cc
    style F fill:#ffe0d0,stroke:#cc6600
    style G fill:#d0ffd0,stroke:#00cc00
    style H fill:#d0e0ff,stroke:#0066cc
    style I fill:#d0ffd0,stroke:#00cc00
    style J fill:#d0ffd0,stroke:#00cc00
```

### Agent Collaboration Flow

```mermaid
flowchart TD
    subgraph "Collaboration Initiation"
        A[Agent A] -->|Collaboration Request| B[Agent Orchestrator]
        B -->|Check Agent State| C[Agent Database]
        C -->|Agent B Status| B
    end
    
    subgraph "Communication"
        B -->|Message Delivery| D[Agent Communication Hub]
        D -->|Store Message| E[Message Database]
        D -->|Route Message| F[Agent B]
        F -->|Process Message| G[Model Orchestration]
        G -->|Model Request| H[External AI Models]
        H -->|Model Response| G
        G -->|Processing Result| F
        F -->|Response Message| D
        D -->|Deliver Response| A
    end
    
    subgraph "Collaboration Tracking"
        D -->|Collaboration Event| I[Message Queue]
        I -->|Collaboration Notification| J[Planning System]
        J -->|Update Task Status| K[Task Database]
    end
    
    style A fill:#ffe0d0,stroke:#cc6600
    style B fill:#ffe0d0,stroke:#cc6600
    style C fill:#d0ffd0,stroke:#00cc00
    style D fill:#ffe0d0,stroke:#cc6600
    style E fill:#d0ffd0,stroke:#00cc00
    style F fill:#ffe0d0,stroke:#cc6600
    style G fill:#ffe0d0,stroke:#cc6600
    style H fill:#d0e0ff,stroke:#0066cc
    style I fill:#d0ffd0,stroke:#00cc00
    style J fill:#ffe0d0,stroke:#cc6600
    style K fill:#d0ffd0,stroke:#00cc00
```

### Project Completion Flow

```mermaid
flowchart TD
    subgraph "Task Completion"
        A[Planning System] -->|Final Task Completed| B[Project Coordinator]
        B -->|Retrieve Project| C[Project Database]
        B -->|Retrieve Tasks| D[Task Database]
    end
    
    subgraph "Result Compilation"
        B -->|Compile Results| E[Result Compilation]
        E -->|Retrieve Agent Outputs| F[Agent Database]
        E -->|Organize Outputs| B
        B -->|Store Project Results| C
        B -->|Project Completed Event| G[Message Queue]
    end
    
    subgraph "Notification"
        G -->|Project Completion Notification| H[Web Dashboard]
        H -->|Display Results| I[User]
    end
    
    subgraph "Resource Cleanup"
        B -->|Release Agents Request| J[Agent Orchestrator]
        J -->|Update Agent States| F
        J -->|Archive Agent Data| K[Archive Storage]
    end
    
    style A fill:#ffe0d0,stroke:#cc6600
    style B fill:#ffe0d0,stroke:#cc6600
    style C fill:#d0ffd0,stroke:#00cc00
    style D fill:#d0ffd0,stroke:#00cc00
    style E fill:#ffe0d0,stroke:#cc6600
    style F fill:#d0ffd0,stroke:#00cc00
    style G fill:#d0ffd0,stroke:#00cc00
    style H fill:#ffe0d0,stroke:#cc6600
    style I fill:#d0e0ff,stroke:#0066cc
    style J fill:#ffe0d0,stroke:#cc6600
    style K fill:#d0ffd0,stroke:#00cc00
```

## Data Storage Patterns

### Database Partitioning

The platform uses a partitioned database approach to ensure scalability:

- **Service-specific databases**: Each service has its own database schema
- **Shared references**: Cross-service references use UUIDs
- **Data consistency**: Maintained through event-based synchronization

### Data Access Patterns

| Pattern | Use Case | Implementation |
|---------|----------|----------------|
| CQRS | High-read services | Separate read and write models |
| Event Sourcing | Agent state history | Store state transitions as events |
| Materialized Views | Dashboards and reports | Pre-computed aggregates |
| Cache Aside | Frequently accessed data | Redis-based caching layer |
| Repository | Entity access | Repository pattern abstractions |

### Data Migration Strategy

For schema evolution:
- Use Alembic for migration management
- Maintain backward compatibility for at least one version
- Apply migrations in controlled, sequential order
- Test migrations in staging before production
- Create backups before applying migrations

## Cross-Service Data Consistency

To maintain consistency across service boundaries:

```mermaid
sequenceDiagram
    participant Service A
    participant Database A
    participant Message Queue
    participant Service B
    participant Database B
    
    Service A->>Database A: Update Entity
    Service A->>Message Queue: Publish Change Event
    Message Queue-->>Service A: Acknowledge
    
    Note over Service A,Database B: Asynchronous Boundary
    
    Message Queue->>Service B: Deliver Change Event
    Service B->>Database B: Update Related Entity
    Service B-->>Message Queue: Acknowledge
```

Strategies for consistency:
- **Eventually consistent**: Most cross-service data follows eventual consistency
- **Change events**: All state changes broadcast events for synchronization
- **Idempotent operations**: All operations are idempotent to allow retries
- **Outbox pattern**: Ensures reliable event publishing with database transactions

## Privacy and Data Protection

Data classification:
- **Sensitive data**: User information, API keys, credentials
- **System data**: Service configurations, logs, metrics
- **Content data**: Agent inputs, outputs, and artifacts

Data protection strategies:
- **Encryption at rest**: For all databases and object storage
- **Encryption in transit**: TLS for all service communication
- **Field-level encryption**: For sensitive data fields
- **Access control**: Role-based access control for all data access
- **Data retention**: Automated purging of data beyond retention period

## References

- [System Overview](system-overview.md)
- [Communication Patterns](communication-patterns.md)
- [Database Schema Reference](../database-schema.md)
- [Message Contracts Reference](../message-contracts.md)
