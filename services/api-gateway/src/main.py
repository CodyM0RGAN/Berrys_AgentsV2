import os
import sys
import asyncio
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import logging
import uvicorn

# Add parent directory to path to import shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import shared modules
from shared.utils.src.logging import setup_logging, get_logger
from shared.utils.src.database import init_db, get_db, check_db_connection
from shared.utils.src.auth import create_access_token, get_current_user, get_password_hash, verify_password
from shared.utils.src.messaging import init_messaging, close_messaging, get_event_bus, get_command_bus

# Import routers
from .routers import projects, agents, tasks, tools, users, models, audit

# Setup logging
setup_logging(service_name="api-gateway")
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MAS Framework API",
    description="API Gateway for Project-based Multi-Agent System Framework",
    version="1.0.0",
)

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
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])


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


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    """
    # Check database connection
    db_healthy = await check_db_connection()
    
    # Check messaging connection
    messaging_healthy = get_event_bus() is not None and get_command_bus() is not None
    
    # Overall health status
    healthy = db_healthy and messaging_healthy
    
    return {
        "status": "healthy" if healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": {
            "database": "healthy" if db_healthy else "unhealthy",
            "messaging": "healthy" if messaging_healthy else "unhealthy",
        },
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
