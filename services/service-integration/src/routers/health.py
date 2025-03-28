"""
Health Check Router.

This module provides API endpoints for monitoring system health.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from ..models.api import SystemHealthResponse
from ..services.integration_facade import SystemIntegrationFacade
from ..exceptions import ServiceIntegrationError
from ..dependencies import get_integration_facade


router = APIRouter(
    prefix="/health",
    tags=["Health Checks"],
    responses={500: {"description": "Health check error"}},
)


@router.get("/system", response_model=SystemHealthResponse)
async def get_system_health(
    facade: SystemIntegrationFacade = Depends(get_integration_facade)
):
    """
    Get the overall health of the system.
    
    This endpoint returns the health status of all registered services
    and circuit breaker states.
    """
    try:
        return await facade.get_system_health()
    except ServiceIntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/ready")
async def readiness_check():
    """
    Readiness check for the service.
    
    This endpoint returns 200 OK if the service is ready to accept requests.
    It is used by orchestration platforms (e.g., Kubernetes) to determine
    if the service is ready to receive traffic.
    """
    return {"status": "ready"}


@router.get("/alive")
async def liveness_check():
    """
    Liveness check for the service.
    
    This endpoint returns 200 OK if the service is alive.
    It is used by orchestration platforms (e.g., Kubernetes) to determine
    if the service is still running or needs to be restarted.
    """
    return {"status": "alive"}


@router.get("/circuit-breakers")
async def get_circuit_breaker_status(
    facade: SystemIntegrationFacade = Depends(get_integration_facade)
):
    """
    Get the status of all circuit breakers.
    
    This endpoint returns detailed information about all circuit breakers
    in the system, including their current state, failure count, and configuration.
    """
    try:
        health = await facade.get_system_health()
        return {"circuit_breakers": health.circuit_breaker_statuses}
    except ServiceIntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
