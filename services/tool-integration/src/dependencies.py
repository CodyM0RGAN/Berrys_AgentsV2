"""
Tool Integration Service dependencies.

This module defines FastAPI dependencies used throughout the service,
including database sessions, service instances, and utility functions.
"""

import logging
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator, Optional, Dict, Any

from .config import ToolIntegrationSettings, get_settings
from shared.utils.src.messaging import EventBus, CommandBus

# Import service classes - these will be implemented later
from .services.tool_service import ToolService
from .services.registry import ToolRegistry
from .services.repository import ToolRepository
from .services.discovery import DiscoveryService, DiscoveryStrategyFactory
from .services.evaluation import ToolEvaluationService
from .services.integration import ToolIntegrationService, IntegrationAdapterFactory
from .services.security import SecurityScanner

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

def get_event_bus(settings: ToolIntegrationSettings = Depends(get_settings)) -> EventBus:
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

def get_command_bus(settings: ToolIntegrationSettings = Depends(get_settings)) -> CommandBus:
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
def get_repository(db: AsyncSession = Depends(get_db)) -> ToolRepository:
    """
    Dependency for tool repository.
    
    Args:
        db: Database session
        
    Returns:
        ToolRepository: Repository instance
    """
    return ToolRepository(db)

# Component dependencies
def get_security_scanner(
    settings: ToolIntegrationSettings = Depends(get_settings),
) -> SecurityScanner:
    """
    Dependency for security scanner.
    
    Args:
        settings: Service settings
        
    Returns:
        SecurityScanner: Security scanner instance
    """
    return SecurityScanner(
        enabled=settings.security_scanning_enabled,
    )

def get_tool_registry(
    repository: ToolRepository = Depends(get_repository),
    event_bus: EventBus = Depends(get_event_bus),
    settings: ToolIntegrationSettings = Depends(get_settings),
) -> ToolRegistry:
    """
    Dependency for tool registry.
    
    Args:
        repository: Repository instance
        event_bus: Event bus instance
        settings: Service settings
        
    Returns:
        ToolRegistry: Tool registry instance
    """
    return ToolRegistry(
        repository=repository,
        event_bus=event_bus,
        cache_ttl=settings.tool_registry_cache_ttl,
    )

def get_discovery_factory(
    settings: ToolIntegrationSettings = Depends(get_settings),
) -> DiscoveryStrategyFactory:
    """
    Dependency for discovery strategy factory.
    
    Args:
        settings: Service settings
        
    Returns:
        DiscoveryStrategyFactory: Discovery strategy factory instance
    """
    return DiscoveryStrategyFactory(
        batch_size=settings.discovery_batch_size,
        max_depth=settings.max_discovery_depth,
    )

def get_discovery_service(
    repository: ToolRepository = Depends(get_repository),
    event_bus: EventBus = Depends(get_event_bus),
    discovery_factory: DiscoveryStrategyFactory = Depends(get_discovery_factory),
    settings: ToolIntegrationSettings = Depends(get_settings),
) -> DiscoveryService:
    """
    Dependency for discovery service.
    
    Args:
        repository: Repository instance
        event_bus: Event bus instance
        discovery_factory: Discovery strategy factory
        settings: Service settings
        
    Returns:
        DiscoveryService: Discovery service instance
    """
    return DiscoveryService(
        repository=repository,
        event_bus=event_bus,
        discovery_factory=discovery_factory,
        cache_ttl=settings.discovery_cache_ttl,
    )

def get_evaluation_service(
    repository: ToolRepository = Depends(get_repository),
    security_scanner: SecurityScanner = Depends(get_security_scanner),
    settings: ToolIntegrationSettings = Depends(get_settings),
) -> ToolEvaluationService:
    """
    Dependency for evaluation service.
    
    Args:
        repository: Repository instance
        security_scanner: Security scanner instance
        settings: Service settings
        
    Returns:
        ToolEvaluationService: Evaluation service instance
    """
    return ToolEvaluationService(
        repository=repository,
        security_scanner=security_scanner,
        schema_validation_enabled=settings.schema_validation_enabled,
    )

def get_integration_factory(
    settings: ToolIntegrationSettings = Depends(get_settings),
) -> IntegrationAdapterFactory:
    """
    Dependency for integration adapter factory.
    
    Args:
        settings: Service settings
        
    Returns:
        IntegrationAdapterFactory: Integration adapter factory instance
    """
    return IntegrationAdapterFactory(
        mcp_connection_timeout=settings.mcp_connection_timeout,
        mcp_request_timeout=settings.mcp_request_timeout,
        mcp_servers_config_path=settings.mcp_servers_config_path,
    )

def get_integration_service(
    repository: ToolRepository = Depends(get_repository),
    event_bus: EventBus = Depends(get_event_bus),
    integration_factory: IntegrationAdapterFactory = Depends(get_integration_factory),
    security_scanner: SecurityScanner = Depends(get_security_scanner),
    settings: ToolIntegrationSettings = Depends(get_settings),
) -> ToolIntegrationService:
    """
    Dependency for integration service.
    
    Args:
        repository: Repository instance
        event_bus: Event bus instance
        integration_factory: Integration adapter factory
        security_scanner: Security scanner instance
        settings: Service settings
        
    Returns:
        ToolIntegrationService: Integration service instance
    """
    return ToolIntegrationService(
        repository=repository,
        event_bus=event_bus,
        integration_factory=integration_factory,
        security_scanner=security_scanner,
        tool_execution_timeout=settings.tool_execution_timeout,
        max_tool_memory_mb=settings.max_tool_memory_mb,
        max_tool_execution_time_sec=settings.max_tool_execution_time_sec,
        sandboxed_execution=settings.sandboxed_execution,
    )

# Main service dependency - using the Facade pattern
def get_tool_service(
    registry: ToolRegistry = Depends(get_tool_registry),
    repository: ToolRepository = Depends(get_repository),
    discovery_service: DiscoveryService = Depends(get_discovery_service),
    evaluation_service: ToolEvaluationService = Depends(get_evaluation_service),
    integration_service: ToolIntegrationService = Depends(get_integration_service),
    security_scanner: SecurityScanner = Depends(get_security_scanner),
    event_bus: EventBus = Depends(get_event_bus),
    settings: ToolIntegrationSettings = Depends(get_settings),
) -> ToolService:
    """
    Dependency for tool service (main facade).
    
    Args:
        registry: Tool registry instance
        repository: Tool repository instance
        discovery_service: Discovery service instance
        evaluation_service: Evaluation service instance
        integration_service: Integration service instance
        security_scanner: Security scanner instance
        event_bus: Event bus instance
        settings: Service settings
        
    Returns:
        ToolService: Tool service facade instance
    """
    return ToolService(
        registry=registry,
        repository=repository,
        discovery_service=discovery_service,
        evaluation_service=evaluation_service,
        integration_service=integration_service,
        security_scanner=security_scanner,
    )
