from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional
from uuid import UUID

from ..dependencies import get_resource_service, get_current_user, get_optional_user
from ..exceptions import ResourceNotFoundError, ValidationError
from ..models.api import (
    Resource,
    ResourceCreate,
    ResourceUpdate,
    ResourceList,
    UserInfo,
)
from ..services.resource_service import ResourceService

router = APIRouter()


@router.post(
    "",
    response_model=Resource,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new resource",
    description="Create a new resource with the provided data.",
)
async def create_resource(
    resource: ResourceCreate,
    current_user: UserInfo = Depends(get_current_user),
    resource_service: ResourceService = Depends(get_resource_service),
) -> Resource:
    """
    Create a new resource.
    
    Args:
        resource: Resource data
        current_user: Current authenticated user
        resource_service: Resource service
        
    Returns:
        Resource: Created resource
        
    Raises:
        ValidationError: If resource data is invalid
    """
    # Set owner ID to current user if not provided
    if not resource.owner_id:
        resource.owner_id = current_user.id
        
    # Create resource
    return await resource_service.create_resource(resource)


@router.get(
    "",
    response_model=ResourceList,
    summary="List resources",
    description="Get a paginated list of resources with optional filtering.",
)
async def list_resources(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(None, description="Filter by status"),
    type: Optional[str] = Query(None, description="Filter by type"),
    search: Optional[str] = Query(None, description="Search term"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    resource_service: ResourceService = Depends(get_resource_service),
) -> ResourceList:
    """
    List resources with pagination and filtering.
    
    Args:
        page: Page number
        page_size: Page size
        status: Filter by status
        type: Filter by type
        search: Search term
        current_user: Current authenticated user (optional)
        resource_service: Resource service
        
    Returns:
        ResourceList: Paginated list of resources
    """
    # Get resources
    resources, total = await resource_service.list_resources(
        page=page,
        page_size=page_size,
        status=status,
        type=type,
        search=search,
        user_id=current_user.id if current_user else None,
    )
    
    # Return paginated list
    return ResourceList(
        items=resources,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{resource_id}",
    response_model=Resource,
    summary="Get resource",
    description="Get a resource by ID.",
)
async def get_resource(
    resource_id: UUID = Path(..., description="Resource ID"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    resource_service: ResourceService = Depends(get_resource_service),
) -> Resource:
    """
    Get a resource by ID.
    
    Args:
        resource_id: Resource ID
        current_user: Current authenticated user (optional)
        resource_service: Resource service
        
    Returns:
        Resource: Resource
        
    Raises:
        ResourceNotFoundError: If resource not found
    """
    # Get resource
    resource = await resource_service.get_resource(resource_id)
    
    # Check if resource exists
    if not resource:
        raise ResourceNotFoundError("Resource", str(resource_id))
    
    return resource


@router.put(
    "/{resource_id}",
    response_model=Resource,
    summary="Update resource",
    description="Update a resource by ID.",
)
async def update_resource(
    resource_update: ResourceUpdate,
    resource_id: UUID = Path(..., description="Resource ID"),
    current_user: UserInfo = Depends(get_current_user),
    resource_service: ResourceService = Depends(get_resource_service),
) -> Resource:
    """
    Update a resource by ID.
    
    Args:
        resource_update: Resource update data
        resource_id: Resource ID
        current_user: Current authenticated user
        resource_service: Resource service
        
    Returns:
        Resource: Updated resource
        
    Raises:
        ResourceNotFoundError: If resource not found
        ValidationError: If resource data is invalid
    """
    # Get resource
    resource = await resource_service.get_resource(resource_id)
    
    # Check if resource exists
    if not resource:
        raise ResourceNotFoundError("Resource", str(resource_id))
    
    # Check if user is owner or admin
    if resource.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this resource",
        )
    
    # Update resource
    updated_resource = await resource_service.update_resource(resource_id, resource_update)
    
    return updated_resource


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete resource",
    description="Delete a resource by ID.",
)
async def delete_resource(
    resource_id: UUID = Path(..., description="Resource ID"),
    current_user: UserInfo = Depends(get_current_user),
    resource_service: ResourceService = Depends(get_resource_service),
) -> None:
    """
    Delete a resource by ID.
    
    Args:
        resource_id: Resource ID
        current_user: Current authenticated user
        resource_service: Resource service
        
    Raises:
        ResourceNotFoundError: If resource not found
    """
    # Get resource
    resource = await resource_service.get_resource(resource_id)
    
    # Check if resource exists
    if not resource:
        raise ResourceNotFoundError("Resource", str(resource_id))
    
    # Check if user is owner or admin
    if resource.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this resource",
        )
    
    # Delete resource
    await resource_service.delete_resource(resource_id)
