"""
Planning System Service - FastAPI Application Entry Point

This module initializes the FastAPI application for the Planning System service,
configures middleware, sets up API routes, and handles startup/shutdown events.
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import config, get_settings
from .dependencies import get_db, get_planning_service
from .exceptions import (
    PlanningSystemError,
    PlanNotFoundError,
    TaskNotFoundError,
    InvalidDependencyError,
    ResourceNotFoundError,
    ResourceAllocationError,
    ForecastingError,
    TemplateNotFoundError,
    TemplateValidationError,
    ScenarioNotFoundError
)

# Import routers
from .routers import (
    plans, 
    tasks, 
    dependencies, 
    forecasts, 
    optimization, 
    resources, 
    task_templates, 
    dependency_types, 
    what_if_analysis
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Planning System Service",
    description="Service for managing project plans, task dependencies, and timeline forecasting",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(plans, prefix="/plans", tags=["plans"])
app.include_router(tasks, prefix="/tasks", tags=["tasks"])
app.include_router(dependencies, prefix="/dependencies", tags=["dependencies"])
app.include_router(forecasts, prefix="/forecasts", tags=["forecasts"])
app.include_router(optimization, prefix="/optimization", tags=["optimization"])
app.include_router(resources, prefix="/resources", tags=["resources"])
app.include_router(task_templates, tags=["task-templates"])
app.include_router(dependency_types, tags=["dependency-types"])
app.include_router(what_if_analysis, tags=["what-if-analysis"])

# Exception handlers
@app.exception_handler(PlanningSystemError)
async def planning_system_exception_handler(request, exc):
    """Handle general planning system errors"""
    logger.error(f"Planning system error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc), "error_code": exc.error_code},
    )

@app.exception_handler(PlanNotFoundError)
async def plan_not_found_exception_handler(request, exc):
    """Handle plan not found errors"""
    logger.error(f"Plan not found: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc), "error_code": exc.error_code},
    )

@app.exception_handler(TaskNotFoundError)
async def task_not_found_exception_handler(request, exc):
    """Handle task not found errors"""
    logger.error(f"Task not found: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc), "error_code": exc.error_code},
    )

@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_exception_handler(request, exc):
    """Handle resource not found errors"""
    logger.error(f"Resource not found: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc), "error_code": exc.error_code},
    )

@app.exception_handler(InvalidDependencyError)
async def invalid_dependency_exception_handler(request, exc):
    """Handle invalid dependency errors"""
    logger.error(f"Invalid dependency: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc), "error_code": exc.error_code},
    )

@app.exception_handler(ResourceAllocationError)
async def resource_allocation_exception_handler(request, exc):
    """Handle resource allocation errors"""
    logger.error(f"Resource allocation error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc), "error_code": exc.error_code},
    )

@app.exception_handler(ForecastingError)
async def forecasting_exception_handler(request, exc):
    """Handle forecasting errors"""
    logger.error(f"Forecasting error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc), "error_code": exc.error_code},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc)},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Execute actions on app startup"""
    logger.info(f"Starting Planning System Service in {config.environment} mode")

@app.on_event("shutdown")
async def shutdown_event():
    """Execute actions on app shutdown"""
    logger.info("Shutting down Planning System Service")

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
