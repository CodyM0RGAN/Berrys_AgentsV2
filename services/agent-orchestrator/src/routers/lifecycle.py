from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional
from uuid import UUID

from ..dependencies import get_lifecycle_manager, get_current_user, get_optional_user
from ..exceptions import (
    AgentNotFoundError,
    InvalidAgentStateError,
    AgentExecutionError,
    ConcurrentModificationError,
)
from ..models.api import (
    AgentStatusChangeRequest,
    AgentResponse,
    AgentStateHistoryItem,
    UserInfo,
)
from ..services.lifecycle_manager import LifecycleManager

router = APIRouter()


@router.post(
    "/{agent_id}/status",
    response_model=AgentResponse,
    summary="Change agent status",
    description="Change an agent's status.",
)
async def change_agent_status(
    status_change: AgentStatusChangeRequest,
    agent_id: UUID = Path(..., description="Agent ID"),
    current_user: UserInfo = Depends(get_current_user),
    lifecycle_manager: LifecycleManager = Depends(get_lifecycle_manager),
) -> AgentResponse:
    """
    Change an agent's status.
    
    Args:
        status_change: Status change request
        agent_id: Agent ID
        current_user: Current authenticated user
        lifecycle_manager: Lifecycle manager
        
    Returns:
        AgentResponse: Updated agent
        
    Raises:
        AgentNotFoundError: If agent not found
        InvalidAgentStateError: If state transition is invalid
        ConcurrentModificationError: If agent was modified concurrently
    """
    try:
        agent = await lifecycle_manager.change_agent_state(agent_id, status_change)
        return AgentResponse.from_orm(agent)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )
    except InvalidAgentStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ConcurrentModificationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post(
    "/{agent_id}/initialize",
    response_model=AgentResponse,
    summary="Initialize agent",
    description="Initialize an agent.",
)
async def initialize_agent(
    agent_id: UUID = Path(..., description="Agent ID"),
    reason: Optional[str] = Query(None, description="Reason for initialization"),
    current_user: UserInfo = Depends(get_current_user),
    lifecycle_manager: LifecycleManager = Depends(get_lifecycle_manager),
) -> AgentResponse:
    """
    Initialize an agent.
    
    Args:
        agent_id: Agent ID
        reason: Reason for initialization
        current_user: Current authenticated user
        lifecycle_manager: Lifecycle manager
        
    Returns:
        AgentResponse: Updated agent
        
    Raises:
        AgentNotFoundError: If agent not found
        InvalidAgentStateError: If state transition is invalid
        AgentExecutionError: If initialization fails
    """
    try:
        agent = await lifecycle_manager.initialize_agent(agent_id, reason)
        return AgentResponse.from_orm(agent)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )
    except InvalidAgentStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AgentExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{agent_id}/activate",
    response_model=AgentResponse,
    summary="Activate agent",
    description="Activate an agent.",
)
async def activate_agent(
    agent_id: UUID = Path(..., description="Agent ID"),
    reason: Optional[str] = Query(None, description="Reason for activation"),
    current_user: UserInfo = Depends(get_current_user),
    lifecycle_manager: LifecycleManager = Depends(get_lifecycle_manager),
) -> AgentResponse:
    """
    Activate an agent.
    
    Args:
        agent_id: Agent ID
        reason: Reason for activation
        current_user: Current authenticated user
        lifecycle_manager: Lifecycle manager
        
    Returns:
        AgentResponse: Updated agent
        
    Raises:
        AgentNotFoundError: If agent not found
        InvalidAgentStateError: If state transition is invalid
        AgentExecutionError: If activation fails
    """
    try:
        agent = await lifecycle_manager.activate_agent(agent_id, reason)
        return AgentResponse.from_orm(agent)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )
    except InvalidAgentStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AgentExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{agent_id}/pause",
    response_model=AgentResponse,
    summary="Pause agent",
    description="Pause an agent.",
)
async def pause_agent(
    agent_id: UUID = Path(..., description="Agent ID"),
    reason: Optional[str] = Query(None, description="Reason for pausing"),
    current_user: UserInfo = Depends(get_current_user),
    lifecycle_manager: LifecycleManager = Depends(get_lifecycle_manager),
) -> AgentResponse:
    """
    Pause an agent.
    
    Args:
        agent_id: Agent ID
        reason: Reason for pausing
        current_user: Current authenticated user
        lifecycle_manager: Lifecycle manager
        
    Returns:
        AgentResponse: Updated agent
        
    Raises:
        AgentNotFoundError: If agent not found
        InvalidAgentStateError: If state transition is invalid
        AgentExecutionError: If pausing fails
    """
    try:
        agent = await lifecycle_manager.pause_agent(agent_id, reason)
        return AgentResponse.from_orm(agent)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )
    except InvalidAgentStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AgentExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{agent_id}/terminate",
    response_model=AgentResponse,
    summary="Terminate agent",
    description="Terminate an agent.",
)
async def terminate_agent(
    agent_id: UUID = Path(..., description="Agent ID"),
    reason: Optional[str] = Query(None, description="Reason for termination"),
    current_user: UserInfo = Depends(get_current_user),
    lifecycle_manager: LifecycleManager = Depends(get_lifecycle_manager),
) -> AgentResponse:
    """
    Terminate an agent.
    
    Args:
        agent_id: Agent ID
        reason: Reason for termination
        current_user: Current authenticated user
        lifecycle_manager: Lifecycle manager
        
    Returns:
        AgentResponse: Updated agent
        
    Raises:
        AgentNotFoundError: If agent not found
        InvalidAgentStateError: If state transition is invalid
        AgentExecutionError: If termination fails
    """
    try:
        agent = await lifecycle_manager.terminate_agent(agent_id, reason)
        return AgentResponse.from_orm(agent)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )
    except InvalidAgentStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AgentExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{agent_id}/history",
    response_model=List[AgentStateHistoryItem],
    summary="Get agent state history",
    description="Get an agent's state history.",
)
async def get_agent_state_history(
    agent_id: UUID = Path(..., description="Agent ID"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of history entries to return"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    lifecycle_manager: LifecycleManager = Depends(get_lifecycle_manager),
) -> List[AgentStateHistoryItem]:
    """
    Get an agent's state history.
    
    Args:
        agent_id: Agent ID
        limit: Maximum number of history entries to return
        current_user: Current authenticated user (optional)
        lifecycle_manager: Lifecycle manager
        
    Returns:
        List[AgentStateModel]: Agent state history
        
    Raises:
        AgentNotFoundError: If agent not found
    """
    try:
        history = await lifecycle_manager.get_agent_state_history(agent_id, limit)
        return [AgentStateHistoryItem.from_orm(item) for item in history]
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )
