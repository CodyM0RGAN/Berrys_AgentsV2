import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sentry_sdk
from prometheus_client import make_asgi_app
from datetime import datetime

# Import shared modules
from .database import init_db, close_db_connection, check_db_connection
from shared.utils.src.messaging import init_messaging, close_messaging

# Import local modules
from .config import ModelOrchestrationConfig, config, get_settings
from .dependencies import get_model_service
from .exceptions import ModelServiceError, ProviderError
from .routers import models, performance

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("model-orchestration")

# Sentry integration (optional)
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=0.1,
        environment=os.getenv("ENVIRONMENT", "development"),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting Model Orchestration Service in {config.environment} mode")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Initialize messaging
        await init_messaging(service_name="model-orchestration")
        logger.info("Messaging initialized")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Model Orchestration Service")
    
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
    title="Model Orchestration Service",
    description="Service for orchestrating AI model requests across different providers",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create metrics endpoint for monitoring
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(performance.router, prefix="/api/performance", tags=["performance"])


@app.exception_handler(ModelServiceError)
async def model_service_exception_handler(request: Request, exc: ModelServiceError):
    """
    Handle ModelServiceError exceptions.
    """
    logger.error(f"ModelServiceError: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc), "code": exc.code},
    )


@app.exception_handler(ProviderError)
async def provider_exception_handler(request: Request, exc: ProviderError):
    """
    Handle ProviderError exceptions.
    """
    logger.error(f"ProviderError: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": str(exc), "code": exc.code, "provider": exc.provider},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    # Check database connection
    db_healthy = await check_db_connection()
    
    # Check model providers
    # This will be implemented in a more comprehensive way
    providers_healthy = True
    
    # Overall health status
    healthy = db_healthy and providers_healthy
    
    return {
        "status": "healthy" if healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": {
            "database": "healthy" if db_healthy else "unhealthy",
            "providers": "healthy" if providers_healthy else "unhealthy",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
