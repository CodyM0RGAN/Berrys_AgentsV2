"""
Model service implementation.

This module contains the main ModelService class that coordinates all model operations.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from shared.utils.src.messaging import EventBus, CommandBus

from ...config import ModelOrchestrationConfig, config
from ...providers.provider_factory import ProviderFactory
from ..performance_tracker import PerformanceTracker
from .model_management import ModelManagementMixin
from .request_processing import RequestProcessingMixin
from .logging import LoggingMixin

logger = logging.getLogger(__name__)


class ModelService(ModelManagementMixin, RequestProcessingMixin, LoggingMixin):
    """
    Service for model operations.
    
    This service is responsible for:
    - Managing models (registration, retrieval, updates, deletion)
    - Processing model requests (chat, completion, embedding, etc.)
    - Logging requests and tracking performance
    """
    
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        command_bus: CommandBus,
        settings: ModelOrchestrationConfig,
        provider_factory: ProviderFactory,
        performance_tracker: Optional[PerformanceTracker] = None,
    ):
        """
        Initialize the model service.
        
        Args:
            db: Database session
            event_bus: Event bus
            command_bus: Command bus
            settings: Application settings
            provider_factory: Provider factory
            performance_tracker: Performance tracker
        """
        self.db = db
        self.event_bus = event_bus
        self.command_bus = command_bus
        self.settings = config
        self.provider_factory = provider_factory
        self.performance_tracker = performance_tracker
