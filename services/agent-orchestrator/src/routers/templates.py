"""
Template Engine API endpoints.

This module provides the API endpoints for the Agent Template Engine.
"""

import logging
from typing import List, Dict, Optional, Any
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db_session, get_current_user, get_current_user_admin_only
from ..models.template_engine import (
    TemplateType,
    AgentTemplate as TemplateEngine,
    AgentTemplateCreate as TemplateEngineCreate,
    AgentTemplateUpdate as TemplateEngineUpdate,
    AgentTemplateVersion,
    TemplateTag,
    TemplateTagCreate,
    TemplateTagUpdate,
    TemplateCustomization,
    TemplateImportSource,
    VersionComparisonResult,
    AgentTemplateResponse as TemplateEngineResponse,
    AgentTemplateListResponse as TemplateEngineListResponse,
    AgentTemplateVersionResponse,
    AgentTemplateVersionListResponse,
    TemplateTagResponse,
    TemplateTagListResponse,
    VersionComparisonResultResponse,
)
from ..services.template_management_service import TemplateManagementService
from ..exceptions import NotFoundException, AlreadyExistsException, ValidationException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("/", response_model=TemplateEngineListResponse)
async def list_templates(
    agent_type: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated tag names
    search: Optional[str] = None,
    is_system: Optional[bool] = None,
    is_public: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List templates with filtering options.
    
    Args:
        agent_type: Filter by agent type
        category: Filter by category
        tags: Comma-separated list of tags to filter by
        search: Search term for name and description
        is_system: Filter by system template flag
        is_public: Filter by public flag
        skip: Number of records to skip
        limit: Maximum number of records to return
        session: Database session
        
    Returns:
        TemplateEngineListResponse: List of templates
    """
    # Parse tags if provided
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
    
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Get templates
        templates, total_count = await service.list_templates(
            session=session,
            agent_type=agent_type,
            category=category,
            tags=tag_list,
            search_term=search,
            is_system_template=is_system,
            is_public=is_public,
            skip=skip,
            limit=limit,
        )
        
        return {
            "status": "success",
            "data": templates,
            "meta": {
                "total": total_count,
                "skip": skip,
                "limit": limit,
            }
        }
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing templates: {str(e)}"
        )


@router.get("/{template_id}", response_model=TemplateEngineResponse)
async def get_template(
    template_id: UUID = Path(..., description="Template ID"),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get a template by ID.
    
    Args:
        template_id: Template ID
        session: Database session
        
    Returns:
        TemplateEngineResponse: Template
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Get template
        template = await service.get_template(
            session=session,
            template_id=template_id,
        )
        
        return {
            "status": "success",
            "data": template,
        }
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting template: {str(e)}"
        )


@router.post("/", response_model=TemplateEngineResponse)
async def create_template(
    template: TemplateEngineCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new template.
    
    Args:
        template: Template to create
        session: Database session
        current_user: Current user
        
    Returns:
        TemplateEngineResponse: Created template
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Set owner ID if not provided
        if not template.owner_id and current_user:
            template.owner_id = UUID(current_user.get("id")) if current_user.get("id") else None
        
        # Create template
        created_template = await service.create_template(
            session=session,
            template=template,
        )
        
        return {
            "status": "success",
            "data": created_template,
        }
    except AlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating template: {str(e)}"
        )


@router.put("/{template_id}", response_model=TemplateEngineResponse)
async def update_template(
    template_id: UUID = Path(..., description="Template ID"),
    template: TemplateEngineUpdate = None,
    session: AsyncSession = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a template.
    
    Args:
        template_id: Template ID
        template: Template data to update
        session: Database session
        current_user: Current user
        
    Returns:
        TemplateEngineResponse: Updated template
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Update template
        updated_template = await service.update_template(
            session=session,
            template_id=template_id,
            template=template,
        )
        
        return {
            "status": "success",
            "data": updated_template,
        }
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating template: {str(e)}"
        )


@router.delete("/{template_id}", response_model=Dict[str, str])
async def delete_template(
    template_id: UUID = Path(..., description="Template ID"),
    session: AsyncSession = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user_admin_only)
):
    """
    Delete a template.
    
    Args:
        template_id: Template ID
        session: Database session
        current_user: Current user (admin only)
        
    Returns:
        Dict[str, str]: Success message
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Delete template
        await service.delete_template(
            session=session,
            template_id=template_id,
        )
        
        return {
            "status": "success",
            "message": f"Template {template_id} deleted successfully",
        }
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting template: {str(e)}"
        )


