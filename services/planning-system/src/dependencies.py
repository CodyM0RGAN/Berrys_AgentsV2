"""
Planning System Service dependencies.

This module defines FastAPI dependencies used throughout the service,
including database sessions, service instances, and utility functions.
"""

import logging
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator, Optional

from .config import config, PlanningSystemConfig, get_settings
from shared.utils.src.messaging import EventBus, CommandBus

# Import service classes
from .services.planning_service import PlanningService
from .services.strategic_planner import StrategicPlanner
from .services.tactical_planner import TacticalPlanner
from .services.forecaster import ProjectForecaster
from .services.resource_optimizer import ResourceOptimizer
from .services.resource_service import ResourceService
from .services.dependency_manager import DependencyManager
from .services.repository import PlanningRepository
from .services.task_template_service import TaskTemplateService
from .services.dependency_type_service import DependencyTypeService
from .services.what_if_analysis_service import WhatIfAnalysisService

logger = logging.getLogger(__name__)

# Create database engine
_engine = None
_sessionmaker = None

def _get_engine():
    """Get or create SQLAlchemy engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_recycle=settings.database_pool_recycle,
        )
    return _engine

def _get_sessionmaker():
    """Get or create SQLAlchemy sessionmaker."""
    global _sessionmaker
    if _sessionmaker is None:
        engine = _get_engine()
        _sessionmaker = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
        )
    return _sessionmaker

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for database session.
    
    Yields:
        AsyncSession: SQLAlchemy async session
    """
    session_factory = _get_sessionmaker()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Event bus singleton
_event_bus = None

