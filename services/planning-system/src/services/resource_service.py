"""
Resource Service implementation.

This module implements the resource management component, which handles
resource creation, allocation, and management.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Union, cast
from uuid import UUID
from datetime import datetime

from .repository import PlanningRepository
from .base_service import BaseService
from ..models.api.resource import (
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse,
    ResourceListResponse,
    ResourceResponseData
)
from ..models.api.resource_allocation import (
    ResourceAllocationCreate,
    ResourceAllocationUpdate,
    ResourceAllocationResponse,
    ResourceAllocationListResponse,
    ResourceAllocationResponseData
)
from ..models.api.common import (
    PaginationParams,
    ResourceType
)
from ..exceptions import (
    ResourceNotFoundError,
    TaskNotFoundError,
    ResourceAllocationError
)

logger = logging.getLogger(__name__)

class ResourceService(BaseService):
    """
    Resource management service.
    
    This component handles resource creation, allocation, and management,
    providing methods for managing resources and resource allocations.
    """
    
    def __init__(self, repository: PlanningRepository):
        """
        Initialize the resource service.
        
        Args:
            repository: Planning repository
        """
        super().__init__(repository)
        logger.info("Resource Service initialized")
    
    # Resource operations
    
    async def create_resource(self, resource_data: ResourceCreate) -> ResourceResponse:
        """
        Create a new resource.
        
        Args:
            resource_data: Resource data
            
        Returns:
            ResourceResponse: Created resource
        """
        logger.info(f"Creating resource: {resource_data.name}")
        
        # Convert to dictionary for repository
        resource_dict = resource_data.model_dump()
        
        # Create resource
        resource = await self.repository.create_resource(resource_dict)
        
        # Prepare response
        response_data = ResourceResponseData(
            id=resource.id,
            name=resource.name,
            resource_type=resource.resource_type,
            description=resource.description,
            skills=resource.skills,
            availability=resource.availability,
            capacity_hours=resource.capacity_hours,
            cost_rate=resource.cost_rate,
            constraints=resource.constraints,
            external_id=resource.external_id,
            created_at=resource.created_at,
            updated_at=resource.updated_at,
            allocation_count=0,  # New resource has no allocations
            utilization_percentage=0.0,  # New resource has no utilization
            is_overallocated=False  # New resource is not overallocated
        )
        
        return ResourceResponse(
            status="success",
            message="Resource created successfully",
            data=response_data
        )
    
    async def get_resource(self, resource_id: UUID) -> ResourceResponse:
        """
        Get a resource by ID.
        
        Args:
            resource_id: Resource ID
            
        Returns:
            ResourceResponse: Resource
            
        Raises:
            ResourceNotFoundError: If resource not found
        """
        logger.info(f"Getting resource: {resource_id}")
        
        # Get resource
        resource = await self.repository.get_resource_by_id(resource_id)
        if not resource:
            raise ResourceNotFoundError(str(resource_id))
        
        # Get allocations for utilization calculation
        allocations = await self.repository.get_resource_allocations_by_resource(resource_id)
        
        # Calculate utilization
        total_allocated_hours = sum(allocation.assigned_hours for allocation in allocations)
        utilization_percentage = (total_allocated_hours / resource.capacity_hours) * 100 if resource.capacity_hours > 0 else 0
        is_overallocated = utilization_percentage > 100
        
        # Prepare response
        response_data = ResourceResponseData(
            id=resource.id,
            name=resource.name,
            resource_type=resource.resource_type,
            description=resource.description,
            skills=resource.skills,
            availability=resource.availability,
            capacity_hours=resource.capacity_hours,
            cost_rate=resource.cost_rate,
            constraints=resource.constraints,
            external_id=resource.external_id,
            created_at=resource.created_at,
            updated_at=resource.updated_at,
            allocation_count=len(allocations),
            utilization_percentage=utilization_percentage,
            is_overallocated=is_overallocated
        )
        
        return ResourceResponse(
            status="success",
            message="Resource retrieved successfully",
            data=response_data
        )
    
    async def list_resources(
        self,
        resource_type: Optional[ResourceType] = None,
        pagination: Optional[PaginationParams] = None
    ) -> ResourceListResponse:
        """
        List resources with filtering and pagination.
        
        Args:
            resource_type: Optional resource type filter
            pagination: Pagination parameters
            
        Returns:
            ResourceListResponse: List of resources
        """
        logger.info(f"Listing resources: type={resource_type}")
        
        # Prepare filters
        filters = {}
        if resource_type:
            filters["resource_type"] = resource_type
        
        # Prepare pagination
        pagination_dict = pagination.model_dump() if pagination else {"page": 1, "page_size": 20}
        
        # Get resources
        resources, total = await self.repository.list_resources(filters, pagination_dict)
        
        # Prepare response data
        response_data = []
        for resource in resources:
            # Get allocations for utilization calculation
            allocations = await self.repository.get_resource_allocations_by_resource(resource.id)
            
            # Calculate utilization
            total_allocated_hours = sum(allocation.assigned_hours for allocation in allocations)
            utilization_percentage = (total_allocated_hours / resource.capacity_hours) * 100 if resource.capacity_hours > 0 else 0
            is_overallocated = utilization_percentage > 100
            
            # Create response data
            resource_data = ResourceResponseData(
                id=resource.id,
                name=resource.name,
                resource_type=resource.resource_type,
                description=resource.description,
                skills=resource.skills,
                availability=resource.availability,
                capacity_hours=resource.capacity_hours,
                cost_rate=resource.cost_rate,
                constraints=resource.constraints,
                external_id=resource.external_id,
                created_at=resource.created_at,
                updated_at=resource.updated_at,
                allocation_count=len(allocations),
                utilization_percentage=utilization_percentage,
                is_overallocated=is_overallocated
            )
            response_data.append(resource_data)
        
        return ResourceListResponse(
            status="success",
            message=f"Retrieved {len(response_data)} resources",
            data=response_data,
            pagination={
                "page": pagination_dict["page"],
                "page_size": pagination_dict["page_size"],
                "total": total,
                "pages": (total + pagination_dict["page_size"] - 1) // pagination_dict["page_size"]
            }
        )
    
    async def update_resource(
        self,
        resource_id: UUID,
        resource_data: ResourceUpdate
    ) -> ResourceResponse:
        """
        Update a resource.
        
        Args:
            resource_id: Resource ID
            resource_data: Resource data to update
            
        Returns:
            ResourceResponse: Updated resource
            
        Raises:
            ResourceNotFoundError: If resource not found
        """
        logger.info(f"Updating resource: {resource_id}")
        
        # Convert to dictionary for repository
        resource_dict = resource_data.model_dump(exclude_unset=True)
        
        # Update resource
        resource = await self.repository.update_resource(resource_id, resource_dict)
        if not resource:
            raise ResourceNotFoundError(str(resource_id))
        
        # Get allocations for utilization calculation
        allocations = await self.repository.get_resource_allocations_by_resource(resource_id)
        
        # Calculate utilization
        total_allocated_hours = sum(allocation.assigned_hours for allocation in allocations)
        utilization_percentage = (total_allocated_hours / resource.capacity_hours) * 100 if resource.capacity_hours > 0 else 0
        is_overallocated = utilization_percentage > 100
        
        # Prepare response
        response_data = ResourceResponseData(
            id=resource.id,
            name=resource.name,
            resource_type=resource.resource_type,
            description=resource.description,
            skills=resource.skills,
            availability=resource.availability,
            capacity_hours=resource.capacity_hours,
            cost_rate=resource.cost_rate,
            constraints=resource.constraints,
            external_id=resource.external_id,
            created_at=resource.created_at,
            updated_at=resource.updated_at,
            allocation_count=len(allocations),
            utilization_percentage=utilization_percentage,
            is_overallocated=is_overallocated
        )
        
        return ResourceResponse(
            status="success",
            message="Resource updated successfully",
            data=response_data
        )
    
    async def delete_resource(self, resource_id: UUID) -> Dict[str, Any]:
        """
        Delete a resource.
        
        Args:
            resource_id: Resource ID
            
        Returns:
            Dict[str, Any]: Response with status and message
            
        Raises:
            ResourceNotFoundError: If resource not found
        """
        logger.info(f"Deleting resource: {resource_id}")
        
        # Delete resource
        deleted = await self.repository.delete_resource(resource_id)
        if not deleted:
            raise ResourceNotFoundError(str(resource_id))
        
        return {
            "status": "success",
            "message": "Resource deleted successfully"
        }
    
    # Resource allocation operations
    
    async def create_allocation(
        self,
        allocation_data: ResourceAllocationCreate
    ) -> ResourceAllocationResponse:
        """
        Create a new resource allocation.
        
        Args:
            allocation_data: Allocation data
            
        Returns:
            ResourceAllocationResponse: Created allocation
            
        Raises:
            ResourceNotFoundError: If resource not found
            TaskNotFoundError: If task not found
            ResourceAllocationError: If allocation fails
        """
        logger.info(f"Creating allocation: resource={allocation_data.resource_id}, task={allocation_data.task_id}")
        
        # Verify resource exists
        resource = await self.repository.get_resource_by_id(allocation_data.resource_id)
        if not resource:
            raise ResourceNotFoundError(str(allocation_data.resource_id))
        
        # Verify task exists
        task = await self.repository.get_task_by_id(allocation_data.task_id)
        if not task:
            raise TaskNotFoundError(str(allocation_data.task_id))
        
        # Check for overallocation
        allocations = await self.repository.get_resource_allocations_by_resource(allocation_data.resource_id)
        total_allocated_hours = sum(allocation.assigned_hours for allocation in allocations)
        new_total_hours = total_allocated_hours + allocation_data.assigned_hours
        is_overallocated = new_total_hours > resource.capacity_hours
        
        # Convert to dictionary for repository
        allocation_dict = allocation_data.model_dump()
        allocation_dict["is_overallocated"] = is_overallocated
        
        # Create allocation
        allocation = await self.repository.create_resource_allocation(allocation_dict)
        
        # Prepare response
        response_data = ResourceAllocationResponseData(
            id=allocation.id,
            task_id=allocation.task_id,
            resource_id=allocation.resource_id,
            task_name=task.name,
            resource_name=resource.name,
            allocation_percentage=allocation.allocation_percentage,
            assigned_hours=allocation.assigned_hours,
            start_date=allocation.start_date,
            end_date=allocation.end_date,
            is_overallocated=allocation.is_overallocated,
            created_at=allocation.created_at,
            updated_at=allocation.updated_at
        )
        
        return ResourceAllocationResponse(
            status="success",
            message="Resource allocation created successfully",
            data=response_data
        )
    
    async def get_allocation(self, allocation_id: UUID) -> ResourceAllocationResponse:
        """
        Get a resource allocation by ID.
        
        Args:
            allocation_id: Allocation ID
            
        Returns:
            ResourceAllocationResponse: Allocation
            
        Raises:
            ResourceAllocationError: If allocation not found
        """
        logger.info(f"Getting allocation: {allocation_id}")
        
        # Get allocation
        allocation = await self.repository.get_resource_allocation_by_id(allocation_id)
        if not allocation:
            raise ResourceAllocationError(
                message=f"Resource allocation not found: {allocation_id}",
                details={"allocation_id": str(allocation_id)}
            )
        
        # Get task and resource for names
        task = await self.repository.get_task_by_id(allocation.task_id)
        resource = await self.repository.get_resource_by_id(allocation.resource_id)
        
        # Prepare response
        response_data = ResourceAllocationResponseData(
            id=allocation.id,
            task_id=allocation.task_id,
            resource_id=allocation.resource_id,
            task_name=task.name if task else "Unknown Task",
            resource_name=resource.name if resource else "Unknown Resource",
            allocation_percentage=allocation.allocation_percentage,
            assigned_hours=allocation.assigned_hours,
            start_date=allocation.start_date,
            end_date=allocation.end_date,
            is_overallocated=allocation.is_overallocated,
            created_at=allocation.created_at,
            updated_at=allocation.updated_at
        )
        
        return ResourceAllocationResponse(
            status="success",
            message="Resource allocation retrieved successfully",
            data=response_data
        )
    
    async def list_allocations(
        self,
        task_id: Optional[UUID] = None,
        resource_id: Optional[UUID] = None,
        pagination: Optional[PaginationParams] = None
    ) -> ResourceAllocationListResponse:
        """
        List resource allocations with filtering and pagination.
        
        Args:
            task_id: Optional task ID filter
            resource_id: Optional resource ID filter
            pagination: Pagination parameters
            
        Returns:
            ResourceAllocationListResponse: List of allocations
        """
        logger.info(f"Listing allocations: task_id={task_id}, resource_id={resource_id}")
        
        # Prepare filters
        filters = {}
        if task_id:
            filters["task_id"] = task_id
        if resource_id:
            filters["resource_id"] = resource_id
        
        # Prepare pagination
        pagination_dict = pagination.model_dump() if pagination else {"page": 1, "page_size": 20}
        
        # Get allocations
        allocations, total = await self.repository.list_resource_allocations(filters, pagination_dict)
        
        # Prepare response data
        response_data = []
        for allocation in allocations:
            # Get task and resource for names
            task = await self.repository.get_task_by_id(allocation.task_id)
            resource = await self.repository.get_resource_by_id(allocation.resource_id)
            
            # Create response data
            allocation_data = ResourceAllocationResponseData(
                id=allocation.id,
                task_id=allocation.task_id,
                resource_id=allocation.resource_id,
                task_name=task.name if task else "Unknown Task",
                resource_name=resource.name if resource else "Unknown Resource",
                allocation_percentage=allocation.allocation_percentage,
                assigned_hours=allocation.assigned_hours,
                start_date=allocation.start_date,
                end_date=allocation.end_date,
                is_overallocated=allocation.is_overallocated,
                created_at=allocation.created_at,
                updated_at=allocation.updated_at
            )
            response_data.append(allocation_data)
        
        return ResourceAllocationListResponse(
            status="success",
            message=f"Retrieved {len(response_data)} allocations",
            data=response_data,
            pagination={
                "page": pagination_dict["page"],
                "page_size": pagination_dict["page_size"],
                "total": total,
                "pages": (total + pagination_dict["page_size"] - 1) // pagination_dict["page_size"]
            }
        )
    
    async def update_allocation(
        self,
        allocation_id: UUID,
        allocation_data: ResourceAllocationUpdate
    ) -> ResourceAllocationResponse:
        """
        Update a resource allocation.
        
        Args:
            allocation_id: Allocation ID
            allocation_data: Allocation data to update
            
        Returns:
            ResourceAllocationResponse: Updated allocation
            
        Raises:
            ResourceAllocationError: If allocation not found
        """
        logger.info(f"Updating allocation: {allocation_id}")
        
        # Get current allocation
        allocation = await self.repository.get_resource_allocation_by_id(allocation_id)
        if not allocation:
            raise ResourceAllocationError(
                message=f"Resource allocation not found: {allocation_id}",
                details={"allocation_id": str(allocation_id)}
            )
        
        # Convert to dictionary for repository
        allocation_dict = allocation_data.model_dump(exclude_unset=True)
        
        # Check for overallocation if hours are changing
        if "assigned_hours" in allocation_dict:
            resource = await self.repository.get_resource_by_id(allocation.resource_id)
            allocations = await self.repository.get_resource_allocations_by_resource(allocation.resource_id)
            
            # Calculate total hours excluding this allocation
            total_allocated_hours = sum(
                a.assigned_hours for a in allocations if a.id != allocation_id
            )
            
            # Add new hours
            new_total_hours = total_allocated_hours + allocation_dict["assigned_hours"]
            is_overallocated = new_total_hours > resource.capacity_hours
            
            # Update overallocation flag
            allocation_dict["is_overallocated"] = is_overallocated
        
        # Update allocation
        updated_allocation = await self.repository.update_resource_allocation(allocation_id, allocation_dict)
        
        # Get task and resource for names
        task = await self.repository.get_task_by_id(updated_allocation.task_id)
        resource = await self.repository.get_resource_by_id(updated_allocation.resource_id)
        
        # Prepare response
        response_data = ResourceAllocationResponseData(
            id=updated_allocation.id,
            task_id=updated_allocation.task_id,
            resource_id=updated_allocation.resource_id,
            task_name=task.name if task else "Unknown Task",
            resource_name=resource.name if resource else "Unknown Resource",
            allocation_percentage=updated_allocation.allocation_percentage,
            assigned_hours=updated_allocation.assigned_hours,
            start_date=updated_allocation.start_date,
            end_date=updated_allocation.end_date,
            is_overallocated=updated_allocation.is_overallocated,
            created_at=updated_allocation.created_at,
            updated_at=updated_allocation.updated_at
        )
        
        return ResourceAllocationResponse(
            status="success",
            message="Resource allocation updated successfully",
            data=response_data
        )
    
    async def delete_allocation(self, allocation_id: UUID) -> Dict[str, Any]:
        """
        Delete a resource allocation.
        
        Args:
            allocation_id: Allocation ID
            
        Returns:
            Dict[str, Any]: Response with status and message
            
        Raises:
            ResourceAllocationError: If allocation not found
        """
        logger.info(f"Deleting allocation: {allocation_id}")
        
        # Delete allocation
        deleted = await self.repository.delete_resource_allocation(allocation_id)
        if not deleted:
            raise ResourceAllocationError(
                message=f"Resource allocation not found: {allocation_id}",
                details={"allocation_id": str(allocation_id)}
            )
        
        return {
            "status": "success",
            "message": "Resource allocation deleted successfully"
        }
    
    async def get_resource_utilization(
        self,
        resource_id: Optional[UUID] = None,
        resource_type: Optional[ResourceType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get resource utilization.
        
        Args:
            resource_id: Optional resource ID filter
            resource_type: Optional resource type filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dict[str, Any]: Resource utilization data
        """
        logger.info(f"Getting resource utilization: resource_id={resource_id}, type={resource_type}")
        
        # Prepare filters
        filters = {}
        if resource_id:
            filters["resource_id"] = resource_id
        if resource_type:
            filters["resource_type"] = resource_type
        
        # Get resources
        resources, _ = await self.repository.list_resources(filters, {"page": 1, "page_size": 1000})
        
        # Prepare result
        result = {
            "resources": [],
            "summary": {
                "total_resources": len(resources),
                "total_capacity_hours": 0,
                "total_allocated_hours": 0,
                "overall_utilization": 0,
                "overallocated_resources": 0
            }
        }
        
        # Calculate utilization for each resource
        for resource in resources:
            # Get allocations
            allocations = await self.repository.get_resource_allocations_by_resource(resource.id)
            
            # Filter allocations by date if specified
            if start_date or end_date:
                filtered_allocations = []
                for allocation in allocations:
                    # Skip if allocation outside date range
                    if start_date and allocation.end_date < start_date:
                        continue
                    if end_date and allocation.start_date > end_date:
                        continue
                    filtered_allocations.append(allocation)
                allocations = filtered_allocations
            
            # Calculate total allocated hours
            total_allocated_hours = sum(allocation.assigned_hours for allocation in allocations)
            
            # Calculate utilization
            utilization_percentage = (total_allocated_hours / resource.capacity_hours) * 100 if resource.capacity_hours > 0 else 0
            is_overallocated = utilization_percentage > 100
            
            # Add to result
            resource_data = {
                "id": str(resource.id),
                "name": resource.name,
                "type": resource.resource_type.value,
                "capacity_hours": resource.capacity_hours,
                "allocated_hours": total_allocated_hours,
                "utilization_percentage": utilization_percentage,
                "is_overallocated": is_overallocated,
                "allocation_count": len(allocations)
            }
            result["resources"].append(resource_data)
            
            # Update summary
            result["summary"]["total_capacity_hours"] += resource.capacity_hours
            result["summary"]["total_allocated_hours"] += total_allocated_hours
            if is_overallocated:
                result["summary"]["overallocated_resources"] += 1
        
        # Calculate overall utilization
        if result["summary"]["total_capacity_hours"] > 0:
            result["summary"]["overall_utilization"] = (
                result["summary"]["total_allocated_hours"] / result["summary"]["total_capacity_hours"]
            ) * 100
        
        return result