@router.get("/{template_id}/versions", response_model=AgentTemplateVersionListResponse)
async def list_template_versions(
    template_id: UUID = Path(..., description="Template ID"),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List all versions of a template.
    
    Args:
        template_id: Template ID
        session: Database session
        
    Returns:
        AgentTemplateVersionListResponse: List of template versions
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Get template versions
        versions = await service.get_template_versions(
            session=session,
            template_id=template_id,
        )
        
        return {
            "status": "success",
            "data": versions,
        }
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error listing template versions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing template versions: {str(e)}"
        )


@router.get("/{template_id}/versions/{version_number}", response_model=AgentTemplateVersionResponse)
async def get_template_version(
    template_id: UUID = Path(..., description="Template ID"),
    version_number: int = Path(..., description="Version number"),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get a specific version of a template.
    
    Args:
        template_id: Template ID
        version_number: Version number
        session: Database session
        
    Returns:
        AgentTemplateVersionResponse: Template version
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Get template version
        version = await service.get_template_version(
            session=session,
            template_id=template_id,
            version_number=version_number,
        )
        
        return {
            "status": "success",
            "data": version,
        }
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting template version: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting template version: {str(e)}"
        )


@router.post("/{template_id}/versions", response_model=AgentTemplateVersionResponse)
async def create_template_version(
    template_id: UUID = Path(..., description="Template ID"),
    changelog: str = Query(..., description="Changelog message"),
    session: AsyncSession = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Manually create a new version of a template.
    
    Args:
        template_id: Template ID
        changelog: Changelog message
        session: Database session
        current_user: Current user
        
    Returns:
        AgentTemplateVersionResponse: Created version
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Get creator ID
        creator_id = UUID(current_user.get("id")) if current_user and current_user.get("id") else None
        
        # Create version
        version = await service.create_version(
            session=session,
            template_id=template_id,
            changelog=changelog,
            creator_id=creator_id,
        )
        
        return {
            "status": "success",
            "data": version,
        }
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating template version: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating template version: {str(e)}"
        )


@router.post("/{template_id}/revert/{version_number}", response_model=TemplateEngineResponse)
async def revert_to_version(
    template_id: UUID = Path(..., description="Template ID"),
    version_number: int = Path(..., description="Version number"),
    session: AsyncSession = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Revert a template to a previous version.
    
    Args:
        template_id: Template ID
        version_number: Version number
        session: Database session
        current_user: Current user
        
    Returns:
        TemplateEngineResponse: Updated template
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Revert to version
        template = await service.revert_to_version(
            session=session,
            template_id=template_id,
            version_number=version_number,
        )
        
        return {
            "status": "success",
            "data": template,
        }
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error reverting to version: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reverting to version: {str(e)}"
        )


@router.get("/{template_id}/compare", response_model=VersionComparisonResultResponse)
async def compare_versions(
    template_id: UUID = Path(..., description="Template ID"),
    version1: int = Query(..., description="First version number"),
    version2: int = Query(..., description="Second version number"),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Compare two versions of a template.
    
    Args:
        template_id: Template ID
        version1: First version number
        version2: Second version number
        session: Database session
        
    Returns:
        VersionComparisonResultResponse: Comparison result
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Compare versions
        result = await service.compare_versions(
            session=session,
            template_id=template_id,
            version1=version1,
            version2=version2,
        )
        
        return {
            "status": "success",
            "data": result,
        }
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error comparing versions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error comparing versions: {str(e)}"
        )


@router.get("/tags", response_model=TemplateTagListResponse)
async def list_tags(
    session: AsyncSession = Depends(get_db_session)
):
    """
    List all template tags.
    
    Args:
        session: Database session
        
    Returns:
        TemplateTagListResponse: List of tags
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Get tags
        tags = await service.list_tags(
            session=session,
        )
        
        return {
            "status": "success",
            "data": tags,
        }
    except Exception as e:
        logger.error(f"Error listing tags: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing tags: {str(e)}"
        )


@router.post("/tags", response_model=TemplateTagResponse)
async def create_tag(
    tag: TemplateTagCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new tag.
    
    Args:
        tag: Tag to create
        session: Database session
        current_user: Current user
        
    Returns:
        TemplateTagResponse: Created tag
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Create tag
        created_tag = await service.create_tag(
            session=session,
            tag=tag,
        )
        
        return {
            "status": "success",
            "data": created_tag,
        }
    except AlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating tag: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating tag: {str(e)}"
        )


@router.put("/tags/{tag_id}", response_model=TemplateTagResponse)
async def update_tag(
    tag_id: UUID = Path(..., description="Tag ID"),
    tag: TemplateTagUpdate = None,
    session: AsyncSession = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a tag.
    
    Args:
        tag_id: Tag ID
        tag: Tag data to update
        session: Database session
        current_user: Current user
        
    Returns:
        TemplateTagResponse: Updated tag
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Update tag
        updated_tag = await service.update_tag(
            session=session,
            tag_id=tag_id,
            tag=tag,
        )
        
        return {
            "status": "success",
            "data": updated_tag,
        }
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating tag: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating tag: {str(e)}"
        )


@router.delete("/tags/{tag_id}", response_model=Dict[str, str])
async def delete_tag(
    tag_id: UUID = Path(..., description="Tag ID"),
    session: AsyncSession = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user_admin_only)
):
    """
    Delete a tag.
    
    Args:
        tag_id: Tag ID
        session: Database session
        current_user: Current user (admin only)
        
    Returns:
        Dict[str, str]: Success message
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Delete tag
        await service.delete_tag(
            session=session,
            tag_id=tag_id,
        )
        
        return {
            "status": "success",
            "message": f"Tag {tag_id} deleted successfully",
        }
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting tag: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting tag: {str(e)}"
        )


