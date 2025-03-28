"""
Agent specialization router.

This module contains the API endpoints for agent specializations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional
from uuid import UUID

from shared.models.src.enums import AgentType

from ..dependencies import get_current_user, get_admin_user, get_optional_user
from ..exceptions import (
    SpecializationNotFoundError,
    DatabaseError,
)
from ..models.api import (
    UserInfo,
)
from ..models.requirement_analysis import (
    AgentSpecializationRequirement,
)
from ..dependencies import get_agent_specialization_service

router = APIRouter()


@router.get(
    "",
    response_model=List[AgentSpecializationRequirement],
    summary="List agent specializations",
    description="Get a list of all agent specializations.",
)
async def list_specializations(
    specialization_service = Depends(get_agent_specialization_service),
) -> List[AgentSpecializationRequirement]:
    """
    List all agent specializations.
    
    Args:
        specialization_service: Agent specialization service
        
    Returns:
        List[AgentSpecializationRequirement]: List of agent specializations
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        return await specialization_service.list_agent_specializations()
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{agent_type}",
    response_model=AgentSpecializationRequirement,
    summary="Get agent specialization",
    description="Get an agent specialization by agent type.",
)
async def get_specialization(
    agent_type: str = Path(..., description="Agent type"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    specialization_service = Depends(get_agent_specialization_service),
) -> AgentSpecializationRequirement:
    """
    Get an agent specialization by agent type.
    
    Args:
        agent_type: Agent type
        current_user: Current authenticated user (optional)
        specialization_service: Agent specialization service
        
    Returns:
        AgentSpecializationRequirement: Agent specialization
        
    Raises:
        SpecializationNotFoundError: If specialization not found
        DatabaseError: If database operation fails
    """
    try:
        # Convert string to enum
        agent_type_enum = AgentType(agent_type)
        
        # Get specialization
        specialization = await specialization_service.get_agent_specialization(agent_type_enum)
        
        # Check if specialization exists
        if not specialization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Specialization for agent type {agent_type} not found",
            )
        
        return specialization
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid agent type: {agent_type}",
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "",
    response_model=AgentSpecializationRequirement,
    status_code=status.HTTP_201_CREATED,
    summary="Create agent specialization",
    description="Create a new agent specialization.",
)
async def create_specialization(
    specialization: AgentSpecializationRequirement,
    current_user: UserInfo = Depends(get_admin_user),  # Only admins can create specializations
    specialization_service = Depends(get_agent_specialization_service),
) -> AgentSpecializationRequirement:
    """
    Create a new agent specialization.
    
    Args:
        specialization: Agent specialization
        current_user: Current authenticated admin user
        specialization_service: Agent specialization service
        
    Returns:
        AgentSpecializationRequirement: Created specialization
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        return await specialization_service.create_agent_specialization(specialization)
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.put(
    "/{agent_type}",
    response_model=AgentSpecializationRequirement,
    summary="Update agent specialization",
    description="Update an agent specialization by agent type.",
)
async def update_specialization(
    specialization: AgentSpecializationRequirement,
    agent_type: str = Path(..., description="Agent type"),
    current_user: UserInfo = Depends(get_admin_user),  # Only admins can update specializations
    specialization_service = Depends(get_agent_specialization_service),
) -> AgentSpecializationRequirement:
    """
    Update an agent specialization by agent type.
    
    Args:
        specialization: Agent specialization
        agent_type: Agent type
        current_user: Current authenticated admin user
        specialization_service: Agent specialization service
        
    Returns:
        AgentSpecializationRequirement: Updated specialization
        
    Raises:
        SpecializationNotFoundError: If specialization not found
        DatabaseError: If database operation fails
    """
    try:
        # Convert string to enum
        agent_type_enum = AgentType(agent_type)
        
        # Check if agent type matches
        if agent_type_enum != specialization.agent_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent type in path ({agent_type}) does not match agent type in body ({specialization.agent_type.value})",
            )
        
        # Update specialization
        return await specialization_service.update_agent_specialization(agent_type_enum, specialization)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid agent type: {agent_type}",
        )
    except SpecializationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specialization for agent type {agent_type} not found",
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete(
    "/{agent_type}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete agent specialization",
    description="Delete an agent specialization by agent type.",
)
async def delete_specialization(
    agent_type: str = Path(..., description="Agent type"),
    current_user: UserInfo = Depends(get_admin_user),  # Only admins can delete specializations
    specialization_service = Depends(get_agent_specialization_service),
) -> None:
    """
    Delete an agent specialization by agent type.
    
    Args:
        agent_type: Agent type
        current_user: Current authenticated admin user
        specialization_service: Agent specialization service
        
    Raises:
        SpecializationNotFoundError: If specialization not found
        DatabaseError: If database operation fails
    """
    try:
        # Convert string to enum
        agent_type_enum = AgentType(agent_type)
        
        # Delete specialization
        await specialization_service.delete_agent_specialization(agent_type_enum)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid agent type: {agent_type}",
        )
    except SpecializationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specialization for agent type {agent_type} not found",
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
