# Planning System Service

The Planning System Service is responsible for project planning, task dependency management, resource allocation, and timeline forecasting in the Berrys_AgentsV2 system.

## Overview

This service implements three main capabilities:

1. **Strategic Planning**: High-level project planning and resource allocation
2. **Tactical Planning**: Breaking down plans into executable tasks with dependencies
3. **Project Forecasting**: Predicting project timelines and identifying potential bottlenecks

## Architecture

The service follows a modular design pattern with clear separation of concerns:

```
┌─────────────────────────┐     ┌───────────────────────┐
│                         │     │                       │
│  API Routes/Controllers │────▶│    PlanningService    │
│                         │     │      (Facade)         │
└─────────────────────────┘     └───────────┬───────────┘
                                            │
                                            │ coordinates
                                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐    │
│  │                 │   │                 │   │                 │    │
│  │ StrategicPlanner│◀──┼─▶ TacticalPlanner│◀──┼─▶ ProjectForecaster│    │
│  │                 │   │                 │   │                 │    │
│  └─────┬───────────┘   └────────┬────────┘   └────────┬────────┘    │
│        │                        │                     │              │
│        │                        │                     │              │
│        ▼                        ▼                     ▼              │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐    │
│  │                 │   │                 │   │                 │    │
│  │ResourceOptimizer│   │DependencyManager│   │ Repository     │    │
│  │                 │   │                 │   │                 │    │
│  └────────┬────────┘   └─────────────────┘   └────────┬────────┘    │
│           │                                           │              │
└───────────┼───────────────────────────────────────────┼──────────────┘
            │                                           │
            ▼                                           ▼
    ┌───────────────┐                          ┌───────────────┐
    │               │                          │               │
    │   Event Bus   │                          │   Database    │
    │               │                          │               │
    └───────────────┘                          └───────────────┘
```

## Key Components

1. **PlanningService**: Main facade coordinating all planning components ✅
2. **StrategicPlanner**: High-level planning and resource allocation ✅
3. **TacticalPlanner**: Task breakdown and dependency management ✅
4. **ProjectForecaster**: Timeline prediction and bottleneck identification ✅
5. **ResourceOptimizer**: Optimal allocation of resources ✅
6. **DependencyManager**: Manages task dependencies using graph algorithms ✅

## Architecture Improvements

The Planning System now utilizes several advanced architectural patterns:

1. **Base Component Pattern**: A `BasePlannerComponent` provides common functionality for all planners, reducing code duplication and standardizing logging, error handling, and event publishing.

2. **Validation Strategy Pattern**: Specialized validation strategies separate validation logic from business logic, allowing for more flexible and maintainable validation rules.

3. **Builder Pattern**: `ResponseBuilder` creates consistent response models with a fluent interface.

4. **Dependency Injection**: All components follow consistent dependency injection patterns for better testability and modularity.

## Technologies

- **NetworkX**: Graph-based dependency management
- **PuLP/OR-Tools**: Mathematical optimization for resource allocation
- **PyMC/Prophet**: Probabilistic forecasting
- **FastAPI**: Web framework
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and serialization

## API Endpoints

The service exposes the following API endpoints:

- `POST /plans`: Create a new plan
- `GET /plans/{plan_id}`: Get plan details
- `PUT /plans/{plan_id}`: Update a plan
- `DELETE /plans/{plan_id}`: Delete a plan
- `POST /plans/{plan_id}/tasks`: Add tasks to a plan
- `GET /plans/{plan_id}/tasks`: List tasks in a plan
- `POST /plans/{plan_id}/dependencies`: Define task dependencies
- `GET /plans/{plan_id}/dependencies`: Get task dependencies
- `GET /plans/{plan_id}/forecast`: Get timeline forecast
- `GET /plans/{plan_id}/bottlenecks`: Identify bottlenecks
- `POST /plans/{plan_id}/optimize`: Optimize resource allocation

## Event Integration

The service publishes and subscribes to the following events:

- **Published**:
  - `plan.created`: When a new plan is created
  - `plan.updated`: When a plan is updated
  - `plan.task.added`: When tasks are added to a plan
  - `plan.dependencies.updated`: When dependencies are updated
  - `plan.timeline.forecasted`: When a timeline forecast is updated

- **Subscribed**:
  - `project.created`: To create initial plans for new projects
  - `task.completed`: To update plan progress
  - `resource.availability.changed`: To update resource allocations

## Getting Started

To run the service locally:

```bash
cd services/planning-system
pip install -r requirements.txt
uvicorn src.main:app --reload
```

For more details on the service design and implementation, see the [implementation docs](src/docs/implementation.md).
