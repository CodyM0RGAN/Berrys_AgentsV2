"""
Service Registry Router.

This module provides API endpoints for service registration and management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from ..models.api import (
    ServiceInfo, ServiceRegistrationRequest, ServiceHeartbeatRequest,
    ServiceType, ServiceStatus
)
from ..services.integration_facade import SystemIntegrationFacade
from ..exceptions import ServiceNotFoundError, ServiceIntegrationError
from ..dependencies import get_integration_facade


router = APIRouter(
    prefix="/registry",
    tags=["Service Registry"],
    responses={404: {"description": "Service not found"}},
)


@router.post("/services", response_model=ServiceInfo, status_code=status.HTTP_201_CREATED)
async def register_service(
    service: ServiceRegistrationRequest,
    facade: SystemIntegrationFacade = Depends(get_integration_facade)
):
    """
    Register a service with the system.
    
    This endpoint allows services to register themselves with the system,
    making them discoverable by other services.
    """
    try:
        return await facade.register_service(ServiceInfo(**service.dict()))
    except ServiceIntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_service(
    service_id: str,
    facade: SystemIntegrationFacade = Depends(get_integration_facade)
):
    """
    Unregister a service from the system.
    
    This endpoint allows services to unregister themselves from the system,
    making them no longer discoverable by other services.
    """
    try:
        result = await facade.unregister_service(service_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service {service_id} not found"
            )
    except ServiceIntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/services/{service_id}/heartbeat", response_model=ServiceInfo)
async def update_service_heartbeat(
    service_id: str,
    heartbeat: Optional[ServiceHeartbeatRequest] = None,
    facade: SystemIntegrationFacade = Depends(get_integration_facade)
):
    """
    Update service heartbeat.
    
    This endpoint allows services to update their heartbeat timestamp,
    indicating that they are still alive and functioning.
    """
    try:
        # If a status is provided, update it
        if heartbeat and heartbeat.status:
            await facade.update_service_status(service_id, heartbeat.status)
        
        # Get service (this will also update the heartbeat)
        service = await facade.get_service(service_id)
        return service
        
    except ServiceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service {service_id} not found"
        )
    except ServiceIntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/services/{service_id}", response_model=ServiceInfo)
async def get_service(
    service_id: str,
    facade: SystemIntegrationFacade = Depends(get_integration_facade)
):
    """
    Get information about a specific service.
    
    This endpoint returns detailed information about a registered service.
    """
    try:
        return await facade.get_service(service_id)
    except ServiceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service {service_id} not found"
        )
    except ServiceIntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/services/{service_id}/status", response_model=ServiceInfo)
async def update_service_status(
    service_id: str,
    status: ServiceStatus,
    facade: SystemIntegrationFacade = Depends(get_integration_facade)
):
    """
    Update the status of a service.
    
    This endpoint allows updating the status of a service,
    e.g., to mark it as offline or degraded.
    """
    try:
        result = await facade.update_service_status(service_id, status)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service {service_id} not found"
            )
        
        # Get updated service
        return await facade.get_service(service_id)
        
    except ServiceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service {service_id} not found"
        )
    except ServiceIntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
