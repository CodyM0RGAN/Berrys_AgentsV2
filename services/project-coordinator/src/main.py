"""
Project Coordinator Service - FastAPI Application Entry Point

This module initializes the FastAPI application for the Project Coordinator service,
configures middleware, sets up API routes, and handles startup/shutdown events.
"""

import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid

from .config import Settings, get_settings
from .exceptions import (
    ProjectCoordinatorError, ProjectNotFoundError, InvalidProjectStateError,
    ResourceAllocationError, ArtifactStorageError, ProjectLimitExceededError,
    AnalyticsGenerationError, InvalidTransitionError, DependencyError
)

# Import routers
from .routers import projects, chat

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Project Coordinator Service",
    description="Service for managing project lifecycle, progress tracking, and resource management",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

# Add request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """
    Add a unique request ID to each request.
    
    Args:
        request: FastAPI request
        call_next: Next middleware function
        
    Returns:
        Response with request ID header
    """
    request_id = str(uuid.uuid4())
    logger.info(f"Request {request_id} started: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    response.headers["X-Request-ID"] = request_id
    logger.info(f"Request {request_id} completed: {response.status_code}")
    
    return response

# Exception handlers
@app.exception_handler(ProjectCoordinatorError)
async def project_coordinator_exception_handler(request, exc):
    """Handle general project coordinator errors"""
    logger.error(f"Project coordinator error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_code": exc.error_code, "details": exc.details}
    )

@app.exception_handler(ProjectNotFoundError)
async def project_not_found_exception_handler(request, exc):
    """Handle project not found errors"""
    logger.error(f"Project not found: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_code": exc.error_code, "details": exc.details}
    )

@app.exception_handler(InvalidProjectStateError)
async def invalid_project_state_exception_handler(request, exc):
    """Handle invalid project state errors"""
    logger.error(f"Invalid project state: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_code": exc.error_code, "details": exc.details}
    )

@app.exception_handler(ResourceAllocationError)
async def resource_allocation_exception_handler(request, exc):
    """Handle resource allocation errors"""
    logger.error(f"Resource allocation error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_code": exc.error_code, "details": exc.details}
    )

@app.exception_handler(ArtifactStorageError)
async def artifact_storage_exception_handler(request, exc):
    """Handle artifact storage errors"""
    logger.error(f"Artifact storage error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_code": exc.error_code, "details": exc.details}
    )

@app.exception_handler(ProjectLimitExceededError)
async def project_limit_exceeded_exception_handler(request, exc):
    """Handle project limit exceeded errors"""
    logger.error(f"Project limit exceeded: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_code": exc.error_code, "details": exc.details}
    )

@app.exception_handler(AnalyticsGenerationError)
async def analytics_generation_exception_handler(request, exc):
    """Handle analytics generation errors"""
    logger.error(f"Analytics generation error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_code": exc.error_code, "details": exc.details}
    )

@app.exception_handler(InvalidTransitionError)
async def invalid_transition_exception_handler(request, exc):
    """Handle invalid transition errors"""
    logger.error(f"Invalid transition: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_code": exc.error_code, "details": exc.details}
    )

@app.exception_handler(DependencyError)
async def dependency_exception_handler(request, exc):
    """Handle dependency errors"""
    logger.error(f"Dependency error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_code": exc.error_code, "details": exc.details}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Execute actions on app startup"""
    settings = get_settings()
    logger.info(f"Starting Project Coordinator Service in {settings.environment} mode")
    logger.info(f"Artifact storage path: {settings.artifact_storage_path}")

@app.on_event("shutdown")
async def shutdown_event():
    """Execute actions on app shutdown"""
    logger.info("Shutting down Project Coordinator Service")

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "project-coordinator"}

# Integration with Service Integration service
@app.on_event("startup")
async def register_with_service_integration():
    """Register with Service Integration service on startup"""
    settings = get_settings()
    
    if settings.service_integration_url and settings.self_registration:
        try:
            logger.info("Registering with Service Integration service")
            # Registration logic would go here
            # This would typically involve making an HTTP request to the Service Integration service
            # to register this service and its endpoints
        except Exception as e:
            logger.error(f"Error registering with Service Integration service: {str(e)}")
            # We don't want to fail startup if registration fails, just log the error
