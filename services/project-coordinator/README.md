# Project Coordinator Service

The Project Coordinator Service is responsible for project lifecycle management, resource coordination, progress tracking, and analytics within the Berrys_AgentsV2 system.

## Purpose

This service acts as the central hub for managing projects throughout their entire lifecycle, from initial creation through planning, execution, and completion. It provides APIs for tracking project progress, managing associated resources, storing artifacts, and generating analytics.

## Core Features

- **Project Lifecycle Management**: Track and manage the project lifecycle using a state machine pattern that enforces valid state transitions (draft, planning, in progress, paused, completed, archived)
- **Progress Tracking**: Monitor project progress with support for multiple tracking strategies (simple, weighted, milestone-based)
- **Resource Management**: Allocate, monitor, and optimize resources across projects with different optimization strategies (time, cost, quality, balanced)
- **Analytics Generation**: Generate comprehensive project analytics with task-specific generators for progress, resources, and performance
- **Artifact Storage**: Store and retrieve project artifacts with content-type detection and deduplication
- **Service Integration**: Coordinate with other services through the Service Integration service for cross-service workflows

## Architecture

The Project Coordinator Service follows a clean, modular architecture implementing several design patterns:

- **Repository Pattern**: For data access abstraction
- **State Pattern**: For managing project lifecycle states
- **Strategy Pattern**: For interchangeable tracking and optimization algorithms
- **Template Method Pattern**: For analytics generation
- **Factory Pattern**: For creating appropriate optimizers
- **Facade Pattern**: For providing a simplified interface to the complex subsystems

```
┌───────────────────────────────────────────────────────────────────────┐
│                           API Layer                                    │
│                                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Projects   │  │  Lifecycle  │  │  Resources  │  │  Analytics  │  │
│  │   Router    │  │   Router    │  │   Router    │  │   Router    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
                           │
┌───────────────────────────────────────────────────────────────────────┐
│                        Service Layer                                   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                       Project Facade                             │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐          │
│  │ Lifecycle │  │ Progress  │  │ Resource  │  │ Analytics │          │
│  │  Manager  │  │  Tracker  │  │  Manager  │  │  Engine   │          │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘          │
│                                                                       │
│  ┌───────────────────┐  ┌───────────────────┐                        │
│  │    Artifacts      │  │  Other Specialized │                        │
│  │      Store        │  │      Services      │                        │
│  └───────────────────┘  └───────────────────┘                        │
└───────────────────────────────────────────────────────────────────────┘
                           │
┌───────────────────────────────────────────────────────────────────────┐
│                      Repository Layer                                  │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                       Base Repository                            │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐          │
│  │  Project  │  │   State   │  │ Resource  │  │ Analytics │          │
│  │ Repository│  │ Repository│  │ Repository│  │ Repository│          │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘          │
└───────────────────────────────────────────────────────────────────────┘
                           │
                     ┌───────────┐
                     │ Database  │
                     └───────────┘
```

## Key Components

### Repository Layer

- **BaseRepository**: Generic repository implementation for CRUD operations
- **ProjectRepository**: Project-specific repository with specialized queries and operations

### Service Layer

- **ProjectFacade**: Unified interface for all project operations
- **LifecycleManager**: Handles project state transitions and enforces valid state changes
- **ProgressTracker**: Tracks and analyzes project progress with multiple strategies
- **ResourceManager**: Manages resource allocation and optimization
- **AnalyticsEngine**: Generates project analytics with various generators
- **ArtifactStore**: Stores and retrieves project artifacts

### API Layer

- **ProjectsRouter**: Endpoints for project CRUD operations
- **LifecycleRouter**: Endpoints for project state transitions
- **ResourcesRouter**: Endpoints for resource management
- **AnalyticsRouter**: Endpoints for analytics generation
- **ArtifactsRouter**: Endpoints for artifact management

## Integration Points

- **Service Integration Service**: For cross-service workflows
- **Planning System**: For project planning and forecasting
- **Agent Orchestrator**: For agent task execution

## Repository Structure

```
services/project-coordinator/
├── src/
│   ├── models/            # Data models (API and internal)
│   ├── repositories/      # Data access layer
│   ├── services/          # Business logic
│   │   ├── lifecycle/     # Lifecycle management
│   │   ├── progress/      # Progress tracking
│   │   ├── resources/     # Resource management
│   │   ├── analytics/     # Analytics generation
│   │   ├── artifacts/     # Artifact storage
│   │   └── project_facade.py  # Facade service
│   ├── routers/           # API endpoints
│   ├── config.py          # Configuration
│   ├── dependencies.py    # Dependency injection
│   ├── exceptions.py      # Custom exceptions
│   └── main.py            # Application entrypoint
├── Dockerfile             # Container definition
├── README.md              # Documentation
└── requirements.txt       # Dependencies
```

## Running the Service

### Prerequisites

- Python 3.9+
- PostgreSQL
- Redis (for message bus)

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ARTIFACT_STORAGE_PATH`: Path for artifact storage
- `SERVICE_INTEGRATION_URL`: URL of Service Integration service

### Local Development

```bash
cd services/project-coordinator
pip install -r requirements.txt
uvicorn src.main:app --reload
```

### Docker

```bash
docker-compose up -d project-coordinator
```

## API Endpoints

- `GET /projects`: List projects
- `POST /projects`: Create a new project
- `GET /projects/{project_id}`: Get project details
- `PUT /projects/{project_id}`: Update project
- `POST /projects/{project_id}/archive`: Archive project
- `POST /projects/{project_id}/state`: Transition project state
- `GET /projects/{project_id}/progress`: Get project progress
- `POST /projects/{project_id}/progress`: Update project progress
- `GET /projects/{project_id}/resources`: Get project resources
- `POST /projects/{project_id}/resources`: Allocate resource to project
- `GET /projects/{project_id}/analytics/{analytics_type}`: Generate project analytics
- `GET /projects/{project_id}/artifacts`: Get project artifacts
- `POST /projects/{project_id}/artifacts`: Upload project artifact

## License

[MIT](../../LICENSE)
