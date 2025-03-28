from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional
from uuid import UUID

from ..dependencies import get_agent_service, get_current_user, get_optional_user
from ..exceptions import AgentNotFoundError, AgentConfigurationError, TemplateNotFoundError
from ..models.api import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentList,
    AgentExecutionRequest,
    AgentExecutionResponse,
    UserInfo,
)
from ..services.agent_service import AgentService

router = APIRouter()


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent",
    description="Create a new agent with the provided data.",
)
async def create_agent(
    agent: AgentCreate,
    current_user: UserInfo = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """
    Create a new agent.
    
    Args:
        agent: Agent data
        current_user: Current authenticated user
        agent_service: Agent service
        
    Returns:
        AgentResponse: Created agent
        
    Raises:
        AgentConfigurationError: If agent configuration is invalid
        TemplateNotFoundError: If template not found
    """
    try:
        return await agent_service.create_agent(agent)
    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AgentConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=AgentList,
    summary="List agents",
    description="Get a paginated list of agents with optional filtering.",
)
async def list_agents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    state: Optional[str] = Query(None, description="Filter by state"),
    type: Optional[str] = Query(None, description="Filter by type"),
    search: Optional[str] = Query(None, description="Search term"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentList:
    """
    List agents with pagination and filtering.
    
    Args:
        page: Page number
        page_size: Page size
        project_id: Filter by project ID
        state: Filter by state
        type: Filter by type
        search: Search term
        current_user: Current authenticated user (optional)
        agent_service: Agent service
        
    Returns:
        AgentList: Paginated list of agents
    """
    # Get agents
    agents, total = await agent_service.list_agents(
        page=page,
        page_size=page_size,
        project_id=project_id,
        state=state,
        type=type,
        search=search,
    )
    
    # Return paginated list
    return AgentList(
        items=agents,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Get agent",
    description="Get an agent by ID.",
)
async def get_agent(
    agent_id: UUID = Path(..., description="Agent ID"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """
    Get an agent by ID.
    
    Args:
        agent_id: Agent ID
        current_user: Current authenticated user (optional)
        agent_service: Agent service
        
    Returns:
        AgentResponse: Agent
        
    Raises:
        AgentNotFoundError: If agent not found
    """
    # Get agent
    agent = await agent_service.get_agent(agent_id)
    
    # Check if agent exists
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )
    
    return agent


@router.put(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Update agent",
    description="Update an agent by ID.",
)
async def update_agent(
    agent_update: AgentUpdate,
    agent_id: UUID = Path(..., description="Agent ID"),
    current_user: UserInfo = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """
    Update an agent by ID.
    
    Args:
        agent_update: Agent update data
        agent_id: Agent ID
        current_user: Current authenticated user
        agent_service: Agent service
        
    Returns:
        AgentResponse: Updated agent
        
    Raises:
        AgentNotFoundError: If agent not found
        AgentConfigurationError: If agent configuration is invalid
    """
    try:
        return await agent_service.update_agent(agent_id, agent_update)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )
    except AgentConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete agent",
    description="Delete an agent by ID.",
)
async def delete_agent(
    agent_id: UUID = Path(..., description="Agent ID"),
    current_user: UserInfo = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> None:
    """
    Delete an agent by ID.
    
    Args:
        agent_id: Agent ID
        current_user: Current authenticated user
        agent_service: Agent service
        
    Raises:
        AgentNotFoundError: If agent not found
    """
    try:
        await agent_service.delete_agent(agent_id)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )


@router.post(
    "/{agent_id}/execute",
    response_model=AgentExecutionResponse,
    summary="Execute agent",
    description="Execute an agent on a task.",
)
async def execute_agent(
    execution_request: AgentExecutionRequest,
    agent_id: UUID = Path(..., description="Agent ID"),
    current_user: UserInfo = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentExecutionResponse:
    """
    Execute an agent on a task.
    
    Args:
        execution_request: Execution request
        agent_id: Agent ID
        current_user: Current authenticated user
        agent_service: Agent service
        
    Returns:
        AgentExecutionResponse: Execution response
        
    Raises:
        AgentNotFoundError: If agent not found
        AgentConfigurationError: If agent configuration is invalid
    """
    try:
        return await agent_service.execute_agent(agent_id, execution_request)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )
    except AgentConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
