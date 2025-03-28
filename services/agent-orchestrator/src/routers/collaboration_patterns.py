"""
Collaboration pattern router.

This module contains the API endpoints for collaboration patterns.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional, Dict, Any
from uuid import UUID

from shared.models.src.enums import AgentType

from ..dependencies import get_current_user, get_admin_user, get_optional_user, get_collaboration_pattern_service
from ..exceptions import (
    PatternNotFoundError,
    DatabaseError,
)
from ..models.api import (
    UserInfo,
)
from ..models.collaboration_pattern import (
    CollaborationPattern,
    CollaborationPatternCreate,
    CollaborationPatternUpdate,
    CollaborationPatternResponse,
    CollaborationPatternListResponse,
    CollaborationGraph,
    CollaborationGraphResponse,
)

router = APIRouter()


@router.get(
    "",
    response_model=CollaborationPatternListResponse,
    summary="List collaboration patterns",
    description="Get a list of collaboration patterns with optional filtering.",
)
async def list_patterns(
    source_agent_type: Optional[str] = Query(None, description="Filter by source agent type"),
    target_agent_type: Optional[str] = Query(None, description="Filter by target agent type"),
    interaction_type: Optional[str] = Query(None, description="Filter by interaction type"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    collaboration_pattern_service = Depends(get_collaboration_pattern_service),
) -> CollaborationPatternListResponse:
    """
    List collaboration patterns with optional filtering.
    
    Args:
        source_agent_type: Filter by source agent type
        target_agent_type: Filter by target agent type
        interaction_type: Filter by interaction type
        current_user: Current authenticated user (optional)
        collaboration_pattern_service: Collaboration pattern service
        
    Returns:
        CollaborationPatternListResponse: List of collaboration patterns
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        # Convert string to enum if provided
        source_agent_type_enum = None
        if source_agent_type:
            try:
                source_agent_type_enum = AgentType(source_agent_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid source agent type: {source_agent_type}",
                )
        
        target_agent_type_enum = None
        if target_agent_type:
            try:
                target_agent_type_enum = AgentType(target_agent_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid target agent type: {target_agent_type}",
                )
        
        # Get patterns
        patterns = await collaboration_pattern_service.list_patterns(
            source_agent_type=source_agent_type_enum,
            target_agent_type=target_agent_type_enum,
            interaction_type=interaction_type,
        )
        
        return CollaborationPatternListResponse(
            success=True,
            message="Collaboration patterns retrieved successfully",
            data=patterns,
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{pattern_id}",
    response_model=CollaborationPatternResponse,
    summary="Get collaboration pattern",
    description="Get a collaboration pattern by ID.",
)
async def get_pattern(
    pattern_id: UUID = Path(..., description="Collaboration pattern ID"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    collaboration_pattern_service = Depends(get_collaboration_pattern_service),
) -> CollaborationPatternResponse:
    """
    Get a collaboration pattern by ID.
    
    Args:
        pattern_id: Collaboration pattern ID
        current_user: Current authenticated user (optional)
        collaboration_pattern_service: Collaboration pattern service
        
    Returns:
        CollaborationPatternResponse: Collaboration pattern
        
    Raises:
        PatternNotFoundError: If pattern not found
        DatabaseError: If database operation fails
    """
    try:
        # Get pattern
        pattern = await collaboration_pattern_service.get_pattern(pattern_id)
        
        # Check if pattern exists
        if not pattern:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collaboration pattern with ID {pattern_id} not found",
            )
        
        return CollaborationPatternResponse(
            success=True,
            message="Collaboration pattern retrieved successfully",
            data=pattern,
        )
    except PatternNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collaboration pattern with ID {pattern_id} not found",
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "",
    response_model=CollaborationPatternResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create collaboration pattern",
    description="Create a new collaboration pattern.",
)
async def create_pattern(
    pattern: CollaborationPatternCreate,
    current_user: UserInfo = Depends(get_admin_user),  # Only admins can create patterns
    collaboration_pattern_service = Depends(get_collaboration_pattern_service),
) -> CollaborationPatternResponse:
    """
    Create a new collaboration pattern.
    
    Args:
        pattern: Collaboration pattern to create
        current_user: Current authenticated admin user
        collaboration_pattern_service: Collaboration pattern service
        
    Returns:
        CollaborationPatternResponse: Created collaboration pattern
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        # Validate agent types
        try:
            source_agent_type = AgentType(pattern.source_agent_type)
            target_agent_type = AgentType(pattern.target_agent_type)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent type: {str(e)}",
            )
        
        # Create pattern
        created_pattern = await collaboration_pattern_service.create_pattern(pattern)
        
        return CollaborationPatternResponse(
            success=True,
            message="Collaboration pattern created successfully",
            data=created_pattern,
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.put(
    "/{pattern_id}",
    response_model=CollaborationPatternResponse,
    summary="Update collaboration pattern",
    description="Update a collaboration pattern by ID.",
)
async def update_pattern(
    pattern: CollaborationPatternUpdate,
    pattern_id: UUID = Path(..., description="Collaboration pattern ID"),
    current_user: UserInfo = Depends(get_admin_user),  # Only admins can update patterns
    collaboration_pattern_service = Depends(get_collaboration_pattern_service),
) -> CollaborationPatternResponse:
    """
    Update a collaboration pattern by ID.
    
    Args:
        pattern: Collaboration pattern update data
        pattern_id: Collaboration pattern ID
        current_user: Current authenticated admin user
        collaboration_pattern_service: Collaboration pattern service
        
    Returns:
        CollaborationPatternResponse: Updated collaboration pattern
        
    Raises:
        PatternNotFoundError: If pattern not found
        DatabaseError: If database operation fails
    """
    try:
        # Validate agent type if provided
        if pattern.target_agent_type:
            try:
                target_agent_type = AgentType(pattern.target_agent_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid target agent type: {pattern.target_agent_type}",
                )
        
        # Update pattern
        updated_pattern = await collaboration_pattern_service.update_pattern(pattern_id, pattern)
        
        return CollaborationPatternResponse(
            success=True,
            message="Collaboration pattern updated successfully",
            data=updated_pattern,
        )
    except PatternNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collaboration pattern with ID {pattern_id} not found",
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete(
    "/{pattern_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete collaboration pattern",
    description="Delete a collaboration pattern by ID.",
)
async def delete_pattern(
    pattern_id: UUID = Path(..., description="Collaboration pattern ID"),
    current_user: UserInfo = Depends(get_admin_user),  # Only admins can delete patterns
    collaboration_pattern_service = Depends(get_collaboration_pattern_service),
) -> None:
    """
    Delete a collaboration pattern by ID.
    
    Args:
        pattern_id: Collaboration pattern ID
        current_user: Current authenticated admin user
        collaboration_pattern_service: Collaboration pattern service
        
    Raises:
        PatternNotFoundError: If pattern not found
        DatabaseError: If database operation fails
    """
    try:
        # Delete pattern
        await collaboration_pattern_service.delete_pattern(pattern_id)
    except PatternNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collaboration pattern with ID {pattern_id} not found",
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/project/{project_id}/graph",
    response_model=CollaborationGraphResponse,
    summary="Get collaboration graph",
    description="Get the collaboration graph for a project.",
)
async def get_collaboration_graph(
    project_id: UUID = Path(..., description="Project ID"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    collaboration_pattern_service = Depends(get_collaboration_pattern_service),
) -> CollaborationGraphResponse:
    """
    Get the collaboration graph for a project.
    
    Args:
        project_id: Project ID
        current_user: Current authenticated user (optional)
        collaboration_pattern_service: Collaboration pattern service
        
    Returns:
        CollaborationGraphResponse: Collaboration graph
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        # Get collaboration graph
        graph = await collaboration_pattern_service.get_collaboration_graph(project_id)
        
        return CollaborationGraphResponse(
            success=True,
            message="Collaboration graph retrieved successfully",
            data=graph,
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/project/{project_id}/setup-communication",
    status_code=status.HTTP_200_OK,
    summary="Setup communication rules",
    description="Setup communication rules based on collaboration patterns for a project.",
)
async def setup_communication_rules(
    project_id: UUID = Path(..., description="Project ID"),
    current_user: UserInfo = Depends(get_current_user),
    collaboration_pattern_service = Depends(get_collaboration_pattern_service),
) -> Dict[str, Any]:
    """
    Setup communication rules based on collaboration patterns for a project.
    
    Args:
        project_id: Project ID
        current_user: Current authenticated user
        collaboration_pattern_service: Collaboration pattern service
        
    Returns:
        Dict[str, Any]: Result of the operation
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        # Setup communication rules
        result = await collaboration_pattern_service.setup_project_communication_rules(project_id)
        
        return {
            "success": True,
            "message": "Communication rules setup successfully",
            "data": result,
        }
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
