import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn

from .config import config, get_settings
from .database import init_db, close_db_connection, check_db_connection
from shared.utils.src.messaging import init_messaging, close_messaging
from .exceptions import ServiceError
from .routers import (
    agents_router,
    templates_router,
    lifecycle_router,
    state_router,
    communications_router,
    human_interactions_router,
)
from .routers.executions import router as executions_router
from .routers.enhanced_communication import router as enhanced_communication_router
from .routers.metrics_router import router as metrics_router
from .routers.alerts_router import router as alerts_router
from shared.utils.src.feature_flags import is_feature_enabled

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting Agent Orchestrator Service in {config.environment} mode")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Initialize messaging
        await init_messaging(service_name="agent-orchestrator")
        logger.info("Messaging initialized")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Agent Orchestrator Service")
    
    try:
        # Close messaging connections
        await close_messaging()
        logger.info("Messaging connections closed")
        
        # Close database connections
        await close_db_connection()
        logger.info("Database connections closed")
    
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Create FastAPI app
app = FastAPI(
    title="Agent Orchestrator Service",
    description="Service for managing agent lifecycle and orchestration",
    version="0.1.0",
    lifespan=lifespan,
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
app.include_router(agents_router, prefix="/api/agents", tags=["agents"])
app.include_router(templates_router, prefix="/api/templates", tags=["templates"])
app.include_router(lifecycle_router, prefix="/api/agents", tags=["lifecycle"])
app.include_router(state_router, prefix="/api/agents", tags=["state"])
app.include_router(communications_router, prefix="/api/agents", tags=["communications"])
app.include_router(human_interactions_router, prefix="/api/agents", tags=["human-interactions"])
app.include_router(executions_router, prefix="/api/executions", tags=["executions"])
app.include_router(enhanced_communication_router, prefix="/api", tags=["enhanced-communication"])
app.include_router(metrics_router, prefix="/api", tags=["metrics"])
app.include_router(alerts_router, prefix="/api", tags=["alerts"])


# Exception handlers
@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    """
    Handle service-specific errors.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code, **exc.details},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc), "code": "validation_error"},
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    """
    # Check database connection
    db_healthy = await check_db_connection()
    
    # Overall health status
    healthy = db_healthy
    
    response = {
        "status": "healthy" if healthy else "unhealthy",
        "service": "agent-orchestrator",
        "components": {
            "database": "healthy" if db_healthy else "unhealthy",
        }
    }
    
    if is_feature_enabled("include_service_description"):
        response["description"] = "Service for managing agent lifecycle and orchestration"
    
    return response



# Run the application
if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.is_development(),
        log_level="info",
    )
