import logging
from typing import Dict, Any, Callable, Awaitable
from uuid import UUID

from shared.utils.src.messaging import EventBus

logger = logging.getLogger(__name__)


class EventHandler:
    """
    Event handler for the service.
    """
    
    def __init__(self, event_bus: EventBus):
        """
        Initialize the event handler.
        
        Args:
            event_bus: Event bus
        """
        self.event_bus = event_bus
    
    async def register_handlers(self) -> None:
        """
        Register event handlers.
        """
        # Register handlers for events
        await self.event_bus.subscribe_to_event("resource.created", self.handle_resource_created)
        await self.event_bus.subscribe_to_event("resource.updated", self.handle_resource_updated)
        await self.event_bus.subscribe_to_event("resource.deleted", self.handle_resource_deleted)
        
        # Register handlers for external events
        await self.event_bus.subscribe_to_event("external.event", self.handle_external_event)
        
        logger.info("Event handlers registered")
    
    async def handle_resource_created(self, event_data: Dict[str, Any]) -> None:
        """
        Handle resource created event.
        
        Args:
            event_data: Event data
        """
        resource_id = event_data.get("resource_id")
        logger.info(f"Resource created: {resource_id}")
        
        # Process event
        # ...
    
    async def handle_resource_updated(self, event_data: Dict[str, Any]) -> None:
        """
        Handle resource updated event.
        
        Args:
            event_data: Event data
        """
        resource_id = event_data.get("resource_id")
        updated_fields = event_data.get("updated_fields", [])
        logger.info(f"Resource updated: {resource_id}, fields: {updated_fields}")
        
        # Process event
        # ...
    
    async def handle_resource_deleted(self, event_data: Dict[str, Any]) -> None:
        """
        Handle resource deleted event.
        
        Args:
            event_data: Event data
        """
        resource_id = event_data.get("resource_id")
        logger.info(f"Resource deleted: {resource_id}")
        
        # Process event
        # ...
    
    async def handle_external_event(self, event_data: Dict[str, Any]) -> None:
        """
        Handle external event.
        
        Args:
            event_data: Event data
        """
        event_type = event_data.get("type")
        logger.info(f"External event received: {event_type}")
        
        # Process event
        # ...


# Event publishing helper functions

async def publish_resource_event(
    event_bus: EventBus,
    event_type: str,
    resource_id: UUID,
    owner_id: str,
    resource_type: str,
    resource_status: str,
    additional_data: Dict[str, Any] = None,
) -> None:
    """
    Publish a resource event.
    
    Args:
        event_bus: Event bus
        event_type: Event type
        resource_id: Resource ID
        owner_id: Owner ID
        resource_type: Resource type
        resource_status: Resource status
        additional_data: Additional event data
    """
    # Prepare event data
    event_data = {
        "resource_id": str(resource_id),
        "owner_id": owner_id,
        "type": resource_type,
        "status": resource_status,
    }
    
    # Add additional data
    if additional_data:
        event_data.update(additional_data)
    
    # Publish event
    await event_bus.publish_event(event_type, event_data)
    logger.debug(f"Published event: {event_type}, resource_id: {resource_id}")
