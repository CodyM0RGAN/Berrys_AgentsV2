import logging
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from shared.utils.src.messaging import EventBus, CommandBus

from ..config import Settings
from ..exceptions import ResourceNotFoundError, ValidationError, DatabaseError
from ..models.api import ResourceCreate, ResourceUpdate, Resource, ResourceStatus
from ..models.internal import ResourceModel

logger = logging.getLogger(__name__)


class ResourceService:
    """
    Service for resource operations.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        command_bus: CommandBus,
        settings: Settings,
    ):
        """
        Initialize the resource service.
        
        Args:
            db: Database session
            event_bus: Event bus
            command_bus: Command bus
            settings: Application settings
        """
        self.db = db
        self.event_bus = event_bus
        self.command_bus = command_bus
        self.settings = settings
    
    async def create_resource(self, resource_data: ResourceCreate) -> Resource:
        """
        Create a new resource.
        
        Args:
            resource_data: Resource data
            
        Returns:
            Resource: Created resource
            
        Raises:
            ValidationError: If resource data is invalid
            DatabaseError: If database operation fails
        """
        try:
            # Create resource model
            resource_model = ResourceModel(
                name=resource_data.name,
                description=resource_data.description,
                type=resource_data.type,
                status=resource_data.status,
                owner_id=resource_data.owner_id,
                metadata=resource_data.metadata,
            )
            
            # Add to database
            self.db.add(resource_model)
            await self.db.commit()
            await self.db.refresh(resource_model)
            
            # Convert to API model
            resource = Resource.from_orm(resource_model)
            
            # Publish event
            await self.event_bus.publish_event(
                "resource.created",
                {
                    "resource_id": str(resource.id),
                    "owner_id": resource.owner_id,
                    "type": resource.type.value,
                    "status": resource.status.value,
                }
            )
            
            return resource
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating resource: {str(e)}")
            
            if isinstance(e, ValidationError):
                raise
            
            raise DatabaseError(f"Failed to create resource: {str(e)}")
    
    async def get_resource(self, resource_id: UUID) -> Optional[Resource]:
        """
        Get a resource by ID.
        
        Args:
            resource_id: Resource ID
            
        Returns:
            Optional[Resource]: Resource if found, None otherwise
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Query resource
            query = select(ResourceModel).where(ResourceModel.id == resource_id)
            result = await self.db.execute(query)
            resource_model = result.scalars().first()
            
            # Return None if not found
            if not resource_model:
                return None
            
            # Convert to API model
            return Resource.from_orm(resource_model)
        except Exception as e:
            logger.error(f"Error getting resource {resource_id}: {str(e)}")
            raise DatabaseError(f"Failed to get resource: {str(e)}")
    
    async def list_resources(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        type: Optional[str] = None,
        search: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Tuple[List[Resource], int]:
        """
        List resources with pagination and filtering.
        
        Args:
            page: Page number
            page_size: Page size
            status: Filter by status
            type: Filter by type
            search: Search term
            user_id: Filter by owner ID
            
        Returns:
            Tuple[List[Resource], int]: List of resources and total count
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Build query
            query = select(ResourceModel)
            count_query = select(func.count()).select_from(ResourceModel)
            
            # Apply filters
            filters = []
            
            if status:
                try:
                    status_enum = ResourceStatus(status)
                    filters.append(ResourceModel.status == status_enum)
                except ValueError:
                    # Invalid status, ignore filter
                    pass
            
            if type:
                filters.append(ResourceModel.type == type)
            
            if search:
                search_filter = or_(
                    ResourceModel.name.ilike(f"%{search}%"),
                    ResourceModel.description.ilike(f"%{search}%"),
                )
                filters.append(search_filter)
            
            if user_id:
                filters.append(ResourceModel.owner_id == user_id)
            
            # Apply filters to queries
            if filters:
                filter_clause = and_(*filters)
                query = query.where(filter_clause)
                count_query = count_query.where(filter_clause)
            
            # Get total count
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()
            
            # Apply pagination
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # Execute query
            result = await self.db.execute(query)
            resource_models = result.scalars().all()
            
            # Convert to API models
            resources = [Resource.from_orm(model) for model in resource_models]
            
            return resources, total
        except Exception as e:
            logger.error(f"Error listing resources: {str(e)}")
            raise DatabaseError(f"Failed to list resources: {str(e)}")
    
    async def update_resource(
        self,
        resource_id: UUID,
        resource_update: ResourceUpdate,
    ) -> Resource:
        """
        Update a resource.
        
        Args:
            resource_id: Resource ID
            resource_update: Resource update data
            
        Returns:
            Resource: Updated resource
            
        Raises:
            ResourceNotFoundError: If resource not found
            ValidationError: If resource data is invalid
            DatabaseError: If database operation fails
        """
        try:
            # Query resource
            query = select(ResourceModel).where(ResourceModel.id == resource_id)
            result = await self.db.execute(query)
            resource_model = result.scalars().first()
            
            # Check if resource exists
            if not resource_model:
                raise ResourceNotFoundError("Resource", str(resource_id))
            
            # Update fields
            update_data = resource_update.dict(exclude_unset=True)
            
            for key, value in update_data.items():
                setattr(resource_model, key, value)
            
            # Commit changes
            await self.db.commit()
            await self.db.refresh(resource_model)
            
            # Convert to API model
            resource = Resource.from_orm(resource_model)
            
            # Publish event
            await self.event_bus.publish_event(
                "resource.updated",
                {
                    "resource_id": str(resource.id),
                    "owner_id": resource.owner_id,
                    "type": resource.type.value,
                    "status": resource.status.value,
                    "updated_fields": list(update_data.keys()),
                }
            )
            
            return resource
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating resource {resource_id}: {str(e)}")
            
            if isinstance(e, (ResourceNotFoundError, ValidationError)):
                raise
            
            raise DatabaseError(f"Failed to update resource: {str(e)}")
    
    async def delete_resource(self, resource_id: UUID) -> None:
        """
        Delete a resource.
        
        Args:
            resource_id: Resource ID
            
        Raises:
            ResourceNotFoundError: If resource not found
            DatabaseError: If database operation fails
        """
        try:
            # Query resource
            query = select(ResourceModel).where(ResourceModel.id == resource_id)
            result = await self.db.execute(query)
            resource_model = result.scalars().first()
            
            # Check if resource exists
            if not resource_model:
                raise ResourceNotFoundError("Resource", str(resource_id))
            
            # Store resource data for event
            resource_data = {
                "resource_id": str(resource_model.id),
                "owner_id": resource_model.owner_id,
                "type": resource_model.type.value,
                "status": resource_model.status.value,
            }
            
            # Delete resource
            await self.db.delete(resource_model)
            await self.db.commit()
            
            # Publish event
            await self.event_bus.publish_event(
                "resource.deleted",
                resource_data
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting resource {resource_id}: {str(e)}")
            
            if isinstance(e, ResourceNotFoundError):
                raise
            
            raise DatabaseError(f"Failed to delete resource: {str(e)}")
