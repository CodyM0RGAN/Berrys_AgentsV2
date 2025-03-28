# Execution Service Implementation Guide

This document provides detailed guidance for developers working on the Execution Service components.

## Component Specifications

### ExecutionRepository

```python
class ExecutionRepository:
    """
    Handles all database operations for executions.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_by_id(self, execution_id: UUID) -> Optional[AgentExecutionModel]:
        """
        Get an execution by ID.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Optional[AgentExecutionModel]: Execution if found, None otherwise
            
        Raises:
            DatabaseError: If database operation fails
        """
        # Implementation
        
    async def list_executions(self, filters: Dict[str, Any], pagination: Dict[str, int]) -> Tuple[List[AgentExecutionModel], int]:
        """
        List executions with filtering and pagination.
        
        Args:
            filters: Dictionary of filter parameters
            pagination: Dictionary with page and page_size
            
        Returns:
            Tuple[List[AgentExecutionModel], int]: List of executions and total count
            
        Raises:
            DatabaseError: If database operation fails
        """
        # Implementation
        
    async def update_state(self, execution_id: UUID, state: ExecutionState, timestamps: Dict[str, datetime] = None) -> Optional[AgentExecutionModel]:
        """
        Update execution state.
        
        Args:
            execution_id: Execution ID
            state: New state
            timestamps: Optional timestamps to update (e.g., started_at, completed_at)
            
        Returns:
            Optional[AgentExecutionModel]: Updated execution if successful, None if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        # Implementation
        
    async def update_progress(self, execution_id: UUID, percentage: float, message: str, context_update: Dict = None) -> Optional[AgentExecutionModel]:
        """
        Update execution progress.
        
        Args:
            execution_id: Execution ID
            percentage: Progress percentage (0-100)
            message: Status message
            context_update: Optional context update
            
        Returns:
            Optional[AgentExecutionModel]: Updated execution if successful, None if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        # Implementation
        
    async def update_result(self, execution_id: UUID, result: Dict[str, Any], error_message: Optional[str] = None) -> Optional[AgentExecutionModel]:
        """
        Update execution result.
        
        Args:
            execution_id: Execution ID
            result: Execution result
            error_message: Optional error message
            
        Returns:
            Optional[AgentExecutionModel]: Updated execution if successful, None if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        # Implementation
        
    async def create_state_history(self, history_item: ExecutionStateModel) -> ExecutionStateModel:
        """
        Create execution state history entry.
        
        Args:
            history_item: History item to create
            
        Returns:
            ExecutionStateModel: Created history item
            
        Raises:
            DatabaseError: If database operation fails
        """
        # Implementation
        
    async def get_state_history(self, execution_id: UUID, limit: int = 10) -> List[ExecutionStateModel]:
        """
        Get execution state history.
        
        Args:
            execution_id: Execution ID
            limit: Maximum number of history entries to return
            
        Returns:
            List[ExecutionStateModel]: Execution state history
            
        Raises:
            DatabaseError: If database operation fails
        """
        # Implementation
        
    async def delete_execution(self, execution_id: UUID) -> bool:
        """
        Delete an execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            bool: True if deleted, False if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        # Implementation
```

### ExecutionStateManager

```python
class ExecutionStateManager:
    """
    Manages execution state transitions ensuring validation rules are followed.
    """
    def __init__(self, repository: ExecutionRepository, event_emitter: ExecutionEventEmitter):
        self.repository = repository
        self.event_emitter = event_emitter
        
    async def change_state(self, execution_id: UUID, target_state: ExecutionState, reason: str = None) -> AgentExecutionModel:
        """
        Change execution state.
        
        Args:
            execution_id: Execution ID
            target_state: Target state
            reason: Reason for state change
            
        Returns:
            AgentExecutionModel: Updated execution
            
        Raises:
            ExecutionNotFoundError: If execution not found
            InvalidExecutionStateError: If state transition is invalid
            DatabaseError: If database operation fails
        """
        # Implementation
        
    async def handle_state_side_effects(self, execution: AgentExecutionModel, previous_state: ExecutionState, new_state: ExecutionState) -> None:
        """
        Handle state-specific side effects.
        
        Args:
            execution: Execution model
            previous_state: Previous state
            new_state: New state
            
        Raises:
            DatabaseError: If database operation fails
        """
        # Implementation
        
    def validate_transition(self, current_state: ExecutionState, target_state: ExecutionState) -> bool:
        """
        Validate state transition.
        
        Args:
            current_state: Current state
            target_state: Target state
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Implementation
```

### ExecutionTaskRunner

