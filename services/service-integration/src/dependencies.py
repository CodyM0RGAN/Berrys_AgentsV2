"""
Dependencies for the Service Integration service.

This module provides FastAPI dependencies for service components,
implementing the Dependency Injection pattern.
"""
import logging
from typing import Optional, Dict, Any
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .config import settings
from .services.discovery.service import ServiceDiscovery
from .services.discovery.factory import ServiceDiscoveryFactory
from .services.communication.client import ServiceClient
from .services.communication.mediator import RequestMediator
from .services.integration_facade import SystemIntegrationFacade
from .services.workflow.agent_task_execution import AgentTaskExecutionWorkflow
from .services.workflow.project_planning import ProjectPlanningWorkflow


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger("service_integration")


# Database connection
async_engine = create_async_engine(
    settings.get_database_url(),
    echo=settings.LOG_LEVEL == "DEBUG",
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# Database dependency
async def get_db():
    """
    Get a database session.
    
    This dependency provides a database session that is automatically
    closed when the request is complete.
    """
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()


# Service Discovery dependency
@lru_cache()
def get_service_discovery() -> ServiceDiscovery:
    """
    Get the service discovery instance.
    
    This dependency provides access to the service discovery functionality.
    """
    return ServiceDiscovery(cache_ttl=30)


# Service Client dependency
def get_service_client(
    service_discovery: ServiceDiscovery = Depends(get_service_discovery)
) -> ServiceClient:
    """
    Get the service client instance.
    
    This dependency provides a client for making requests to other services.
    """
    return ServiceClient(
        service_discovery=service_discovery,
        default_timeout=30.0,
        circuit_breaker_config={
            "failure_threshold": settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            "reset_timeout": settings.CIRCUIT_BREAKER_RESET_TIMEOUT,
            "half_open_max_calls": settings.CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS,
        }
    )


# Request Mediator dependency
def get_request_mediator(
    service_discovery: ServiceDiscovery = Depends(get_service_discovery)
) -> RequestMediator:
    """
    Get the request mediator instance.
    
    This dependency provides a mediator for handling different types of requests.
    """
    return RequestMediator(service_discovery=service_discovery)


# System Integration Facade dependency
def get_integration_facade(
    service_discovery: ServiceDiscovery = Depends(get_service_discovery),
    request_mediator: RequestMediator = Depends(get_request_mediator),
    service_client: ServiceClient = Depends(get_service_client)
) -> SystemIntegrationFacade:
    """
    Get the system integration facade instance.
    
    This dependency provides the main entry point for system integration functionality.
    """
    return SystemIntegrationFacade(
        service_discovery=service_discovery,
        request_mediator=request_mediator,
        service_client=service_client
    )


# Register workflow handlers
def register_workflow_handlers(
    request_mediator: RequestMediator = Depends(get_request_mediator),
    service_discovery: ServiceDiscovery = Depends(get_service_discovery),
    service_client: ServiceClient = Depends(get_service_client)
) -> None:
    """
    Register workflow handlers with the request mediator.
    
    This function sets up the handlers for different workflow types.
    """
    # Agent Task Execution Workflow
    agent_task_workflow = AgentTaskExecutionWorkflow(
        service_discovery=service_discovery,
        service_client=service_client
    )
    request_mediator.register_handler(
        "workflow.AGENT_TASK_EXECUTION",
        agent_task_workflow.execute
    )
    
    # Project Planning Workflow
    project_planning_workflow = ProjectPlanningWorkflow(
        service_discovery=service_discovery,
        service_client=service_client
    )
    request_mediator.register_handler(
        "workflow.PROJECT_PLANNING",
        project_planning_workflow.execute
    )
    
    logger.info("Workflow handlers registered")
