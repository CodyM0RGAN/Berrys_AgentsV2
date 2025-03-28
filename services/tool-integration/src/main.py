"""
Tool Integration Service - FastAPI Application Entry Point

This module initializes the FastAPI application for the Tool Integration service,
configures middleware, sets up API routes, and handles startup/shutdown events.
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import ToolIntegrationSettings, get_settings
from .dependencies import get_db, get_tool_service
from .exceptions import (
    ToolIntegrationError,
    ToolNotFoundError,
    ToolValidationError,
    ToolSchemaValidationError,
    ToolExecutionError,
    ToolExecutionTimeoutError,
    SecurityViolationError,
    ToolDiscoveryError,
    MCPIntegrationError,
    MCPToolNotAvailableError,
    ToolRegistrationError,
    ToolEvaluationError,
)

# Import routers - these will be implemented later
from .routers import tools, discovery, evaluation, integration, execution, mcp

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Tool Integration Service",
    description="Service for discovering, evaluating, integrating, and executing tools for agents",
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
app.include_router(tools.router, prefix="/tools", tags=["tools"])
app.include_router(discovery.router, prefix="/discovery", tags=["discovery"])
app.include_router(evaluation.router, prefix="/evaluation", tags=["evaluation"])
app.include_router(integration.router, prefix="/integration", tags=["integration"])
app.include_router(execution.router, prefix="/execution", tags=["execution"])
app.include_router(mcp.router, prefix="/mcp", tags=["mcp"])

# Exception handlers
@app.exception_handler(ToolIntegrationError)
async def tool_integration_exception_handler(request, exc):
    """Handle general tool integration errors"""
    logger.error(f"Tool integration error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc), "error_code": exc.error_code},
    )

@app.exception_handler(ToolNotFoundError)
async def tool_not_found_exception_handler(request, exc):
    """Handle tool not found errors"""
    logger.error(f"Tool not found: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc), "error_code": exc.error_code},
    )

@app.exception_handler(ToolValidationError)
async def tool_validation_exception_handler(request, exc):
    """Handle tool validation errors"""
    logger.error(f"Tool validation error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": str(exc), 
            "error_code": exc.error_code,
            "validation_errors": exc.details.get("validation_errors", [])
        },
    )

@app.exception_handler(ToolSchemaValidationError)
async def schema_validation_exception_handler(request, exc):
    """Handle schema validation errors"""
    logger.error(f"Schema validation error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": str(exc), 
            "error_code": exc.error_code,
            "validation_errors": exc.details.get("validation_errors", [])
        },
    )

@app.exception_handler(ToolExecutionError)
async def tool_execution_exception_handler(request, exc):
    """Handle tool execution errors"""
    logger.error(f"Tool execution error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc), "error_code": exc.error_code},
    )

@app.exception_handler(ToolExecutionTimeoutError)
async def execution_timeout_exception_handler(request, exc):
    """Handle execution timeout errors"""
    logger.error(f"Execution timeout: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": str(exc), 
            "error_code": exc.error_code,
            "timeout_seconds": exc.details.get("timeout_seconds"),
            "tool_id": exc.details.get("tool_id")
        },
    )

@app.exception_handler(SecurityViolationError)
async def security_violation_exception_handler(request, exc):
    """Handle security violation errors"""
    logger.error(f"Security violation: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": str(exc), 
            "error_code": exc.error_code,
            "violation_type": exc.details.get("violation_type")
        },
    )

@app.exception_handler(ToolDiscoveryError)
async def tool_discovery_exception_handler(request, exc):
    """Handle tool discovery errors"""
    logger.error(f"Tool discovery error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc), "error_code": exc.error_code},
    )

@app.exception_handler(MCPIntegrationError)
async def mcp_integration_exception_handler(request, exc):
    """Handle MCP integration errors"""
    logger.error(f"MCP integration error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": str(exc), 
            "error_code": exc.error_code,
            "server_name": exc.details.get("server_name")
        },
    )

@app.exception_handler(MCPToolNotAvailableError)
async def mcp_tool_not_available_exception_handler(request, exc):
    """Handle MCP tool not available errors"""
    logger.error(f"MCP tool not available: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": str(exc), 
            "error_code": exc.error_code,
            "server_name": exc.details.get("server_name"),
            "tool_name": exc.details.get("tool_name")
        },
    )

@app.exception_handler(ToolRegistrationError)
async def tool_registration_exception_handler(request, exc):
    """Handle tool registration errors"""
    logger.error(f"Tool registration error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc), "error_code": exc.error_code},
    )

@app.exception_handler(ToolEvaluationError)
async def tool_evaluation_exception_handler(request, exc):
    """Handle tool evaluation errors"""
    logger.error(f"Tool evaluation error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": str(exc), 
            "error_code": exc.error_code,
            "tool_id": exc.details.get("tool_id"),
            "evaluation_type": exc.details.get("evaluation_type")
        },
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
    settings = get_settings()
    logger.info(f"Starting Tool Integration Service in {settings.environment} mode")

@app.on_event("shutdown")
async def shutdown_event():
    """Execute actions on app shutdown"""
    logger.info("Shutting down Tool Integration Service")

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "tool-integration"}
