"""
Base classes for the Planning System service.

This module provides abstract base classes and common patterns
to support modularity and code reuse across planning components.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Union, Generic, TypeVar, Type
from uuid import UUID
from datetime import datetime

from shared.utils.src.messaging import EventBus

from ..exceptions import PlanningSystemError

# Type variables for generic type hinting
T = TypeVar('T')  # For entity data
R = TypeVar('R')  # For response models

class BasePlannerComponent:
    """
    Abstract base class for planner components.
    
    This class provides common functionality for all planner components,
    including logging, event publishing, and error handling.
    """
    
    def __init__(
        self,
        repository: Any,
        event_bus: EventBus,
        component_name: str = None,
    ):
        """
        Initialize the base planner component.
        
        Args:
            repository: Data repository
            event_bus: Event bus for publishing events
            component_name: Optional component name for logging
        """
        self.repository = repository
        self.event_bus = event_bus
        self.component_name = component_name or self.__class__.__name__
        self.logger = logging.getLogger(self.component_name)
        self.logger.info(f"{self.component_name} initialized")
    
    async def _publish_event(
        self, 
        event_type: str, 
        entity: Any, 
        additional_data: Dict[str, Any] = None
    ) -> None:
        """
        Publish an event with entity data.
        
        Args:
            event_type: Type of event (e.g., 'plan.created')
            entity: Entity data to include in event
            additional_data: Additional data to include in event
        """
        # Start with basic entity data
        event_data = {
            "id": str(entity.id),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Add common entity fields if they exist
        for field in ["name", "project_id", "plan_id", "status"]:
            if hasattr(entity, field):
                value = getattr(entity, field)
                # Convert enums to values and UUIDs to strings
                if hasattr(value, "value"):
                    value = value.value
                elif isinstance(value, UUID):
                    value = str(value)
                event_data[field] = value
        
        # Add timestamp fields if they exist
        for field in ["created_at", "updated_at"]:
            if hasattr(entity, field):
                value = getattr(entity, field)
                if isinstance(value, datetime):
                    event_data[field] = value.isoformat()
        
        # Add additional data if provided
        if additional_data:
            event_data.update(additional_data)
        
        # Publish the event
        self.logger.debug(f"Publishing event: {event_type}")
        await self.event_bus.publish(event_type, event_data)
    
    async def _handle_not_found_error(
        self, 
        entity_type: str, 
        entity_id: UUID, 
        error_class: Type[PlanningSystemError]
    ) -> None:
        """
        Handle a not found error consistently.
        
        Args:
            entity_type: Type of entity (e.g., 'plan', 'task')
            entity_id: ID of the entity
            error_class: Error class to raise
            
        Raises:
            PlanningSystemError: The specified error class
        """
        self.logger.warning(f"{entity_type.capitalize()} not found: {entity_id}")
        raise error_class(str(entity_id))
    
    async def _log_operation(
        self, 
        operation: str, 
        entity_type: str, 
        entity_id: Optional[UUID] = None, 
        entity_name: Optional[str] = None
    ) -> None:
        """
        Log an operation consistently.
        
        Args:
            operation: Operation being performed (e.g., 'Creating', 'Updating')
            entity_type: Type of entity (e.g., 'plan', 'task')
            entity_id: Optional entity ID
            entity_name: Optional entity name
        """
        message = f"{operation} {entity_type}"
        if entity_name:
            message += f": {entity_name}"
        if entity_id:
            message += f" (ID: {entity_id})"
        
        self.logger.info(message)


class ValidationStrategy(ABC, Generic[T]):
    """
    Abstract base class for validation strategies.
    
    This class defines the interface for validation strategies,
    which are responsible for validating entity data.
    """
    
    @abstractmethod
    async def validate(self, data: T, context: Dict[str, Any] = None) -> List[str]:
        """
        Validate entity data.
        
        Args:
            data: Entity data to validate
            context: Additional context for validation
            
        Returns:
            List[str]: List of validation error messages, empty if valid
        """
        pass


class ResponseBuilder(Generic[T, R]):
    """
    Builder for constructing response models.
    
    This class provides a fluent interface for building response models
    from entity data.
    """
    
    def __init__(self, entity: T):
        """
        Initialize the response builder.
        
        Args:
            entity: Entity data to build response from
        """
        self.entity = entity
        self.data = {}
    
    def with_base_fields(self) -> 'ResponseBuilder[T, R]':
        """
        Add base fields (id, created_at, updated_at) to response.
        
        Returns:
            ResponseBuilder: Self for chaining
        """
        self.data.update({
            "id": self.entity.id,
            "created_at": self.entity.created_at,
            "updated_at": self.entity.updated_at,
        })
        return self
    
    def with_field(self, field_name: str, value: Any = None) -> 'ResponseBuilder[T, R]':
        """
        Add a field to the response.
        
        Args:
            field_name: Name of the field
            value: Optional value, if not provided will get from entity
            
        Returns:
            ResponseBuilder: Self for chaining
        """
        if value is None and hasattr(self.entity, field_name):
            value = getattr(self.entity, field_name)
        
        self.data[field_name] = value
        return self
    
    def with_fields(self, field_names: List[str]) -> 'ResponseBuilder[T, R]':
        """
        Add multiple fields to the response.
        
        Args:
            field_names: List of field names to add
            
        Returns:
            ResponseBuilder: Self for chaining
        """
        for field_name in field_names:
            self.with_field(field_name)
        return self
    
    def with_computed_field(
        self, 
        field_name: str, 
        compute_func: callable
    ) -> 'ResponseBuilder[T, R]':
        """
        Add a computed field to the response.
        
        Args:
            field_name: Name of the field
            compute_func: Function to compute the field value
            
        Returns:
            ResponseBuilder: Self for chaining
        """
        self.data[field_name] = compute_func(self.entity)
        return self
    
    def build(self, response_class: Type[R]) -> R:
        """
        Build the response model.
        
        Args:
            response_class: Response model class
            
        Returns:
            R: Instantiated response model
        """
        return response_class(**self.data)
