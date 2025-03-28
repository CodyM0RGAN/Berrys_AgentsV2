"""
System Integration Facade.

This module implements the Facade pattern to provide a simplified interface
for system integration functionality.
"""
import logging
import uuid
from typing import Dict, Any, Optional, List, Callable, Awaitable
from datetime import datetime

from ..models.api import (
    WorkflowRequest, WorkflowResponse, WorkflowType, WorkflowStatus,
    ServiceInfo, ServiceType, ServiceStatus, SystemHealthResponse
)
from ..exceptions import (
    ServiceIntegrationError, ServiceNotFoundError, WorkflowError,
    UnknownRequestTypeError
)
from .discovery.service import ServiceDiscovery
from .communication.mediator import RequestMediator
from .communication.client import ServiceClient
from .communication.circuit_breaker import CircuitBreakerRegistry


class SystemIntegrationFacade:
    """
    System Integration Facade.
    
    This class provides a simplified interface to the system integration
    functionality, coordinating service discovery, communication, and workflows.
    """
    
    def __init__(
        self,
        service_discovery: ServiceDiscovery,
        request_mediator: RequestMediator,
        service_client: ServiceClient,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the system integration facade.
        
        Args:
            service_discovery: Service discovery instance
            request_mediator: Request mediator instance
            service_client: Service client instance
            logger: Logger instance (optional)
        """
        self.service_discovery = service_discovery
        self.request_mediator = request_mediator
        self.service_client = service_client
        self.logger = logger or logging.getLogger("integration_facade")
    
    async def execute_workflow(self, workflow_request: WorkflowRequest) -> WorkflowResponse:
        """
        Execute a cross-service workflow.
        
        Args:
            workflow_request: Workflow request data
            
        Returns:
            Workflow response
            
        Raises:
            WorkflowError: If the workflow execution fails
            UnknownRequestTypeError: If the workflow type is not supported
        """
        workflow_id = workflow_request.workflow_id or str(uuid.uuid4())
        start_time = datetime.now()
        
        self.logger.info(f"Starting workflow {workflow_request.workflow_type} with ID {workflow_id}")
        
        try:
            # Route to appropriate workflow handler
            request_type = f"workflow.{workflow_request.workflow_type}"
            result = await self.request_mediator.send(request_type, workflow_request)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Create successful response
            response = WorkflowResponse(
                workflow_id=workflow_id,
                status=WorkflowStatus.COMPLETED,
                execution_time=execution_time,
                result=result,
                errors=[]
            )
            
            self.logger.info(f"Workflow {workflow_request.workflow_type} completed successfully in {execution_time:.2f}s")
            return response
            
        except UnknownRequestTypeError as ex:
            self.logger.error(f"Unknown workflow type: {workflow_request.workflow_type}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Create error response
            response = WorkflowResponse(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                execution_time=execution_time,
                result=None,
                errors=[f"Unknown workflow type: {workflow_request.workflow_type}"]
            )
            
            raise WorkflowError(f"Unknown workflow type: {workflow_request.workflow_type}") from ex
            
        except Exception as ex:
            self.logger.exception(f"Error executing workflow {workflow_request.workflow_type}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Create error response
            response = WorkflowResponse(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                execution_time=execution_time,
                result=None,
                errors=[str(ex)]
            )
            
            raise WorkflowError(f"Error executing workflow: {str(ex)}") from ex
    
    async def register_service(self, service: ServiceInfo) -> ServiceInfo:
        """
        Register a service with the system.
        
        Args:
            service: Service information
            
        Returns:
            Updated service information
            
        Raises:
            ServiceIntegrationError: If registration fails
        """
        try:
            # Register with discovery service
            service = await self.service_discovery.register_service(service)
            
            # Notify other systems (broadcast event)
            await self.request_mediator.broadcast(
                "event.service_registered",
                {"service_id": service.service_id, "service": service}
            )
            
            self.logger.info(f"Service {service.name} registered with ID {service.service_id}")
            return service
            
        except Exception as ex:
            self.logger.exception(f"Error registering service {service.name}")
            raise ServiceIntegrationError(f"Failed to register service: {str(ex)}") from ex
    
    async def unregister_service(self, service_id: str) -> bool:
        """
        Unregister a service from the system.
        
        Args:
            service_id: ID of the service to unregister
            
        Returns:
            True if unregistered, False if not found
            
        Raises:
            ServiceIntegrationError: If unregistration fails
        """
        try:
            # Get service details before unregistering
            service = await self.service_discovery.get_service(service_id)
            
            # Unregister from discovery service
            result = await self.service_discovery.unregister_service(service_id)
            
            if result:
                # Notify other systems (broadcast event)
                await self.request_mediator.broadcast(
                    "event.service_unregistered",
                    {"service_id": service_id, "service": service}
                )
                
                self.logger.info(f"Service {service_id} unregistered")
            
            return result
            
        except ServiceNotFoundError:
            return False
        except Exception as ex:
            self.logger.exception(f"Error unregistering service {service_id}")
            raise ServiceIntegrationError(f"Failed to unregister service: {str(ex)}") from ex
    
    async def get_service(self, service_id: str) -> ServiceInfo:
        """
        Get information about a specific service.
        
        Args:
            service_id: ID of the service to get
            
        Returns:
            Service information
            
        Raises:
            ServiceNotFoundError: If the service is not found
            ServiceIntegrationError: If retrieval fails
        """
        try:
            return await self.service_discovery.get_service(service_id)
        except ServiceNotFoundError:
            raise
        except Exception as ex:
            self.logger.exception(f"Error getting service {service_id}")
            raise ServiceIntegrationError(f"Failed to get service: {str(ex)}") from ex
    
    async def find_services(
        self, 
        service_type: Optional[ServiceType] = None,
        include_offline: bool = False
    ) -> List[ServiceInfo]:
        """
        Find services matching the specified criteria.
        
        Args:
            service_type: Type of services to find (optional)
            include_offline: Whether to include offline services
            
        Returns:
            List of services matching the criteria
            
        Raises:
            ServiceIntegrationError: If the search fails
        """
        try:
            return await self.service_discovery.find_services(
                service_type=service_type,
                include_offline=include_offline
            )
        except Exception as ex:
            self.logger.exception("Error finding services")
            raise ServiceIntegrationError(f"Failed to find services: {str(ex)}") from ex
    
    async def update_service_status(self, service_id: str, status: ServiceStatus) -> bool:
        """
        Update the status of a service.
        
        Args:
            service_id: ID of the service to update
            status: New status
            
        Returns:
            True if updated
            
        Raises:
            ServiceNotFoundError: If the service is not found
            ServiceIntegrationError: If the update fails
        """
        try:
            result = await self.service_discovery.update_service_status(service_id, status)
            
            if result:
                # Get updated service details
                service = await self.service_discovery.get_service(service_id)
                
                # Notify other systems (broadcast event)
                await self.request_mediator.broadcast(
                    "event.service_status_changed",
                    {"service_id": service_id, "status": status, "service": service}
                )
                
                self.logger.info(f"Service {service_id} status updated to {status}")
            
            return result
            
        except ServiceNotFoundError:
            raise
        except Exception as ex:
            self.logger.exception(f"Error updating service status for {service_id}")
            raise ServiceIntegrationError(f"Failed to update service status: {str(ex)}") from ex
    
    async def get_system_health(self) -> SystemHealthResponse:
        """
        Get the overall health of the system.
        
        Returns:
            System health response
            
        Raises:
            ServiceIntegrationError: If health check fails
        """
        start_time = datetime.now()
        
        try:
            # Get all services
            services = await self.service_discovery.find_services(include_offline=True)
            
            # Check circuit breakers
            circuit_breakers = CircuitBreakerRegistry.get_all_circuit_breakers()
            
            # Prepare response
            service_statuses = {service.service_id: service.status for service in services}
            circuit_breaker_statuses = {
                name: {
                    "service_id": name,
                    "state": cb.state.value,
                    "failure_count": cb.failure_count,
                    "last_failure_time": cb.last_failure_time,
                    "half_open_call_count": cb.half_open_call_count
                }
                for name, cb in circuit_breakers.items()
            }
            
            # Determine overall status
            if all(status == ServiceStatus.ONLINE for status in service_statuses.values()):
                overall_status = "HEALTHY"
            elif any(status == ServiceStatus.OFFLINE for status in service_statuses.values()):
                overall_status = "DEGRADED"
            else:
                overall_status = "UNHEALTHY"
            
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return SystemHealthResponse(
                status=overall_status,
                service_statuses=service_statuses,
                circuit_breaker_statuses=circuit_breaker_statuses,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as ex:
            self.logger.exception("Error checking system health")
            raise ServiceIntegrationError(f"Failed to get system health: {str(ex)}") from ex