@router.post("/{template_id}/tags/{tag_id}", response_model=Dict[str, str])
async def add_tag_to_template(
    template_id: UUID = Path(..., description="Template ID"),
    tag_id: UUID = Path(..., description="Tag ID"),
    session: AsyncSession = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Add a tag to a template.
    
    Args:
        template_id: Template ID
        tag_id: Tag ID
        session: Database session
        current_user: Current user
        
    Returns:
        Dict[str, str]: Success message
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Add tag to template
        await service.add_tag_to_template(
            session=session,
            template_id=template_id,
            tag_id=tag_id,
        )
        
        return {
            "status": "success",
            "message": f"Tag {tag_id} added to template {template_id} successfully",
        }
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding tag to template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding tag to template: {str(e)}"
        )


@router.delete("/{template_id}/tags/{tag_id}", response_model=Dict[str, str])
async def remove_tag_from_template(
    template_id: UUID = Path(..., description="Template ID"),
    tag_id: UUID = Path(..., description="Tag ID"),
    session: AsyncSession = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Remove a tag from a template.
    
    Args:
        template_id: Template ID
        tag_id: Tag ID
        session: Database session
        current_user: Current user
        
    Returns:
        Dict[str, str]: Success message
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Remove tag from template
        await service.remove_tag_from_template(
            session=session,
            template_id=template_id,
            tag_id=tag_id,
        )
        
        return {
            "status": "success",
            "message": f"Tag {tag_id} removed from template {template_id} successfully",
        }
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error removing tag from template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing tag from template: {str(e)}"
        )


@router.get("/{template_id}/tags", response_model=TemplateTagListResponse)
async def get_template_tags(
    template_id: UUID = Path(..., description="Template ID"),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get all tags for a template.
    
    Args:
        template_id: Template ID
        session: Database session
        
    Returns:
        TemplateTagListResponse: List of tags
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Get template tags
        tags = await service.get_template_tags(
            session=session,
            template_id=template_id,
        )
        
        return {
            "status": "success",
            "data": tags,
        }
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting template tags: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting template tags: {str(e)}"
        )


@router.post("/import", response_model=Dict[str, Any])
async def import_templates(
    import_source: TemplateImportSource,
    session: AsyncSession = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user_admin_only)
):
    """
    Import templates from files.
    
    Args:
        import_source: Import source
        session: Database session
        current_user: Current user (admin only)
        
    Returns:
        Dict[str, Any]: Import results
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Import templates
        imported_count, failed_count = await service.import_templates_from_files(
            session=session,
            directory_path=import_source.source_path,
        )
        
        return {
            "status": "success",
            "data": {
                "imported_count": imported_count,
                "failed_count": failed_count,
            },
            "message": f"Imported {imported_count} templates, {failed_count} failed",
        }
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error importing templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing templates: {str(e)}"
        )


@router.post("/{template_id}/customize", response_model=Dict[str, Any])
async def customize_template(
    template_id: UUID = Path(..., description="Template ID"),
    customization: TemplateCustomization = None,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Apply customization to a template.
    
    Args:
        template_id: Template ID
        customization: Customization values
        session: Database session
        
    Returns:
        Dict[str, Any]: Customized template content
    """
    # Create service
    service = TemplateManagementService(None)
    
    try:
        # Customize template
        customized_content = await service.customize_template(
            session=session,
            template_id=template_id,
            customization=customization,
        )
        
        return {
            "status": "success",
            "data": customized_content,
        }
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error customizing template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error customizing template: {str(e)}"
        )
