"""
Main module for the Service Integration service.

This module sets up the FastAPI application, includes routers,
configures middleware, and adds startup and shutdown events.
"""
import logging
import asyncio
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import config, get_settings
from .exceptions import ServiceIntegrationError, service_exception_handler
from .routers import registry_router, discovery_router, workflows_router, health_router
from .dependencies import get_service_discovery


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format=config.log_format
)
logger = logging.getLogger("service_integration")


# Create FastAPI application
app = FastAPI(
    title="Service Integration Service",
    description="""
    Service Integration service for Berrys_AgentsV2.
    
    This service provides functionalities for service discovery, registration,
    and cross-service workflow execution, enabling seamless integration
    between the different services in the system.
    """,
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(registry_router)
app.include_router(discovery_router)
app.include_router(workflows_router)
app.include_router(health_router)


# Add exception handlers
@app.exception_handler(ServiceIntegrationError)
async def handle_service_integration_error(request: Request, exc: ServiceIntegrationError):
    """
    Handle ServiceIntegrationError exceptions.
    
    This converts ServiceIntegrationError to an appropriate HTTP response.
    """
    http_exception = service_exception_handler(exc)
    return JSONResponse(
        status_code=http_exception.status_code,
        content={"detail": http_exception.detail}
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """
    Execute actions when the application starts.
    
    This includes starting the heartbeat monitor for services.
    """
    logger.info("Service Integration service starting up")
    
    # Start the heartbeat monitor
    service_discovery = get_service_discovery()
    await service_discovery.start_heartbeat_monitor()
    
    logger.info("Service Integration service started")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Execute actions when the application shuts down.
    
    This includes stopping the heartbeat monitor.
    """
    logger.info("Service Integration service shutting down")
    
    # Stop the heartbeat monitor
    service_discovery = get_service_discovery()
    await service_discovery.stop_heartbeat_monitor()
    
    logger.info("Service Integration service shut down")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    
    This endpoint provides basic information about the service.
    """
    return {
        "service": "Service Integration",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
    }


# Ready endpoint for Kubernetes
@app.get("/ready", tags=["Health"])
async def ready():
    """
    Readiness check endpoint.
    
    This endpoint is used by Kubernetes to determine if the service is ready to receive traffic.
    """
    return {"status": "ready"}


# Alive endpoint for Kubernetes
@app.get("/alive", tags=["Health"])
async def alive():
    """
    Liveness check endpoint.
    
    This endpoint is used by Kubernetes to determine if the service is alive and working properly.
    """
    return {"status": "alive"}
