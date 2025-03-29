import logging
from typing import Dict, Any, Optional
from uuid import UUID

from shared.utils.src.messaging import CommandBus
from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import ResourceNotFoundError, ValidationError
from ..models.api import ResourceStatus, ResourceType
from ..services.resource_service import ResourceService

logger = logging.getLogger(__name__)


class CommandHandler:
    """
    Command handler for the service.
    """
    
    def __init__(self, command_bus: CommandBus, resource_service: ResourceService):
        """
        Initialize the command handler.
        
        Args:
            command_bus: Command bus
            resource_service: Resource service
        """
        self.command_bus = command_bus
        self.resource_service = resource_service
    
    async def register_handlers(self) -> None:
        """
        Register command handlers.
        """
        # Register handlers for commands
        await self.command_bus.register_command_handler("resource.create", self.handle_create_resource)
        await self.command_bus.register_command_handler("resource.update", self.handle_update_resource)
        await self.command_bus.register_command_handler("resource.delete", self.handle_delete_resource)
        await self.command_bus.register_command_handler("resource.change_status", self.handle_change_resource_status)
        
        logger.info("Command handlers registered")
    
    async def handle_create_resource(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle create resource command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            ValidationError: If command data is invalid
        """
        try:
            # Validate command data
            name = command_data.get("name")
            if not name:
                raise ValidationError("Name is required")
            
            # Create resource data
            resource_data = {
                "name": name,
                "description": command_data.get("description"),
                "type": command_data.get("type", "TYPE_A"),
                "status": command_data.get("status", "DRAFT"),
                "owner_id": command_data.get("owner_id"),
                "metadata": command_data.get("metadata", {}),
            }
            
            # Create resource
            from ..models.api import ResourceCreate
            resource = await self.resource_service.create_resource(
                ResourceCreate(**resource_data)
            )
            
            # Return result
            return {
                "resource_id": str(resource.id),
                "status": "created",
            }
        except Exception as e:
            logger.error(f"Error handling create resource command: {str(e)}")
            raise
    
    async def handle_update_resource(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle update resource command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            ResourceNotFoundError: If resource not found
            ValidationError: If command data is invalid
        """
        try:
            # Validate command data
            resource_id = command_data.get("resource_id")
            if not resource_id:
                raise ValidationError("Resource ID is required")
            
            # Create update data
            update_data = {}
            
            if "name" in command_data:
                update_data["name"] = command_data["name"]
            
            if "description" in command_data:
                update_data["description"] = command_data["description"]
            
            if "type" in command_data:
                update_data["type"] = ResourceType(command_data["type"])
            
            if "status" in command_data:
                update_data["status"] = ResourceStatus(command_data["status"])
            
            if "metadata" in command_data:
                update_data["metadata"] = command_data["metadata"]
            
            # Update resource
            from ..models.api import ResourceUpdate
            resource = await self.resource_service.update_resource(
                UUID(resource_id),
                ResourceUpdate(**update_data)
            )
            
            # Return result
            return {
                "resource_id": str(resource.id),
                "status": "updated",
                "updated_fields": list(update_data.keys()),
            }
        except Exception as e:
            logger.error(f"Error handling update resource command: {str(e)}")
            raise
    
    async def handle_delete_resource(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle delete resource command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            ResourceNotFoundError: If resource not found
            ValidationError: If command data is invalid
        """
        try:
            # Validate command data
            resource_id = command_data.get("resource_id")
            if not resource_id:
                raise ValidationError("Resource ID is required")
            
            # Delete resource
            await self.resource_service.delete_resource(UUID(resource_id))
            
            # Return result
            return {
                "resource_id": resource_id,
                "status": "deleted",
            }
        except Exception as e:
            logger.error(f"Error handling delete resource command: {str(e)}")
            raise
    
    async def handle_change_resource_status(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle change resource status command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            ResourceNotFoundError: If resource not found
            ValidationError: If command data is invalid
        """
        try:
            # Validate command data
            resource_id = command_data.get("resource_id")
            if not resource_id:
                raise ValidationError("Resource ID is required")
            
            status = command_data.get("status")
            if not status:
                raise ValidationError("Status is required")
            
            # Create update data
            update_data = {
                "status": ResourceStatus(status),
            }
            
            # Update resource
            from ..models.api import ResourceUpdate
            resource = await self.resource_service.update_resource(
                UUID(resource_id),
                ResourceUpdate(**update_data)
            )
            
            # Return result
            return {
                "resource_id": str(resource.id),
                "status": "updated",
                "new_status": status,
            }
        except Exception as e:
            logger.error(f"Error handling change resource status command: {str(e)}")
            raise


# Command sending helper functions

async def send_create_resource_command(
    command_bus: CommandBus,
    name: str,
    description: Optional[str] = None,
    resource_type: str = "TYPE_A",
    owner_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send create resource command.
    
    Args:
        command_bus: Command bus
        name: Resource name
        description: Resource description
        resource_type: Resource type
        owner_id: Owner ID
        metadata: Resource metadata
        
    Returns:
        Dict[str, Any]: Command result
    """
    # Prepare command data
    command_data = {
        "name": name,
        "type": resource_type,
        "owner_id": owner_id,
    }
    
    if description:
        command_data["description"] = description
    
    if metadata:
        command_data["metadata"] = metadata
    
    # Send command
    result = await command_bus.send_command(
        "service-name",
        "resource.create",
        command_data,
        wait_for_response=True,
    )
    
    return result
