from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import Dict, Any, Optional
from uuid import UUID

from ..dependencies import get_state_manager, get_current_user, get_optional_user
from ..exceptions import (
    AgentNotFoundError,
    AgentStateError,
)
from ..models.api import UserInfo
from ..services.state_manager import StateManager

router = APIRouter()


@router.get(
    "/{agent_id}/state",
    response_model=Dict[str, Any],
    summary="Get agent state",
    description="Get an agent's runtime state.",
)
async def get_agent_state(
    agent_id: UUID = Path(..., description="Agent ID"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    state_manager: StateManager = Depends(get_state_manager),
) -> Dict[str, Any]:
    """
    Get an agent's runtime state.
    
    Args:
        agent_id: Agent ID
        current_user: Current authenticated user (optional)
        state_manager: State manager
        
    Returns:
        Dict[str, Any]: Agent state
        
    Raises:
        AgentNotFoundError: If agent not found
    """
    try:
        state = await state_manager.get_agent_state(agent_id)
        
        if state is None:
            return {}
        
        return state
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )


@router.put(
    "/{agent_id}/state",
    response_model=Dict[str, Any],
    summary="Update agent state",
    description="Update an agent's runtime state.",
)
async def update_agent_state(
    state_update: Dict[str, Any],
    agent_id: UUID = Path(..., description="Agent ID"),
    create_checkpoint: bool = Query(False, description="Whether to create a checkpoint"),
    current_user: UserInfo = Depends(get_current_user),
    state_manager: StateManager = Depends(get_state_manager),
) -> Dict[str, Any]:
    """
    Update an agent's runtime state.
    
    Args:
        state_update: State update
        agent_id: Agent ID
        create_checkpoint: Whether to create a checkpoint
        current_user: Current authenticated user
        state_manager: State manager
        
    Returns:
        Dict[str, Any]: Updated state
        
    Raises:
        AgentNotFoundError: If agent not found
        AgentStateError: If state update fails
    """
    try:
        return await state_manager.update_agent_state(
            agent_id,
            state_update,
            create_checkpoint,
        )
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )
    except AgentStateError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{agent_id}/checkpoint",
    response_model=Dict[str, Any],
    summary="Create checkpoint",
    description="Create a checkpoint for an agent's state.",
)
async def create_checkpoint(
    agent_id: UUID = Path(..., description="Agent ID"),
    state_data: Optional[Dict[str, Any]] = None,
    is_recoverable: bool = Query(True, description="Whether the checkpoint is recoverable"),
    current_user: UserInfo = Depends(get_current_user),
    state_manager: StateManager = Depends(get_state_manager),
) -> Dict[str, Any]:
    """
    Create a checkpoint for an agent's state.
    
    Args:
        agent_id: Agent ID
        state_data: State data to checkpoint (if None, use current state)
        is_recoverable: Whether the checkpoint is recoverable
        current_user: Current authenticated user
        state_manager: State manager
        
    Returns:
        Dict[str, Any]: Checkpoint information
        
    Raises:
        AgentNotFoundError: If agent not found
        AgentStateError: If checkpoint creation fails
    """
    try:
        # If state_data is not provided, get current state
        if state_data is None:
            state_data = await state_manager.get_agent_state(agent_id)
            
            if state_data is None:
                state_data = {}
        
        # Create checkpoint
        checkpoint = await state_manager.create_checkpoint(
            agent_id,
            state_data,
            is_recoverable,
        )
        
        # Return checkpoint information
        return {
            "checkpoint_id": str(checkpoint.id),
            "agent_id": str(checkpoint.agent_id),
            "sequence_number": checkpoint.sequence_number,
            "is_recoverable": checkpoint.is_recoverable,
            "created_at": checkpoint.created_at.isoformat(),
        }
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )
    except AgentStateError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete(
    "/{agent_id}/checkpoint",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete checkpoint",
    description="Delete the checkpoint for an agent.",
)
async def delete_checkpoint(
    agent_id: UUID = Path(..., description="Agent ID"),
    current_user: UserInfo = Depends(get_current_user),
    state_manager: StateManager = Depends(get_state_manager),
) -> None:
    """
    Delete the checkpoint for an agent.
    
    Args:
        agent_id: Agent ID
        current_user: Current authenticated user
        state_manager: State manager
        
    Raises:
        AgentNotFoundError: If agent not found
    """
    try:
        await state_manager.delete_checkpoint(agent_id)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )


@router.post(
    "/{agent_id}/schedule-checkpoint",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Schedule checkpoint",
    description="Schedule a checkpoint for an agent.",
)
async def schedule_checkpoint(
    agent_id: UUID = Path(..., description="Agent ID"),
    current_user: UserInfo = Depends(get_current_user),
    state_manager: StateManager = Depends(get_state_manager),
) -> None:
    """
    Schedule a checkpoint for an agent.
    
    Args:
        agent_id: Agent ID
        current_user: Current authenticated user
        state_manager: State manager
        
    Raises:
        AgentNotFoundError: If agent not found
    """
    try:
        await state_manager.schedule_checkpoint(agent_id)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )
