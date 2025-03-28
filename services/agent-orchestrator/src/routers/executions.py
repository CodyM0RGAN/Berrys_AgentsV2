from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..dependencies import get_execution_service, get_current_user, get_optional_user
from ..exceptions import (
    AgentNotFoundError,
    ExecutionNotFoundError,
    InvalidExecutionStateError,
    ConcurrentModificationError,
    DatabaseError,
)
from ..models.api import (
    ExecutionState,
    ExecutionStatusChangeRequest,
    ExecutionProgressUpdate,
    ExecutionResultRequest,
    ExecutionResponse,
    ExecutionStateHistoryItem,
    UserInfo,
)
from ..services.execution_service import ExecutionService

router = APIRouter()


@router.get(
    "/{execution_id}",
    response_model=Dict[str, Any],
    summary="Get execution",
    description="Get execution details by ID.",
)
async def get_execution(
    execution_id: UUID = Path(..., description="Execution ID"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    execution_service: ExecutionService = Depends(get_execution_service),
) -> Dict[str, Any]:
    """
    Get execution details.
    
    Args:
        execution_id: Execution ID
        current_user: Current authenticated user (optional)
        execution_service: Execution service
        
    Returns:
        Dict[str, Any]: Execution details
        
    Raises:
        HTTPException: If execution not found
    """
    # Get execution
    execution = await execution_service.get_execution(execution_id)
    
    # Check if execution exists
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution with ID {execution_id} not found",
        )
    
    # Convert to dictionary
    return execution.to_dict()