```python
class ExecutionTaskRunner:
    """
    Handles the execution of tasks, communicating with model services.
    """
    def __init__(
        self,
        repository: ExecutionRepository,
        state_manager: ExecutionStateManager,
        progress_tracker: ExecutionProgressTracker,
        command_bus: CommandBus,
    ):
        self.repository = repository
        self.state_manager = state_manager
        self.progress_tracker = progress_tracker
        self.command_bus = command_bus
        
    async def execute_task(self, execution: AgentExecutionModel) -> None:
        """
        Execute a task.
        
        Args:
            execution: Execution model
        """
        # Implementation
        
    async def prepare_task_input(self, execution: AgentExecutionModel) -> Dict[str, Any]:
        """
        Prepare task input.
        
        Args:
            execution: Execution model
            
        Returns:
            Dict[str, Any]: Task input
            
        Raises:
            AgentNotFoundError: If agent not found
        """
        # Implementation
        
    async def call_model_service(self, execution: AgentExecutionModel, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call model service.
        
        Args:
            execution: Execution model
            task_input: Task input
            
        Returns:
            Dict[str, Any]: Model service response
            
        Raises:
            ModelOrchestrationError: If model service call fails
        """
        # Implementation
        
    def process_results(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process task results.
        
        Args:
            result: Raw result from model service
            
        Returns:
            Dict[str, Any]: Processed result
        """
        # Implementation
```

### ExecutionProgressTracker

```python
class ExecutionProgressTracker:
    """
    Tracks and reports execution progress.
    """
    def __init__(self, repository: ExecutionRepository, event_emitter: ExecutionEventEmitter):
        self.repository = repository
        self.event_emitter = event_emitter
        
    async def update_progress(self, execution_id: UUID, progress_data: ExecutionProgressUpdate) -> AgentExecutionModel:
        """
        Update execution progress.
        
        Args:
            execution_id: Execution ID
            progress_data: Progress update
            
        Returns:
            AgentExecutionModel: Updated execution
            
        Raises:
            ExecutionNotFoundError: If execution not found
            InvalidExecutionStateError: If execution is not in a state that allows progress updates
            DatabaseError: If database operation fails
        """
        # Implementation
```

### BackgroundTaskManager

```python
class BackgroundTaskManager:
    """
    Manages background tasks for executions.
    """
    def __init__(self):
        self._running_tasks: Dict[UUID, asyncio.Task] = {}
        
    def start_task(self, execution_id: UUID, coro) -> asyncio.Task:
        """
        Start a background task.
        
        Args:
            execution_id: Execution ID
            coro: Coroutine to run as background task
            
        Returns:
            asyncio.Task: Created task
        """
        # Implementation
        
    async def cancel_task(self, execution_id: UUID) -> None:
        """
        Cancel a background task.
        
        Args:
            execution_id: Execution ID
        """
        # Implementation
        
    def get_task(self, execution_id: UUID) -> Optional[asyncio.Task]:
        """
        Get a background task.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Optional[asyncio.Task]: Task if found, None otherwise
        """
        # Implementation
        
    def clear_task(self, execution_id: UUID) -> None:
        """
        Clear a background task reference.
        
        Args:
            execution_id: Execution ID
        """
        # Implementation
```

### ExecutionEventEmitter

```python
class ExecutionEventEmitter:
    """
    Handles publishing execution-related events.
    """
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        
    async def emit_state_changed(self, execution: AgentExecutionModel, previous_state: ExecutionState, reason: str = None) -> None:
        """
        Emit state changed event.
        
        Args:
            execution: Execution model
            previous_state: Previous state
            reason: Reason for state change
        """
        # Implementation
        
    async def emit_progress_updated(self, execution: AgentExecutionModel) -> None:
        """
        Emit progress updated event.
        
        Args:
            execution: Execution model
        """
        # Implementation
        
    async def emit_execution_completed(self, execution: AgentExecutionModel) -> None:
        """
        Emit execution completed event.
        
        Args:
            execution: Execution model
        """
        # Implementation
```

## Testing Strategy

### Unit Testing

#### Repository Tests
- Mock the database session
- Test all CRUD operations
- Test error handling
- Test transaction management

#### StateManager Tests
- Mock repository and event emitter
- Test state transition validation
- Test state change logic
- Test side effect handling

#### TaskRunner Tests
- Mock repository, state manager, progress tracker, and command bus
- Test task preparation
- Test model service integration
- Test result processing
- Test error handling

#### ProgressTracker Tests
- Mock repository and event emitter
- Test progress updates
- Test error handling

#### BackgroundManager Tests
- Test task creation
- Test task cancellation
- Test task cleanup

#### EventEmitter Tests
- Mock event bus
- Test event payload formatting
- Test event publishing

### Integration Testing

#### State Transition Flow Tests
- Test full state transition lifecycle
- Test concurrent modifications
- Test transaction handling

#### Task Execution Flow Tests
- Test task execution through the entire service
- Test progress updates during execution
- Test result submission

#### Error Handling Tests
- Test service recovery from errors
- Test database transaction rollbacks
- Test error propagation

## Development Guidelines

### Error Handling Principles

1. **Explicit exceptions**: Use specific exception types for different error cases
2. **Consistent error handling pattern**:
   ```python
   try:
       # Code that might fail
   except SpecificError as e:
       # Handle specific error
       raise AppropriateException(details) from e
   except Exception as e:
       # Handle unexpected errors
       logger.error(f"Unexpected error: {str(e)}")
       raise DatabaseError(f"Operation failed: {str(e)}") from e
   ```
