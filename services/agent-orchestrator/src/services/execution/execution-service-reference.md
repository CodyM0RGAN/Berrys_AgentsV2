# Execution Service Technical Reference

## Public API

### Getting and Listing Executions
- `get_execution(execution_id: UUID)`: Retrieve a single execution by ID
- `list_executions(agent_id: Optional[UUID] = None, task_id: Optional[UUID] = None, state: Optional[ExecutionState] = None, page: int = 1, page_size: int = 20)`: Retrieve executions with filtering and pagination

### Execution Lifecycle Control
- `start_execution(execution_id: UUID)`: Start an execution
- `pause_execution(execution_id: UUID, reason: Optional[str] = None)`: Pause a running execution
- `resume_execution(execution_id: UUID)`: Resume a paused execution
- `cancel_execution(execution_id: UUID, reason: Optional[str] = None)`: Cancel an execution
- `retry_execution(execution_id: UUID)`: Retry a failed execution

### Progress and Results
- `update_progress(execution_id: UUID, progress_update: ExecutionProgressUpdate)`: Update execution progress
- `submit_result(execution_id: UUID, result_request: ExecutionResultRequest)`: Submit execution results
- `complete_execution(execution_id: UUID, result: Dict[str, Any])`: Mark execution as completed with results
- `fail_execution(execution_id: UUID, error_message: str)`: Mark execution as failed

### History and Monitoring
- `get_execution_state_history(execution_id: UUID, limit: int = 10)`: Get execution state history

## Execution States

The `ExecutionState` enum defines the possible states of an execution:

- `QUEUED`: Initial state when execution is created
- `PREPARING`: Gathering resources and context for execution
- `RUNNING`: Actively executing the task
- `PAUSED`: Execution temporarily halted
- `COMPLETED`: Successfully finished execution
- `FAILED`: Execution terminated with errors
- `CANCELLED`: Execution manually cancelled

## Valid State Transitions

The following diagram shows the valid state transitions for executions:

```
             ┌─────────────────────┐
             │                     │
             │       QUEUED        │◀────────┐
             │                     │         │
             └────────┬────────────┘         │
                      │                      │
                      ▼                      │
             ┌─────────────────────┐         │
             │                     │         │
             │     PREPARING       │         │
             │                     │         │
             └────────┬────────────┘         │
                      │                      │
                      ▼                      │
┌───────────┐  ┌─────────────────────┐       │
│           │  │                     │       │
│  CANCELLED│◀─┤      RUNNING        │       │
│           │  │                     │       │
└───────────┘  └──────┬──────┬───────┘       │
      ▲                │      │              │
      │                ▼      ▼              │
      │        ┌─────────┐  ┌─────────┐      │
      │        │         │  │         │      │
      └────────┤ PAUSED  │  │ FAILED  ├──────┘
               │         │  │         │
               └────┬────┘  └─────────┘
                    │            
                    ▼            
            ┌──────────────┐     
            │              │     
            │  COMPLETED   │     
            │              │     
            └──────────────┘     
```

## Events Published

The Execution Service publishes the following events that other services can subscribe to:

### Event: `agent.execution.state_changed`
Emitted when an execution's state changes.

**Payload:**
```json
{
  "execution_id": "123e4567-e89b-12d3-a456-426614174000",
  "agent_id": "123e4567-e89b-12d3-a456-426614174001", 
  "task_id": "123e4567-e89b-12d3-a456-426614174002",
  "previous_state": "RUNNING",
  "new_state": "COMPLETED",
  "reason": "Execution completed successfully"
}
```

### Event: `agent.execution.progress`
Emitted when execution progress is updated.

**Payload:**
```json
{
  "execution_id": "123e4567-e89b-12d3-a456-426614174000",
  "agent_id": "123e4567-e89b-12d3-a456-426614174001",
  "task_id": "123e4567-e89b-12d3-a456-426614174002",
  "progress_percentage": 75.0,
  "status_message": "Processing data"
}
```

### Event: `agent.execution.completed`
Emitted when an execution reaches a terminal state (COMPLETED, FAILED, or CANCELLED).

**Payload:**
```json
{
  "execution_id": "123e4567-e89b-12d3-a456-426614174000",
  "agent_id": "123e4567-e89b-12d3-a456-426614174001",
  "task_id": "123e4567-e89b-12d3-a456-426614174002",
  "state": "COMPLETED",
  "result": { "data": "execution result data..." },
  "error_message": null
}
```

## Error Handling

The Execution Service throws the following exceptions:

- `ExecutionNotFoundError`: When an execution with the specified ID doesn't exist
- `InvalidExecutionStateError`: When attempting an invalid state transition
- `ConcurrentModificationError`: When the execution was modified by another process
- `AgentNotFoundError`: When the associated agent doesn't exist
- `ModelOrchestrationError`: When there's an error communicating with the Model Orchestration service
- `DatabaseError`: When there's an error with database operations

Error handling follows a consistent pattern:
1. All errors are caught and converted to appropriate exceptions
2. Database transactions are rolled back on errors
3. Error details are logged for troubleshooting
4. Clear error messages are provided in the exception

## Usage Examples

### Starting an Execution

```python
# Create an execution (through agent service)
execution_response = await agent_service.execute_agent(
    agent_id=agent_id,
    execution_request=AgentExecutionRequest(
        task_id=task_id,
        context=[{"type": "text", "content": "Research quantum computing"}],
        parameters={"max_depth": 3}
    )
)

# Start the execution
execution = await execution_service.start_execution(execution_response.execution_id)
```

### Tracking Progress

```python
# Update execution progress
await execution_service.update_progress(
    execution_id=execution_id,
    progress_update=ExecutionProgressUpdate(
        progress_percentage=50.0,
        status_message="Processing research data",
        completed_steps=["Initialize", "Search"],
        current_step="Process",
        remaining_steps=["Summarize", "Finalize"]
    )
)
```

### Handling Results

```python
# Complete an execution with results
await execution_service.complete_execution(
    execution_id=execution_id,
    result={
        "summary": "Research findings on quantum computing...",
        "sources": ["https://example.com/quantum-paper", "...]
    }
)

# Or mark an execution as failed
await execution_service.fail_execution(
    execution_id=execution_id,
    error_message="Failed to complete research: insufficient data available"
)
```

### Controlling Execution Flow

```python
# Pause an execution
await execution_service.pause_execution(
    execution_id=execution_id,
    reason="Pausing for human review"
)

# Resume an execution
await execution_service.resume_execution(execution_id=execution_id)

# Cancel an execution
await execution_service.cancel_execution(
    execution_id=execution_id,
    reason="Task no longer required"
)
```

### Retry a Failed Execution

```python
# Retry a failed execution
await execution_service.retry_execution(execution_id=execution_id)
