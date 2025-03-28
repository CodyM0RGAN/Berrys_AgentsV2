from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional
from uuid import UUID

from ..dependencies import get_template_service, get_current_user, get_admin_user, get_optional_user
from ..exceptions import (
    TemplateNotFoundError,
    TemplateValidationError,
)
from ..models.api import (
    AgentTemplateCreate,
    AgentTemplateUpdate,
    AgentTemplate,
    AgentTemplateList,
    UserInfo,
)
from ..services.template_service import TemplateService

router = APIRouter()


@router.post(
    "",
    response_model=AgentTemplate,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new template",
    description="Create a new agent template with the provided data.",
)
async def create_template(
    template: AgentTemplateCreate,
    current_user: UserInfo = Depends(get_admin_user),  # Only admins can create templates
    template_service: TemplateService = Depends(get_template_service),
) -> AgentTemplate:
    """
    Create a new agent template.
    
    Args:
        template: Template data
        current_user: Current authenticated admin user
        template_service: Template service
        
    Returns:
        AgentTemplate: Created template
        
    Raises:
        TemplateValidationError: If template data is invalid
    """
    try:
        return await template_service.create_template(template)
    except TemplateValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=AgentTemplateList,
    summary="List templates",
    description="Get a paginated list of agent templates with optional filtering.",
)
async def list_templates(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    search: Optional[str] = Query(None, description="Search term"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    template_service: TemplateService = Depends(get_template_service),
) -> AgentTemplateList:
    """
    List agent templates with pagination and filtering.
    
    Args:
        page: Page number
        page_size: Page size
        agent_type: Filter by agent type
        search: Search term
        current_user: Current authenticated user (optional)
        template_service: Template service
        
    Returns:
        AgentTemplateList: Paginated list of templates
    """
    # Get templates
    templates, total = await template_service.list_templates(
        page=page,
        page_size=page_size,
        agent_type=agent_type,
        search=search,
    )
    
    # Return paginated list
    return AgentTemplateList(
        items=templates,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{template_id}",
    response_model=AgentTemplate,
    summary="Get template",
    description="Get an agent template by ID.",
)
async def get_template(
    template_id: str = Path(..., description="Template ID"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    template_service: TemplateService = Depends(get_template_service),
) -> AgentTemplate:
    """
    Get an agent template by ID.
    
    Args:
        template_id: Template ID
        current_user: Current authenticated user (optional)
        template_service: Template service
        
    Returns:
        AgentTemplate: Template
        
    Raises:
        TemplateNotFoundError: If template not found
    """
    # Get template
    template = await template_service.get_template(template_id)
    
    # Check if template exists
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found",
        )
    
    return template


@router.put(
    "/{template_id}",
    response_model=AgentTemplate,
    summary="Update template",
    description="Update an agent template by ID.",
)
async def update_template(
    template_update: AgentTemplateUpdate,
    template_id: str = Path(..., description="Template ID"),
    current_user: UserInfo = Depends(get_admin_user),  # Only admins can update templates
    template_service: TemplateService = Depends(get_template_service),
) -> AgentTemplate:
    """
    Update an agent template by ID.
    
    Args:
        template_update: Template update data
        template_id: Template ID
        current_user: Current authenticated admin user
        template_service: Template service
        
    Returns:
        AgentTemplate: Updated template
        
    Raises:
        TemplateNotFoundError: If template not found
        TemplateValidationError: If template data is invalid
    """
    try:
        return await template_service.update_template(template_id, template_update)
    except TemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found",
        )
    except TemplateValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete template",
    description="Delete an agent template by ID.",
)
async def delete_template(
    template_id: str = Path(..., description="Template ID"),
    current_user: UserInfo = Depends(get_admin_user),  # Only admins can delete templates
    template_service: TemplateService = Depends(get_template_service),
) -> None:
    """
    Delete an agent template by ID.
    
    Args:
        template_id: Template ID
        current_user: Current authenticated admin user
        template_service: Template service
        
    Raises:
        TemplateNotFoundError: If template not found
    """
    try:
        await template_service.delete_template(template_id)
    except TemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found",
        )
