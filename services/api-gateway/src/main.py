import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import uvicorn

# Import shared modules
from shared.utils.src.auth import create_access_token, get_current_user, get_password_hash, verify_password
from shared.utils.src.messaging import init_messaging, close_messaging, get_event_bus, get_command_bus

# Import monitoring modules
from shared.utils.src.monitoring.middleware.fastapi import setup_monitoring
from shared.utils.src.monitoring.logging import get_logger, configure_logging
from shared.utils.src.monitoring.metrics import configure_metrics, MetricsBackend
from shared.utils.src.monitoring.health import register_health_check, check_health

# Import local modules
from .database import get_db, check_db_connection, init_db

# Import routers
from .routers import projects
# TODO: Uncomment these imports when the routers are implemented
# from .routers import agents, tasks, tools, users, models, audit

# Setup monitoring
configure_logging(
    level="INFO",
    json_format=True,
    log_to_console=True,
    service_name="api-gateway",
)

# Configure metrics
configure_metrics(
    backend=MetricsBackend.PROMETHEUS,
    prefix="berrys_agents",
    default_labels={"service": "api-gateway"},
    http_port=8001,  # Use a different port to avoid conflict with the API server
)

# Create logger
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Berry's Agents API",
    description="API Gateway for Project-based Multi-Agent System Framework",
    version="1.0.0",
)

# Set up monitoring middleware
setup_monitoring(app, service_name="api-gateway")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

# Include routers
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
# TODO: Uncomment these lines when the routers are implemented
# app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
# app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
# app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
# app.include_router(users.router, prefix="/api/users", tags=["users"])
# app.include_router(models.router, prefix="/api/models", tags=["models"])
# app.include_router(audit.router, prefix="/api/audit", tags=["audit"])


@app.on_event("startup")
async def startup():
    """
    Initialize services on startup.
    """
    logger.info("Starting API Gateway service")
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
        
    # Initialize messaging
    try:
        await init_messaging(service_name="api-gateway")
        logger.info("Messaging initialized")
    except Exception as e:
        logger.error(f"Failed to initialize messaging: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """
    Clean up resources on shutdown.
    """
    logger.info("Shutting down API Gateway service")
    
    # Close messaging
    try:
        await close_messaging()
        logger.info("Messaging closed")
    except Exception as e:
        logger.error(f"Error closing messaging: {str(e)}")


# Register health checks
@register_health_check("database")
async def check_database():
    """Check if database is accessible."""
    is_healthy = await check_db_connection()
    return is_healthy, "Database connection is healthy" if is_healthy else "Database connection failed"

@register_health_check("messaging")
def check_messaging():
    """Check if messaging system is accessible."""
    is_healthy = get_event_bus() is not None and get_command_bus() is not None
    return is_healthy, "Messaging system is healthy" if is_healthy else "Messaging system is not available"

@app.get("/api/health")
def api_health_check():
    """
    Health check endpoint (API path version).
    Returns a simple health check response.
    """
    # Create a simple health check response
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.post("/api/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and return JWT token.
    """
    # This is a placeholder implementation
    # In a real implementation, we would fetch the user from the database
    
    # For demo purposes, accept admin/admin
    if form_data.username == "admin" and form_data.password == "admin":
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": form_data.username, "is_admin": True},
            expires_delta=access_token_expires,
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
    # Authentication failed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
