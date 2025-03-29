"""
Base service class for the Planning System.

This module provides the BaseService abstract class that should be
extended by all service implementations in the planning system.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from uuid import UUID

from shared.utils.src.messaging import EventBus

from .base import BasePlannerComponent
from ..exceptions import PlanningSystemError

class BaseService(BasePlannerComponent):
    """
    Abstract base class for services in the Planning System.
    
    This class extends BasePlannerComponent to provide a standard
    interface for all service implementations.
    """
    
    def __init__(
        self,
        repository: Any,
        event_bus: EventBus,
        service_name: str = None,
    ):
        """
        Initialize the base service.
        
        Args:
            repository: Data repository
            event_bus: Event bus for publishing events
            service_name: Optional service name for logging
        """
        super().__init__(repository, event_bus, service_name or self.__class__.__name__)
    
    async def initialize(self) -> None:
        """
        Initialize the service.
        
        This method is called during application startup and can be
        overridden to perform service-specific initialization.
        """
        self.logger.info(f"Initializing {self.component_name}")
    
    async def shutdown(self) -> None:
        """
        Shutdown the service.
        
        This method is called during application shutdown and can be
        overridden to perform service-specific cleanup.
        """
        self.logger.info(f"Shutting down {self.component_name}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the service.
        
        Returns:
            Dict[str, Any]: Health check result with status and details
        """
        return {
            "status": "healthy",
            "service": self.component_name,
            "details": {}
        }
