"""
Service Discovery Router.

This module provides API endpoints for service discovery.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from ..models.api import (
    ServiceInfo, ServiceDiscoveryRequest, ServiceDiscoveryResponse, 
    ServiceType, ServiceStatus
)
from ..services.integration_facade import SystemIntegrationFacade
from ..exceptions import ServiceNotFoundError, ServiceIntegrationError
from ..dependencies import get_integration_facade


router = APIRouter(
    prefix="/discovery",
    tags=["Service Discovery"],
    responses={500: {"description": "Service Discovery Error"}},
)


@router.get("/services", response_model=ServiceDiscoveryResponse)
async def find_services(
    service_type: Optional[ServiceType] = Query(None, description="Type of service to find"),
    include_offline: bool = Query(False, description="Whether to include offline services"),
    facade: SystemIntegrationFacade = Depends(get_integration_facade)
):
    """
    Find services matching the specified criteria.
    
    This endpoint allows discovering services based on type and status.
    """
    try:
        services = await facade.find_services(
            service_type=service_type,
            include_offline=include_offline
        )
        return ServiceDiscoveryResponse(services=services)
    except ServiceIntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/services/search", response_model=ServiceDiscoveryResponse)
async def search_services(
    search_request: ServiceDiscoveryRequest,
    facade: SystemIntegrationFacade = Depends(get_integration_facade)
):
    """
    Search for services with more complex criteria.
    
    This endpoint provides a more flexible search interface for services.
    """
    try:
        services = await facade.find_services(
            service_type=search_request.service_type,
            include_offline=search_request.include_offline
        )
        return ServiceDiscoveryResponse(services=services)
    except ServiceIntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/services/type/{service_type}", response_model=ServiceInfo)
async def get_service_by_type(
    service_type: ServiceType,
    facade: SystemIntegrationFacade = Depends(get_integration_facade)
):
    """
    Get a service by type.
    
    This endpoint returns a single service of the specified type.
    If multiple services of the type are available, one is selected
    (in a production system, this would implement load balancing).
    """
    try:
        # This function is provided by the service discovery layer
        service = await facade.service_discovery.get_service_by_type(service_type)
        return service
    except ServiceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No service of type {service_type} found"
        )
    except ServiceIntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/health/{service_id}", response_model=ServiceStatus)
async def check_service_health(
    service_id: str,
    facade: SystemIntegrationFacade = Depends(get_integration_facade)
):
    """
    Check the health of a service.
    
    This endpoint checks if a service is healthy based on its heartbeat.
    """
    try:
        status = await facade.service_discovery.check_service_health(service_id)
        return status
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
