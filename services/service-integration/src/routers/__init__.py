"""
API routers for the Service Integration service.

This package contains FastAPI routers that provide the API endpoints for
the Service Integration service.
"""
from .registry import router as registry_router
from .discovery import router as discovery_router
from .workflows import router as workflows_router
from .health import router as health_router

__all__ = [
    "registry_router",
    "discovery_router",
    "workflows_router",
    "health_router",
]
