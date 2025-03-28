from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..dependencies import get_communication_service, get_current_user, get_optional_user
from ..exceptions import (
    AgentNotFoundError,
    AgentCommunicationError,
)
from ..models.api import (
    AgentCommunicationRequest,
    AgentCommunicationResponse,
    UserInfo,
)
from ..models.internal import AgentCommunicationModel
from ..services.communication_service import CommunicationService

router = APIRouter()


@router.post(
    "/{agent_id}/send",
    response_model=AgentCommunicationResponse,
    summary="Send communication",
    description="Send a communication from one agent to another.",
)
async def send_communication(
    communication_request: AgentCommunicationRequest,
    agent_id: UUID = Path(..., description="Sender agent ID"),
    current_user: UserInfo = Depends(get_current_user),
    communication_service: CommunicationService = Depends(get_communication_service),
) -> AgentCommunicationResponse:
    """
    Send a communication from one agent to another.
    
    Args:
        communication_request: Communication request
        agent_id: Sender agent ID
        current_user: Current authenticated user
        communication_service: Communication service
        
    Returns:
        AgentCommunicationResponse: Communication response
        
    Raises:
        AgentNotFoundError: If agent not found
        AgentCommunicationError: If communication fails
    """
    try:
        return await communication_service.send_communication(agent_id, communication_request)
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AgentCommunicationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/communications/{communication_id}/delivered",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark as delivered",
    description="Mark a communication as delivered.",
)
async def mark_as_delivered(
    communication_id: UUID = Path(..., description="Communication ID"),
    current_user: UserInfo = Depends(get_current_user),
    communication_service: CommunicationService = Depends(get_communication_service),
) -> None:
    """
    Mark a communication as delivered.
    
    Args:
        communication_id: Communication ID
        current_user: Current authenticated user
        communication_service: Communication service
        
    Raises:
        AgentCommunicationError: If communication not found
    """
    try:
        await communication_service.mark_as_delivered(communication_id)
    except AgentCommunicationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{agent_id}/communications",
    response_model=Dict[str, Any],
    summary="Get communications",
    description="Get communications for an agent.",
)
async def get_communications(
    agent_id: UUID = Path(..., description="Agent ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    direction: str = Query("both", description="Direction of communications ('sent', 'received', or 'both')"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    communication_service: CommunicationService = Depends(get_communication_service),
) -> Dict[str, Any]:
    """
    Get communications for an agent.
    
    Args:
        agent_id: Agent ID
        page: Page number
        page_size: Page size
        direction: Direction of communications ('sent', 'received', or 'both')
        status: Filter by status
        current_user: Current authenticated user (optional)
        communication_service: Communication service
        
    Returns:
        Dict[str, Any]: Communications and pagination info
        
    Raises:
        AgentNotFoundError: If agent not found
    """
    try:
        # Validate direction
        if direction not in ["sent", "received", "both"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Direction must be 'sent', 'received', or 'both'",
            )
        
        # Get communications
        communications, total = await communication_service.get_communications_for_agent(
            agent_id=agent_id,
            page=page,
            page_size=page_size,
            direction=direction,
            status=status,
        )
        
        # Convert communications to dictionaries
        communications_data = []
        for comm in communications:
            comm_dict = {
                "id": str(comm.id),
                "from_agent_id": str(comm.from_agent_id),
                "to_agent_id": str(comm.to_agent_id),
                "type": comm.type,
                "content": comm.content,
                "status": comm.status,
                "created_at": comm.created_at.isoformat(),
                "delivered_at": comm.delivered_at.isoformat() if comm.delivered_at else None,
            }
            communications_data.append(comm_dict)
        
        # Return paginated list
        return {
            "items": communications_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )


@router.get(
    "/communications/{communication_id}",
    response_model=Dict[str, Any],
    summary="Get communication",
    description="Get a communication by ID.",
)
async def get_communication(
    communication_id: UUID = Path(..., description="Communication ID"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    communication_service: CommunicationService = Depends(get_communication_service),
) -> Dict[str, Any]:
    """
    Get a communication by ID.
    
    Args:
        communication_id: Communication ID
        current_user: Current authenticated user (optional)
        communication_service: Communication service
        
    Returns:
        Dict[str, Any]: Communication
        
    Raises:
        HTTPException: If communication not found
    """
    # Get communication
    communication = await communication_service.get_communication(communication_id)
    
    # Check if communication exists
    if not communication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Communication with ID {communication_id} not found",
        )
    
    # Convert to dictionary
    return {
        "id": str(communication.id),
        "from_agent_id": str(communication.from_agent_id),
        "to_agent_id": str(communication.to_agent_id),
        "type": communication.type,
        "content": communication.content,
        "status": communication.status,
        "created_at": communication.created_at.isoformat(),
        "delivered_at": communication.delivered_at.isoformat() if communication.delivered_at else None,
    }