@router.get(
    "/agent/{agent_id}/executions",
    response_model=Dict[str, Any],
    summary="List executions",
    description="List executions for an agent with filtering and pagination.",
)
async def list_executions(
    agent_id: UUID = Path(..., description="Agent ID"),
    task_id: Optional[UUID] = Query(None, description="Filter by task ID"),
    state: Optional[str] = Query(None, description="Filter by state"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    execution_service: ExecutionService = Depends(get_execution_service),
) -> Dict[str, Any]:
    """
    List executions for an agent with filtering and pagination.
    
    Args:
        agent_id: Agent ID
        task_id: Filter by task ID (optional)
        state: Filter by state (optional)
        page: Page number
        page_size: Page size
        current_user: Current authenticated user (optional)
        execution_service: Execution service
        
    Returns:
        Dict[str, Any]: List of executions with pagination info
    """
    try:
        # Convert state string to enum if provided
        state_enum = None
        if state:
            try:
                state_enum = ExecutionState(state)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid state: {state}",
                )
        
        # Get executions
        executions, total = await execution_service.list_executions(
            agent_id=agent_id,
            task_id=task_id,
            state=state_enum,
            page=page,
            page_size=page_size,
        )
        
        # Convert executions to dictionaries
        executions_data = [execution.to_dict() for execution in executions]
        
        # Return paginated list
        return {
            "items": executions_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }
    except Exception as e:
        # Handle errors
        if isinstance(e, HTTPException):
            raise e
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{execution_id}/state",
    response_model=Dict[str, Any],
    summary="Change execution state",
    description="Change the state of an execution.",
)
async def change_execution_state(
    status_change: ExecutionStatusChangeRequest,
    execution_id: UUID = Path(..., description="Execution ID"),
    current_user: UserInfo = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service),
) -> Dict[str, Any]:
    """
    Change execution state.
    
    Args:
        status_change: Status change request
        execution_id: Execution ID
        current_user: Current authenticated user
        execution_service: Execution service
        
    Returns:
        Dict[str, Any]: Updated execution
        
    Raises:
        HTTPException: If execution not found or state transition invalid
    """
    try:
        execution = await execution_service.change_execution_state(execution_id, status_change)
        return execution.to_dict()
    except ExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidExecutionStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ConcurrentModificationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{execution_id}/start",
    response_model=Dict[str, Any],
    summary="Start execution",
    description="Start an execution.",
)
async def start_execution(
    execution_id: UUID = Path(..., description="Execution ID"),
    current_user: UserInfo = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service),
) -> Dict[str, Any]:
    """
    Start execution.
    
    Args:
        execution_id: Execution ID
        current_user: Current authenticated user
        execution_service: Execution service
        
    Returns:
        Dict[str, Any]: Updated execution
        
    Raises:
        HTTPException: If execution not found or state transition invalid
    """
    try:
        execution = await execution_service.start_execution(execution_id)
        return execution.to_dict()
    except ExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidExecutionStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{execution_id}/pause",
    response_model=Dict[str, Any],
    summary="Pause execution",
    description="Pause a running execution.",
)
async def pause_execution(
    execution_id: UUID = Path(..., description="Execution ID"),
    reason: Optional[str] = Query(None, description="Reason for pausing"),
    current_user: UserInfo = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service),
) -> Dict[str, Any]:
    """
    Pause execution.
    
    Args:
        execution_id: Execution ID
        reason: Reason for pausing (optional)
        current_user: Current authenticated user
        execution_service: Execution service
        
    Returns:
        Dict[str, Any]: Updated execution
        
    Raises:
        HTTPException: If execution not found or state transition invalid
    """
    try:
        execution = await execution_service.pause_execution(execution_id, reason)
        return execution.to_dict()
    except ExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidExecutionStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{execution_id}/resume",
    response_model=Dict[str, Any],
    summary="Resume execution",
    description="Resume a paused execution.",
)
async def resume_execution(
    execution_id: UUID = Path(..., description="Execution ID"),
    current_user: UserInfo = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service),
) -> Dict[str, Any]:
    """
    Resume execution.
    
    Args:
        execution_id: Execution ID
        current_user: Current authenticated user
        execution_service: Execution service
        
    Returns:
        Dict[str, Any]: Updated execution
        
    Raises:
        HTTPException: If execution not found or state transition invalid
    """
    try:
        execution = await execution_service.resume_execution(execution_id)
        return execution.to_dict()
    except ExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidExecutionStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{execution_id}/cancel",
    response_model=Dict[str, Any],
    summary="Cancel execution",
    description="Cancel an execution.",
)
async def cancel_execution(
    execution_id: UUID = Path(..., description="Execution ID"),
    reason: Optional[str] = Query(None, description="Reason for cancellation"),
    current_user: UserInfo = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service),
) -> Dict[str, Any]:
    """
    Cancel execution.
    
    Args:
        execution_id: Execution ID
        reason: Reason for cancellation (optional)
        current_user: Current authenticated user
        execution_service: Execution service
        
    Returns:
        Dict[str, Any]: Updated execution
        
    Raises:
        HTTPException: If execution not found
    """
    try:
        execution = await execution_service.cancel_execution(execution_id, reason)
        return execution.to_dict()
    except ExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{execution_id}/retry",
    response_model=Dict[str, Any],
    summary="Retry execution",
    description="Retry a failed execution.",
)
async def retry_execution(
    execution_id: UUID = Path(..., description="Execution ID"),
    current_user: UserInfo = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service),
) -> Dict[str, Any]:
    """
    Retry execution.
    
    Args:
        execution_id: Execution ID
        current_user: Current authenticated user
        execution_service: Execution service
        
    Returns:
        Dict[str, Any]: Updated execution
        
    Raises:
        HTTPException: If execution not found or state transition invalid
    """
    try:
        execution = await execution_service.retry_execution(execution_id)
        return execution.to_dict()
    except ExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidExecutionStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{execution_id}/progress",
    response_model=Dict[str, Any],
    summary="Update execution progress",
    description="Update the progress of an execution.",
)
async def update_execution_progress(
    progress_update: ExecutionProgressUpdate,
    execution_id: UUID = Path(..., description="Execution ID"),
    current_user: UserInfo = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service),
) -> Dict[str, Any]:
    """
    Update execution progress.
    
    Args:
        progress_update: Progress update
        execution_id: Execution ID
        current_user: Current authenticated user
        execution_service: Execution service
        
    Returns:
        Dict[str, Any]: Updated execution
        
    Raises:
        HTTPException: If execution not found or state transition invalid
    """
    try:
        execution = await execution_service.update_progress(execution_id, progress_update)
        return execution.to_dict()
    except ExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidExecutionStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{execution_id}/result",
    response_model=Dict[str, Any],
    summary="Submit execution result",
    description="Submit the result of an execution.",
)
async def submit_execution_result(
    result_request: ExecutionResultRequest,
    execution_id: UUID = Path(..., description="Execution ID"),
    current_user: UserInfo = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service),
) -> Dict[str, Any]:
    """
    Submit execution result.
    
    Args:
        result_request: Result request
        execution_id: Execution ID
        current_user: Current authenticated user
        execution_service: Execution service
        
    Returns:
        Dict[str, Any]: Updated execution
        
    Raises:
        HTTPException: If execution not found or state transition invalid
    """
    try:
        execution = await execution_service.submit_result(execution_id, result_request)
        return execution.to_dict()
    except ExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidExecutionStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{execution_id}/state-history",
    response_model=List[Dict[str, Any]],
    summary="Get execution state history",
    description="Get the state history of an execution.",
)
async def get_execution_state_history(
    execution_id: UUID = Path(..., description="Execution ID"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of history entries to return"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    execution_service: ExecutionService = Depends(get_execution_service),
) -> List[Dict[str, Any]]:
    """
    Get execution state history.
    
    Args:
        execution_id: Execution ID
        limit: Maximum number of history entries to return
        current_user: Current authenticated user (optional)
        execution_service: Execution service
        
    Returns:
        List[Dict[str, Any]]: Execution state history
        
    Raises:
        HTTPException: If execution not found
    """
    try:
        # Get state history
        state_history = await execution_service.get_execution_state_history(execution_id, limit)
        
        # Convert to dictionaries
        return [
            {
                "id": str(item.id),
                "execution_id": str(item.execution_id),
                "previous_state": item.previous_state.value if item.previous_state else None,
                "new_state": item.new_state.value,
                "reason": item.reason,
                "timestamp": item.timestamp.isoformat(),
            }
            for item in state_history
        ]
    except ExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete(
    "/{execution_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete execution",
    description="Delete an execution.",
)
async def delete_execution(
    execution_id: UUID = Path(..., description="Execution ID"),
    current_user: UserInfo = Depends(get_current_user),
    execution_service: ExecutionService = Depends(get_execution_service),
) -> None:
    """
    Delete execution.
    
    Args:
        execution_id: Execution ID
        current_user: Current authenticated user
        execution_service: Execution service
        
    Raises:
        HTTPException: If execution not found
    """
    try:
        await execution_service.delete_execution(execution_id)
    except ExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
