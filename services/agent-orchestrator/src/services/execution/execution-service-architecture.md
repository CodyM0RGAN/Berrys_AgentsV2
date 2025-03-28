# Execution Service Architecture

## Overview
The Execution Service manages the complete lifecycle of task executions performed by agents. This document outlines the modular architecture of the service and explains how the components interact.

## Architecture Diagram

```
┌─────────────────────────┐     ┌───────────────────────┐
│                         │     │                       │
│  API Routes/Controllers │────▶│   ExecutionService    │
│                         │     │      (Facade)         │
└─────────────────────────┘     └───────────┬───────────┘
                                            │
                                            │ coordinates
                                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐    │
│  │                 │   │                 │   │                 │    │
│  │ StateManager    │◀──┼─▶ TaskRunner    │◀──┼─▶ ProgressTracker│    │
│  │                 │   │                 │   │                 │    │
│  └─────┬───────────┘   └────────┬────────┘   └────────┬────────┘    │
│        │                        │                     │              │
│        │                        │                     │              │
│        ▼                        ▼                     ▼              │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐    │
│  │                 │   │                 │   │                 │    │
│  │ EventEmitter    │   │ BackgroundManager│   │ Repository     │    │
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

## Core Components

### ExecutionService (Facade)
- **Purpose**: Provides a unified API for managing executions
- **Responsibilities**: Orchestrates interactions between specialized components
- **Key Dependencies**: All other components

### ExecutionRepository
- **Purpose**: Data access layer abstracting database operations
- **Responsibilities**: CRUD operations for executions and execution history
- **Key Dependencies**: Database connection

### ExecutionStateManager
- **Purpose**: Manages execution state transitions 
- **Responsibilities**: Validation of state transitions, executing state change logic
- **Key Dependencies**: Repository, EventEmitter

### ExecutionTaskRunner
- **Purpose**: Executes the actual tasks for agents
- **Responsibilities**: Task preparation, execution coordination, result processing
- **Key Dependencies**: Repository, StateManager, ProgressTracker, CommandBus (for model service)

### ProgressTracker
- **Purpose**: Monitors and reports execution progress
- **Responsibilities**: Updating progress metrics, step tracking
- **Key Dependencies**: Repository, EventEmitter

### BackgroundTaskManager
- **Purpose**: Manages asynchronous background tasks
- **Responsibilities**: Task creation, cancellation, cleanup
- **Key Dependencies**: None (handles asyncio.Tasks)

### EventEmitter
- **Purpose**: Centralizes event publishing logic
- **Responsibilities**: Formatting and emitting events to the event bus
- **Key Dependencies**: EventBus

## Component Interactions

### Starting an Execution
1. **ExecutionService** receives the start request
2. **StateManager** validates and updates the execution state to PREPARING
3. **BackgroundTaskManager** creates a background task
4. **TaskRunner** begins the execution process
5. **ProgressTracker** updates the initial progress
6. **EventEmitter** sends state change and progress events

### Updating Progress
1. **TaskRunner** calls the ProgressTracker
2. **ProgressTracker** updates the execution's progress in the Repository
3. **EventEmitter** publishes progress update events

### Transitioning State
1. **StateManager** validates the state transition
2. **Repository** updates the execution state and creates history
3. **EventEmitter** publishes state change events
4. **StateManager** handles any state-specific side effects (e.g., cancellation)

### Completing Execution
1. **TaskRunner** processes the final result
2. **Repository** stores the results
3. **StateManager** transitions to COMPLETED state
4. **ProgressTracker** updates to 100% completion
5. **EventEmitter** publishes completion event
6. **BackgroundTaskManager** cleans up the task resources

## Error Handling Strategy

The service implements a multi-level error handling approach:

1. **Component-level error handling**: Each component handles and logs errors related to its responsibilities
2. **Service-level recovery**: The service facade catches and translates errors into appropriate exceptions
3. **Task isolation**: Errors in one execution don't affect others
4. **State-based recovery**: Failed executions can be retried
5. **Transaction safety**: Database operations use transactions to prevent partial updates

Error handling follows these principles:
- All errors are logged with appropriate context
- Database transactions are properly committed or rolled back
- User-facing errors provide clear information
- Background task errors are captured and result in FAILED state

## Extension Points

The modular architecture provides several extension points:

1. **New Execution States**: Add new states to the ExecutionState enum and update the StateManager's transition rules
2. **Custom Task Types**: Extend the TaskRunner with specialized task execution logic
3. **Additional Progress Metrics**: Extend the ProgressTracker to include new types of progress information
4. **Custom Event Types**: Add new event types to the EventEmitter
5. **Specialized Repositories**: Create specialized repositories for specific data access patterns
