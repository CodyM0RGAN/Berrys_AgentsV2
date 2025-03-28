"""
Planning Methodology Service for the Planning System.

This module implements the planning methodology service, which handles
methodology management for strategic plans.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from shared.utils.src.messaging import EventBus

from ..config import PlanningSystemConfig as Settings
from ..models.api import (
    PlanningMethodologyCreate,
    PlanningMethodologyUpdate,
    PlanningMethodologyResponse,
    PaginatedResponse
)
from ..exceptions import (
    MethodologyNotFoundError,
    MethodologyValidationError
)
from .repository import PlanningRepository

logger = logging.getLogger(__name__)

class PlanningMethodologyService:
    """
    Planning methodology service.
    
    This service handles methodology management for strategic plans,
    providing methods for creating, updating, and managing planning methodologies.
    """
    
    def __init__(
        self,
        repository: PlanningRepository,
        event_bus: EventBus,
    ):
        """
        Initialize the planning methodology service.
        
        Args:
            repository: Planning repository
            event_bus: Event bus
        """
        self.repository = repository
        self.event_bus = event_bus
        logger.info("Planning Methodology Service initialized")
    
    async def create_methodology(self, methodology_data: PlanningMethodologyCreate) -> PlanningMethodologyResponse:
        """
        Create a new planning methodology.
        
        Args:
            methodology_data: Methodology data
            
        Returns:
            PlanningMethodologyResponse: Created methodology
            
        Raises:
            MethodologyValidationError: If methodology data is invalid
        """
        logger.info(f"Creating methodology: {methodology_data.name}")
        
        # Validate methodology data
        await self._validate_methodology_data(methodology_data)
        
        # Convert to dict for repository
        methodology_dict = methodology_data.model_dump()
        
        # Create methodology in repository
        methodology = await self.repository.create_methodology(methodology_dict)
        
        # Publish event
        await self._publish_methodology_created_event(methodology)
        
        # Convert to response model
        return await self._to_methodology_response_model(methodology)
    
    async def get_methodology(self, methodology_id: UUID) -> PlanningMethodologyResponse:
        """
        Get a planning methodology by ID.
        
        Args:
            methodology_id: Methodology ID
            
        Returns:
            PlanningMethodologyResponse: Methodology data
            
        Raises:
            MethodologyNotFoundError: If methodology not found
        """
        logger.info(f"Getting methodology: {methodology_id}")
        
        # Get methodology from repository
        methodology = await self.repository.get_methodology_by_id(methodology_id)
        
        if not methodology:
            raise MethodologyNotFoundError(str(methodology_id))
        
        # Convert to response model
        return await self._to_methodology_response_model(methodology)
    
    async def list_methodologies(
        self,
        is_active: Optional[bool] = None,
        methodology_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """
        List planning methodologies with filtering and pagination.
        
        Args:
            is_active: Optional active status filter
            methodology_type: Optional methodology type filter
            page: Page number
            page_size: Items per page
            
        Returns:
            PaginatedResponse: Paginated list of methodologies
        """
        logger.info(f"Listing methodologies (is_active={is_active}, type={methodology_type})")
        
        # Build filters
        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active
        if methodology_type is not None:
            filters["methodology_type"] = methodology_type
        
        # Get methodologies from repository
        methodologies, total = await self.repository.list_methodologies(
            filters=filters,
            pagination={"page": page, "page_size": page_size}
        )
        
        # Convert to response models
        methodology_responses = [await self._to_methodology_response_model(methodology) for methodology in methodologies]
        
        # Build paginated response
        return PaginatedResponse(
            items=methodology_responses,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
    
    async def update_methodology(
        self,
        methodology_id: UUID,
        methodology_data: PlanningMethodologyUpdate
    ) -> PlanningMethodologyResponse:
        """
        Update a planning methodology.
        
        Args:
            methodology_id: Methodology ID
            methodology_data: Methodology data to update
            
        Returns:
            PlanningMethodologyResponse: Updated methodology
            
        Raises:
            MethodologyNotFoundError: If methodology not found
            MethodologyValidationError: If update data is invalid
        """
        logger.info(f"Updating methodology: {methodology_id}")
        
        # Validate update data
        await self._validate_methodology_update(methodology_id, methodology_data)
        
        # Convert to dict for repository
        update_dict = methodology_data.model_dump(exclude_unset=True)
        
        # Update methodology in repository
        methodology = await self.repository.update_methodology(methodology_id, update_dict)
        
        if not methodology:
            raise MethodologyNotFoundError(str(methodology_id))
        
        # Publish event
        await self._publish_methodology_updated_event(methodology)
        
        # Convert to response model
        return await self._to_methodology_response_model(methodology)
    
    async def delete_methodology(self, methodology_id: UUID) -> None:
        """
        Delete a planning methodology.
        
        Args:
            methodology_id: Methodology ID
            
        Raises:
            MethodologyNotFoundError: If methodology not found
            MethodologyValidationError: If methodology is in use
        """
        logger.info(f"Deleting methodology: {methodology_id}")
        
        # Get methodology data for event
        methodology = await self.repository.get_methodology_by_id(methodology_id)
        
        if not methodology:
            raise MethodologyNotFoundError(str(methodology_id))
        
        # Check if methodology is in use
        plans_using_methodology = await self.repository.count_plans_using_methodology(methodology_id)
        if plans_using_methodology > 0:
            raise MethodologyValidationError(
                message=f"Cannot delete methodology that is in use by {plans_using_methodology} plans",
                validation_errors=["Methodology is in use by existing plans"]
            )
        
        # Delete methodology in repository
        success = await self.repository.delete_methodology(methodology_id)
        
        if not success:
            raise MethodologyNotFoundError(str(methodology_id))
        
        # Publish event
        await self._publish_methodology_deleted_event(methodology)
    
    async def clone_methodology(self, methodology_id: UUID, new_name: str) -> PlanningMethodologyResponse:
        """
        Clone a planning methodology.
        
        Args:
            methodology_id: Source methodology ID
            new_name: Name for the cloned methodology
            
        Returns:
            PlanningMethodologyResponse: Cloned methodology
            
        Raises:
            MethodologyNotFoundError: If methodology not found
        """
        logger.info(f"Cloning methodology: {methodology_id}")
        
        # Get source methodology
        source_methodology = await self.repository.get_methodology_by_id(methodology_id)
        
        if not source_methodology:
            raise MethodologyNotFoundError(str(methodology_id))
        
        # Create new methodology data
        new_methodology_data = {
            "name": new_name,
            "description": source_methodology.description,
            "methodology_type": source_methodology.methodology_type,
            "parameters": source_methodology.parameters,
            "constraints": source_methodology.constraints,
            "is_active": True,
        }
        
        # Create new methodology
        new_methodology = await self.repository.create_methodology(new_methodology_data)
        
        # Publish event
        await self._publish_methodology_cloned_event(new_methodology, source_methodology)
        
        # Convert to response model
        return await self._to_methodology_response_model(new_methodology)
    
    # Helper methods
    
    async def _validate_methodology_data(self, methodology_data: PlanningMethodologyCreate) -> None:
        """
        Validate methodology data for creation.
        
        Args:
            methodology_data: Methodology data
            
        Raises:
            MethodologyValidationError: If methodology data is invalid
        """
        validation_errors = []
        
        # Validate parameters has required fields based on methodology type
        parameters = methodology_data.parameters
        methodology_type = methodology_data.methodology_type.upper()
        
        if methodology_type == "AGILE":
            if "sprint_duration" not in parameters:
                validation_errors.append("Agile methodology must specify sprint_duration parameter")
        elif methodology_type == "WATERFALL":
            if "phase_structure" not in parameters:
                validation_errors.append("Waterfall methodology must specify phase_structure parameter")
        elif methodology_type == "CRITICAL_PATH":
            if "critical_path_algorithm" not in parameters:
                validation_errors.append("Critical Path methodology must specify critical_path_algorithm parameter")
        
        # Raise error if any validation errors
        if validation_errors:
            raise MethodologyValidationError(
                message="Invalid methodology data",
                validation_errors=validation_errors
            )
    
    async def _validate_methodology_update(self, methodology_id: UUID, methodology_data: PlanningMethodologyUpdate) -> None:
        """
        Validate methodology data for update.
        
        Args:
            methodology_id: Methodology ID
            methodology_data: Methodology data
            
        Raises:
            MethodologyValidationError: If methodology data is invalid
        """
        validation_errors = []
        
        # Get existing methodology
        methodology = await self.repository.get_methodology_by_id(methodology_id)
        
        if not methodology:
            raise MethodologyNotFoundError(str(methodology_id))
        
        # Validate parameters has required fields based on methodology type if provided
        if methodology_data.parameters is not None and methodology_data.methodology_type is not None:
            parameters = methodology_data.parameters
            methodology_type = methodology_data.methodology_type.upper()
            
            if methodology_type == "AGILE":
                if "sprint_duration" not in parameters:
                    validation_errors.append("Agile methodology must specify sprint_duration parameter")
            elif methodology_type == "WATERFALL":
                if "phase_structure" not in parameters:
                    validation_errors.append("Waterfall methodology must specify phase_structure parameter")
            elif methodology_type == "CRITICAL_PATH":
                if "critical_path_algorithm" not in parameters:
                    validation_errors.append("Critical Path methodology must specify critical_path_algorithm parameter")
        
        # Raise error if any validation errors
        if validation_errors:
            raise MethodologyValidationError(
                message="Invalid methodology update",
                validation_errors=validation_errors
            )
    
    async def _to_methodology_response_model(self, methodology) -> PlanningMethodologyResponse:
        """
        Convert a methodology model to a response model.
        
        Args:
            methodology: Planning methodology model
            
        Returns:
            PlanningMethodologyResponse: Methodology response model
        """
        # Count plans using this methodology
        plan_count = await self.repository.count_plans_using_methodology(methodology.id)
        
        # Convert to response model
        return PlanningMethodologyResponse(
            id=methodology.id,
            name=methodology.name,
            description=methodology.description,
            methodology_type=methodology.methodology_type,
            parameters=methodology.parameters,
            constraints=methodology.constraints,
            is_active=methodology.is_active,
            created_at=methodology.created_at,
            updated_at=methodology.updated_at,
            plan_count=plan_count,
        )
    
    # Event methods
    
    async def _publish_methodology_created_event(self, methodology) -> None:
        """
        Publish methodology created event.
        
        Args:
            methodology: Created methodology
        """
        event_data = {
            "methodology_id": str(methodology.id),
            "name": methodology.name,
            "methodology_type": methodology.methodology_type,
            "created_at": methodology.created_at.isoformat(),
        }
        
        await self.event_bus.publish("methodology.created", event_data)
    
    async def _publish_methodology_updated_event(self, methodology) -> None:
        """
        Publish methodology updated event.
        
        Args:
            methodology: Updated methodology
        """
        event_data = {
            "methodology_id": str(methodology.id),
            "name": methodology.name,
            "methodology_type": methodology.methodology_type,
            "updated_at": methodology.updated_at.isoformat(),
        }
        
        await self.event_bus.publish("methodology.updated", event_data)
    
    async def _publish_methodology_deleted_event(self, methodology) -> None:
        """
        Publish methodology deleted event.
        
        Args:
            methodology: Deleted methodology
        """
        event_data = {
            "methodology_id": str(methodology.id),
            "name": methodology.name,
            "methodology_type": methodology.methodology_type,
        }
        
        await self.event_bus.publish("methodology.deleted", event_data)
    
    async def _publish_methodology_cloned_event(self, new_methodology, source_methodology) -> None:
        """
        Publish methodology cloned event.
        
        Args:
            new_methodology: Cloned methodology
            source_methodology: Source methodology
        """
        event_data = {
            "methodology_id": str(new_methodology.id),
            "name": new_methodology.name,
            "methodology_type": new_methodology.methodology_type,
            "source_methodology_id": str(source_methodology.id),
            "source_methodology_name": source_methodology.name,
            "created_at": new_methodology.created_at.isoformat(),
        }
        
        await self.event_bus.publish("methodology.cloned", event_data)
