"""
Resource management router.

This module defines API endpoints for resource management.
"""

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Path

from ..services.resource_service import ResourceService
from ..models.api.resource import (
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse,
    ResourceListResponse
)
from ..models.api.resource_allocation import (
    ResourceAllocationCreate,
    ResourceAllocationUpdate,
    ResourceAllocationResponse,
    ResourceAllocationListResponse
)
from ..models.api.common import (
    PaginationParams,
    ResourceType
)
from ..dependencies import get_resource_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/resources",
    tags=["resources"],
)

# Resource endpoints

@router.post("", response_model=ResourceResponse)
async def create_resource(
    resource_data: ResourceCreate,
    resource_service: ResourceService = Depends(get_resource_service),
):
    """
    Create a new resource.
    
    Args:
        resource_data: Resource data
        resource_service: Resource service
        
    Returns:
        ResourceResponse: Created resource
    """
    logger.info(f"Creating resource: {resource_data.name}")
    return await resource_service.create_resource(resource_data)


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: UUID = Path(..., description="Resource ID"),
    resource_service: ResourceService = Depends(get_resource_service),
):
    """
    Get a resource by ID.
    
    Args:
        resource_id: Resource ID
        resource_service: Resource service
        
    Returns:
        ResourceResponse: Resource
    """
    logger.info(f"Getting resource: {resource_id}")
    return await resource_service.get_resource(resource_id)


@router.get("", response_model=ResourceListResponse)
async def list_resources(
    resource_type: Optional[ResourceType] = Query(None, description="Resource type filter"),
    pagination: PaginationParams = Depends(),
    resource_service: ResourceService = Depends(get_resource_service),
):
    """
    List resources with filtering and pagination.
    
    Args:
        resource_type: Optional resource type filter
        pagination: Pagination parameters
        resource_service: Resource service
        
    Returns:
        ResourceListResponse: List of resources
    """
    logger.info(f"Listing resources: type={resource_type}")
    return await resource_service.list_resources(resource_type, pagination)


@router.patch("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_data: ResourceUpdate,
    resource_id: UUID = Path(..., description="Resource ID"),
    resource_service: ResourceService = Depends(get_resource_service),
):
    """
    Update a resource.
    
    Args:
        resource_data: Resource data to update
        resource_id: Resource ID
        resource_service: Resource service
        
    Returns:
        ResourceResponse: Updated resource
    """
    logger.info(f"Updating resource: {resource_id}")
    return await resource_service.update_resource(resource_id, resource_data)


@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: UUID = Path(..., description="Resource ID"),
    resource_service: ResourceService = Depends(get_resource_service),
):
    """
    Delete a resource.
    
    Args:
        resource_id: Resource ID
        resource_service: Resource service
        
    Returns:
        dict: Response with status and message
    """
    logger.info(f"Deleting resource: {resource_id}")
    return await resource_service.delete_resource(resource_id)


# Resource allocation endpoints

@router.post("/{resource_id}/allocations", response_model=ResourceAllocationResponse)
async def create_allocation(
    allocation_data: ResourceAllocationCreate,
    resource_id: UUID = Path(..., description="Resource ID"),
    resource_service: ResourceService = Depends(get_resource_service),
):
    """
    Create a new resource allocation.
    
    Args:
        allocation_data: Allocation data
        resource_id: Resource ID
        resource_service: Resource service
        
    Returns:
        ResourceAllocationResponse: Created allocation
    """
    logger.info(f"Creating allocation for resource: {resource_id}")
    
    # Ensure resource ID in path matches resource ID in data
    if allocation_data.resource_id != resource_id:
        allocation_data.resource_id = resource_id
    
    return await resource_service.create_allocation(allocation_data)


@router.get("/{resource_id}/allocations", response_model=ResourceAllocationListResponse)
async def list_resource_allocations(
    resource_id: UUID = Path(..., description="Resource ID"),
    pagination: PaginationParams = Depends(),
    resource_service: ResourceService = Depends(get_resource_service),
):
    """
    List allocations for a resource.
    
    Args:
        resource_id: Resource ID
        pagination: Pagination parameters
        resource_service: Resource service
        
    Returns:
        ResourceAllocationListResponse: List of allocations
    """
    logger.info(f"Listing allocations for resource: {resource_id}")
    return await resource_service.list_allocations(resource_id=resource_id, pagination=pagination)


@router.get("/allocations/{allocation_id}", response_model=ResourceAllocationResponse)
async def get_allocation(
    allocation_id: UUID = Path(..., description="Allocation ID"),
    resource_service: ResourceService = Depends(get_resource_service),
):
    """
    Get a resource allocation by ID.
    
    Args:
        allocation_id: Allocation ID
        resource_service: Resource service
        
    Returns:
        ResourceAllocationResponse: Allocation
    """
    logger.info(f"Getting allocation: {allocation_id}")
    return await resource_service.get_allocation(allocation_id)


@router.patch("/allocations/{allocation_id}", response_model=ResourceAllocationResponse)
async def update_allocation(
    allocation_data: ResourceAllocationUpdate,
    allocation_id: UUID = Path(..., description="Allocation ID"),
    resource_service: ResourceService = Depends(get_resource_service),
):
    """
    Update a resource allocation.
    
    Args:
        allocation_data: Allocation data to update
        allocation_id: Allocation ID
        resource_service: Resource service
        
    Returns:
        ResourceAllocationResponse: Updated allocation
    """
    logger.info(f"Updating allocation: {allocation_id}")
    return await resource_service.update_allocation(allocation_id, allocation_data)


@router.delete("/allocations/{allocation_id}")
async def delete_allocation(
    allocation_id: UUID = Path(..., description="Allocation ID"),
    resource_service: ResourceService = Depends(get_resource_service),
):
    """
    Delete a resource allocation.
    
    Args:
        allocation_id: Allocation ID
        resource_service: Resource service
        
    Returns:
        dict: Response with status and message
    """
    logger.info(f"Deleting allocation: {allocation_id}")
    return await resource_service.delete_allocation(allocation_id)


@router.get("/{resource_id}/utilization")
async def get_resource_utilization(
    resource_id: UUID = Path(..., description="Resource ID"),
    resource_service: ResourceService = Depends(get_resource_service),
):
    """
    Get resource utilization.
    
    Args:
        resource_id: Resource ID
        resource_service: Resource service
        
    Returns:
        dict: Resource utilization data
    """
    logger.info(f"Getting utilization for resource: {resource_id}")
    return await resource_service.get_resource_utilization(resource_id=resource_id)


@router.get("/utilization")
async def get_all_resources_utilization(
    resource_type: Optional[ResourceType] = Query(None, description="Resource type filter"),
    resource_service: ResourceService = Depends(get_resource_service),
):
    """
    Get utilization for all resources.
    
    Args:
        resource_type: Optional resource type filter
        resource_service: Resource service
        
    Returns:
        dict: Resource utilization data
    """
    logger.info(f"Getting utilization for all resources: type={resource_type}")
    return await resource_service.get_resource_utilization(resource_type=resource_type)