3. **Transaction management**:
   ```python
   try:
       # Database operations
       await self.db.commit()
   except Exception as e:
       await self.db.rollback()
       # Error handling
       raise
   ```
4. **Logging context**: Include relevant identifiers in error logs
   ```python
   logger.error(f"Error processing execution {execution_id}: {str(e)}")
   ```

### Event Publishing Standards

1. **Consistent event types**: Use consistent naming patterns for events
   - `agent.execution.state_changed`
   - `agent.execution.progress`
   - `agent.execution.completed`

2. **Complete event payloads**: Include all relevant information in event payloads
   ```python
   payload = {
       "execution_id": str(execution_id),
       "agent_id": str(execution.agent_id),
       "task_id": str(execution.task_id),
       "previous_state": previous_state.value,
       "new_state": new_state.value,
       "reason": reason,
   }
   ```

3. **Asynchronous handling**: Don't block on event publishing
   ```python
   await self.event_bus.publish_event("agent.execution.state_changed", payload)
   ```

### Performance Considerations

1. **Efficient database queries**:
   - Use specific columns in SELECT statements when possible
   - Use appropriate indexes
   - Minimize the number of queries

2. **Optimistic concurrency control**:
   ```python
   update_stmt = (
       update(AgentExecutionModel)
       .where(
           AgentExecutionModel.id == execution_id,
           AgentExecutionModel.state == current_state
       )
       .values(
           state=target_state,
           updated_at=datetime.utcnow()
       )
       .returning(AgentExecutionModel)
   )
   ```

3. **Resource cleanup**:
   ```python
   try:
       # Use resources
   finally:
       # Clean up resources
       if execution_id in self._running_tasks:
           del self._running_tasks[execution_id]
   ```

4. **Background task management**:
   - Limit the number of concurrent tasks
   - Monitor task memory usage
   - Implement timeouts for long-running tasks

## Extension Guide

### Adding New Execution States

1. Update the `ExecutionState` enum in `models/api.py`:
   ```python
   class ExecutionState(str, Enum):
       # Existing states
       NEW_STATE = "NEW_STATE"
   ```

2. Update the transition rules in `ExecutionStateTransitionValidator`:
   ```python
   VALID_TRANSITIONS = {
       # Existing transitions
       ExecutionState.EXISTING_STATE: {ExecutionState.NEW_STATE, ...},
       ExecutionState.NEW_STATE: {ExecutionState.SOME_OTHER_STATE, ...},
   }
   ```

3. Add handling for the new state in the `ExecutionStateManager`:
   ```python
   async def handle_state_side_effects(self, execution, previous_state, new_state):
       # Existing handling
       if new_state == ExecutionState.NEW_STATE:
           # Handle new state
   ```

### Adding New Task Types

1. Extend the `TaskRunner` with a new method for the task type:
   ```python
   async def execute_specialized_task(self, execution):
       # Specialized task logic
   ```

2. Update the main execution method to handle the new task type:
   ```python
   async def execute_task(self, execution):
       task_type = execution.parameters.get("type")
       if task_type == "specialized":
           await self.execute_specialized_task(execution)
       else:
           await self.execute_standard_task(execution)
   ```

3. Add appropriate progress tracking for the new task type:
   ```python
   specific_steps = ["Initialize", "SpecialStep1", "SpecialStep2", "Finalize"]
   ```

## Migration Strategy

### Phase 1: Create the Module Structure

1. Create the directory structure:
   ```
   services/agent-orchestrator/src/services/execution/
   ├── __init__.py
   ├── repository.py
   ├── state_manager.py
   ├── task_runner.py
   ├── progress_tracker.py
   ├── background_manager.py
   ├── event_emitter.py
   └── service.py
   ```

2. Move the existing service to the new module:
   ```python
   # services/agent-orchestrator/src/services/execution/__init__.py
   from .service import ExecutionService
   
   __all__ = ["ExecutionService"]
   ```

### Phase 2: Extract Components

1. Extract the repository component first (data access layer)
2. Extract the state manager next (core state management)
3. Extract the task runner (execution logic)
4. Extract the progress tracker (progress tracking)
5. Extract the background task manager (async task handling)
6. Extract the event emitter (event publishing)

### Phase 3: Implement the Facade Service

1. Implement the main service that uses all components:
   ```python
   class ExecutionService:
       def __init__(self, db, event_bus, command_bus, settings):
           # Initialize components
           self.repository = ExecutionRepository(db)
           self.event_emitter = ExecutionEventEmitter(event_bus)
           self.state_manager = ExecutionStateManager(self.repository, self.event_emitter)
           # ...
   ```

2. Implement public API methods that delegate to components:
   ```python
   async def get_execution(self, execution_id):
       return await self.repository.get_by_id(execution_id)
       
   async def start_execution(self, execution_id):
       # Coordinate between components
   ```

### Phase 4: Update Dependencies and Integration

1. Update `dependencies.py` to provide the new service
2. Update any services that depend on the execution service
3. Ensure all tests pass with the new implementation
