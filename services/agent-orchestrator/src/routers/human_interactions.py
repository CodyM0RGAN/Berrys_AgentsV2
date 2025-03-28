from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..dependencies import get_human_interaction_service, get_current_user, get_optional_user
from ..exceptions import (
    AgentNotFoundError,
    ExecutionNotFoundError,
    HumanInteractionError,
    DatabaseError,
)
from ..models.api import (
    HumanInteractionRequest,
    HumanInteractionResponse,
    HumanApprovalRequest,
    HumanApprovalResponse,
    HumanFeedbackRequest,
    HumanFeedbackResponse,
    UserInfo,
)
from ..services.human_interaction_service import HumanInteractionService

router = APIRouter()


@router.post(
    "/{agent_id}/request-approval",
    response_model=HumanApprovalResponse,
    summary="Request approval",
    description="Request human approval for an agent action.",
)
async def request_approval(
    approval_request: HumanApprovalRequest,
    agent_id: UUID = Path(..., description="Agent ID"),
    current_user: UserInfo = Depends(get_current_user),
    human_interaction_service: HumanInteractionService = Depends(get_human_interaction_service),
) -> HumanApprovalResponse:
    """
    Request human approval for an agent action.
    
    Args:
        approval_request: Approval request details
        agent_id: Agent ID
        current_user: Current authenticated user
        human_interaction_service: Human interaction service
        
    Returns:
        HumanApprovalResponse: Response with interaction ID
        
    Raises:
        HTTPException: If agent not found or request fails
    """
    try:
        return await human_interaction_service.request_approval(agent_id, approval_request)
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except HumanInteractionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/interactions/{interaction_id}/approve",
    response_model=Dict[str, Any],
    summary="Provide approval",
    description="Provide a response to an approval request.",
)
async def provide_approval(
    interaction_id: UUID = Path(..., description="Interaction ID"),
    response: str = Query(..., description="Response (e.g., 'approved', 'rejected', or a specific option)"),
    feedback: Optional[str] = Query(None, description="Optional feedback text"),
    current_user: UserInfo = Depends(get_current_user),
    human_interaction_service: HumanInteractionService = Depends(get_human_interaction_service),
) -> Dict[str, Any]:
    """
    Provide a response to an approval request.
    
    Args:
        interaction_id: Interaction ID
        response: Response (e.g., "approved", "rejected", or a specific option)
        feedback: Optional feedback text
        current_user: Current authenticated user
        human_interaction_service: Human interaction service
        
    Returns:
        Dict[str, Any]: Updated interaction
        
    Raises:
        HTTPException: If interaction not found or not an approval request
    """
    try:
        interaction = await human_interaction_service.provide_approval(
            interaction_id=interaction_id,
            response=response,
            feedback=feedback,
            user_id=UUID(current_user.id) if current_user.id else None,
        )
        return interaction.to_dict()
    except HumanInteractionError as e:
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
    "/{agent_id}/submit-feedback",
    response_model=HumanFeedbackResponse,
    summary="Submit feedback",
    description="Submit human feedback for an agent.",
)
async def submit_feedback(
    feedback_request: HumanFeedbackRequest,
    agent_id: UUID = Path(..., description="Agent ID"),
    current_user: UserInfo = Depends(get_current_user),
    human_interaction_service: HumanInteractionService = Depends(get_human_interaction_service),
) -> HumanFeedbackResponse:
    """
    Submit human feedback for an agent.
    
    Args:
        feedback_request: Feedback request details
        agent_id: Agent ID
        current_user: Current authenticated user
        human_interaction_service: Human interaction service
        
    Returns:
        HumanFeedbackResponse: Response with interaction ID
        
    Raises:
        HTTPException: If agent not found or request fails
    """
    try:
        return await human_interaction_service.submit_feedback(agent_id, feedback_request)
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except HumanInteractionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{agent_id}/notify",
    response_model=Dict[str, Any],
    summary="Send notification",
    description="Send a notification to humans about agent activity.",
)
async def send_notification(
    notification: Dict[str, Any],
    agent_id: UUID = Path(..., description="Agent ID"),
    execution_id: Optional[UUID] = Query(None, description="Related execution ID"),
    priority: str = Query("normal", description="Priority level ('low', 'normal', 'high', 'critical')"),
    current_user: UserInfo = Depends(get_current_user),
    human_interaction_service: HumanInteractionService = Depends(get_human_interaction_service),
) -> Dict[str, Any]:
    """
    Send a notification to humans about agent activity.
    
    Args:
        notification: Notification content
        agent_id: Agent ID
        execution_id: Optional related execution ID
        priority: Priority level
        current_user: Current authenticated user
        human_interaction_service: Human interaction service
        
    Returns:
        Dict[str, Any]: Created interaction
        
    Raises:
        HTTPException: If agent not found or notification fails
    """
    try:
        interaction = await human_interaction_service.send_notification(
            agent_id=agent_id,
            notification=notification,
            execution_id=execution_id,
            priority=priority,
        )
        return interaction.to_dict()
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ExecutionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except HumanInteractionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{agent_id}/interactions",
    response_model=Dict[str, Any],
    summary="Get interactions",
    description="Get human interactions for an agent.",
)
async def get_interactions(
    agent_id: UUID = Path(..., description="Agent ID"),
    interaction_type: Optional[str] = Query(None, description="Filter by interaction type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    human_interaction_service: HumanInteractionService = Depends(get_human_interaction_service),
) -> Dict[str, Any]:
    """
    Get human interactions for an agent.
    
    Args:
        agent_id: Agent ID
        interaction_type: Filter by interaction type
        status: Filter by status
        page: Page number
        page_size: Page size
        current_user: Current authenticated user (optional)
        human_interaction_service: Human interaction service
        
    Returns:
        Dict[str, Any]: Interactions and pagination info
        
    Raises:
        HTTPException: If agent not found
    """
    try:
        interactions, total = await human_interaction_service.get_interactions_for_agent(
            agent_id=agent_id,
            interaction_type=interaction_type,
            status=status,
            page=page,
            page_size=page_size,
        )
        
        # Convert interactions to dictionaries
        interactions_data = [interaction.to_dict() for interaction in interactions]
        
        # Return paginated list
        return {
            "items": interactions_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/interactions/{interaction_id}",
    response_model=Dict[str, Any],
    summary="Get interaction",
    description="Get a human interaction by ID.",
)
async def get_interaction(
    interaction_id: UUID = Path(..., description="Interaction ID"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    human_interaction_service: HumanInteractionService = Depends(get_human_interaction_service),
) -> Dict[str, Any]:
    """
    Get a human interaction by ID.
    
    Args:
        interaction_id: Interaction ID
        current_user: Current authenticated user (optional)
        human_interaction_service: Human interaction service
        
    Returns:
        Dict[str, Any]: Interaction
        
    Raises:
        HTTPException: If interaction not found
    """
    interaction = await human_interaction_service.get_interaction(interaction_id)
    
    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interaction with ID {interaction_id} not found",
        )
    
    return interaction.to_dict()


@router.get(
    "/pending-approvals",
    response_model=Dict[str, Any],
    summary="Get pending approvals",
    description="Get pending approval requests.",
)
async def get_pending_approvals(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: UserInfo = Depends(get_current_user),
    human_interaction_service: HumanInteractionService = Depends(get_human_interaction_service),
) -> Dict[str, Any]:
    """
    Get pending approval requests.
    
    Args:
        project_id: Optional filter by project ID
        page: Page number
        page_size: Page size
        current_user: Current authenticated user
        human_interaction_service: Human interaction service
        
    Returns:
        Dict[str, Any]: Pending approvals and pagination info
    """
    try:
        approvals, total = await human_interaction_service.get_pending_approvals(
            project_id=project_id,
            page=page,
            page_size=page_size,
        )
        
        # Convert approvals to dictionaries
        approvals_data = [approval.to_dict() for approval in approvals]
        
        # Return paginated list
        return {
            "items": approvals_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