def get_event_bus(settings: PlanningSystemConfig = Depends(get_settings)) -> EventBus:
    """
    Dependency for event bus.
    
    Args:
        settings: Service settings
        
    Returns:
        EventBus: Event bus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus(settings.redis_url)
    return _event_bus

# Command bus singleton
_command_bus = None

def get_command_bus(settings: PlanningSystemConfig = Depends(get_settings)) -> CommandBus:
    """
    Dependency for command bus.
    
    Args:
        settings: Service settings
        
    Returns:
        CommandBus: Command bus instance
    """
    global _command_bus
    if _command_bus is None:
        _command_bus = CommandBus(settings.redis_url)
    return _command_bus

# Repository dependency
def get_repository(db: AsyncSession = Depends(get_db)) -> PlanningRepository:
    """
    Dependency for planning repository.
    
    Args:
        db: Database session
        
    Returns:
        PlanningRepository: Repository instance
    """
    return PlanningRepository(db)

# Component dependencies
def get_dependency_manager(
    repository: PlanningRepository = Depends(get_repository),
) -> DependencyManager:
    """
    Dependency for dependency manager.
    
    Args:
        repository: Repository instance
        
    Returns:
        DependencyManager: Dependency manager instance
    """
    return DependencyManager(repository)

def get_resource_optimizer(
    repository: PlanningRepository = Depends(get_repository),
    settings: PlanningSystemConfig = Depends(get_settings),
) -> ResourceOptimizer:
    """
    Dependency for resource optimizer.
    
    Args:
        repository: Repository instance
        settings: Service settings
        
    Returns:
        ResourceOptimizer: Resource optimizer instance
    """
    return ResourceOptimizer(
        repository=repository,
        solver=settings.default_solver,
        timeout=settings.resource_optimization_timeout,
    )

def get_strategic_planner(
    repository: PlanningRepository = Depends(get_repository),
    event_bus: EventBus = Depends(get_event_bus),
    resource_optimizer: ResourceOptimizer = Depends(get_resource_optimizer),
) -> StrategicPlanner:
    """
    Dependency for strategic planner.
    
    Args:
        repository: Repository instance
        event_bus: Event bus instance
        resource_optimizer: Resource optimizer instance
        
    Returns:
        StrategicPlanner: Strategic planner instance
    """
    return StrategicPlanner(
        repository=repository,
        event_bus=event_bus,
        resource_optimizer=resource_optimizer,
    )

def get_tactical_planner(
    repository: PlanningRepository = Depends(get_repository),
    event_bus: EventBus = Depends(get_event_bus),
    dependency_manager: DependencyManager = Depends(get_dependency_manager),
) -> TacticalPlanner:
    """
    Dependency for tactical planner.
    
    Args:
        repository: Repository instance
        event_bus: Event bus instance
        dependency_manager: Dependency manager instance
        
    Returns:
        TacticalPlanner: Tactical planner instance
    """
    return TacticalPlanner(
        repository=repository,
        event_bus=event_bus,
        dependency_manager=dependency_manager,
    )

def get_forecaster(
    repository: PlanningRepository = Depends(get_repository),
    event_bus: EventBus = Depends(get_event_bus),
    dependency_manager: DependencyManager = Depends(get_dependency_manager),
    settings: PlanningSystemConfig = Depends(get_settings),
) -> ProjectForecaster:
    """
    Dependency for project forecaster.
    
    Args:
        repository: Repository instance
        event_bus: Event bus instance
        dependency_manager: Dependency manager instance
        settings: Service settings
        
    Returns:
        ProjectForecaster: Project forecaster instance
    """
    return ProjectForecaster(
        repository=repository,
        event_bus=event_bus,
        dependency_manager=dependency_manager,
        confidence_interval=settings.forecasting_confidence_interval,
    )

# Resource service dependency
def get_resource_service(
    repository: PlanningRepository = Depends(get_repository),
) -> ResourceService:
    """
    Dependency for resource service.
    
    Args:
        repository: Repository instance
        
    Returns:
        ResourceService: Resource service instance
    """
    return ResourceService(repository=repository)

# Task template service dependency
def get_task_template_service(
    repository: PlanningRepository = Depends(get_repository),
    event_bus: EventBus = Depends(get_event_bus),
) -> TaskTemplateService:
    """
    Dependency for task template service.
    
    Args:
        repository: Repository instance
        event_bus: Event bus instance
        
    Returns:
        TaskTemplateService: Task template service instance
    """
    return TaskTemplateService(
        repository=repository,
        event_bus=event_bus,
    )

# Dependency type service dependency
def get_dependency_type_service(
    repository: PlanningRepository = Depends(get_repository),
    event_bus: EventBus = Depends(get_event_bus),
) -> DependencyTypeService:
    """
    Dependency for dependency type service.
    
    Args:
        repository: Repository instance
        event_bus: Event bus instance
        
    Returns:
        DependencyTypeService: Dependency type service instance
    """
    return DependencyTypeService(
        repository=repository,
        event_bus=event_bus,
    )

# What-if analysis service dependency
def get_what_if_analysis_service(
    repository: PlanningRepository = Depends(get_repository),
    event_bus: EventBus = Depends(get_event_bus),
    forecaster: ProjectForecaster = Depends(get_forecaster),
) -> WhatIfAnalysisService:
    """
    Dependency for what-if analysis service.
    
    Args:
        repository: Repository instance
        event_bus: Event bus instance
        forecaster: Project forecaster instance
        
    Returns:
        WhatIfAnalysisService: What-if analysis service instance
    """
    return WhatIfAnalysisService(
        repository=repository,
        event_bus=event_bus,
        forecaster=forecaster,
    )

# Main service dependency
def get_planning_service(
    db: AsyncSession = Depends(get_db),
    strategic_planner: StrategicPlanner = Depends(get_strategic_planner),
    tactical_planner: TacticalPlanner = Depends(get_tactical_planner),
    forecaster: ProjectForecaster = Depends(get_forecaster),
    resource_optimizer: ResourceOptimizer = Depends(get_resource_optimizer),
    resource_service: ResourceService = Depends(get_resource_service),
    dependency_manager: DependencyManager = Depends(get_dependency_manager),
    event_bus: EventBus = Depends(get_event_bus),
    command_bus: CommandBus = Depends(get_command_bus),
    settings: PlanningSystemConfig = Depends(get_settings),
) -> PlanningService:
    """
    Dependency for planning service.
    
    Args:
        db: Database session
        strategic_planner: Strategic planner instance
        tactical_planner: Tactical planner instance
        forecaster: Project forecaster instance
        resource_optimizer: Resource optimizer instance
        resource_service: Resource service instance
        dependency_manager: Dependency manager instance
        event_bus: Event bus instance
        command_bus: Command bus instance
        settings: Service settings
        
    Returns:
        PlanningService: Planning service instance
    """
    return PlanningService(
        db=db,
        strategic_planner=strategic_planner,
        tactical_planner=tactical_planner,
        forecaster=forecaster,
        resource_optimizer=resource_optimizer,
        resource_service=resource_service,
        dependency_manager=dependency_manager,
        event_bus=event_bus,
        command_bus=command_bus,
        settings=settings,
        task_template_service=get_task_template_service(),
        dependency_type_service=get_dependency_type_service(),
        what_if_analysis_service=get_what_if_analysis_service(forecaster=forecaster)
    )
