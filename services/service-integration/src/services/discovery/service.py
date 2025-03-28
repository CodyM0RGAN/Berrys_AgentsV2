"""
Service Discovery service.

This service provides high-level functionality for service discovery,
abstracting the underlying discovery mechanism details.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ....models.api import ServiceInfo, ServiceType, ServiceStatus
from ....exceptions import ServiceNotFoundError, ServiceDiscoveryError
from .factory import ServiceDiscoveryFactory


class ServiceDiscovery:
    """
    Service Discovery service.
    
    This service provides high-level functionality for service discovery,
    including caching to improve performance and reduce load on the discovery backend.
    """
    
    def __init__(self, cache_ttl: int = 30):
        """
        Initialize the service discovery service.
        
        Args:
            cache_ttl: Time-to-live for cached service information in seconds
        """
        self.logger = logging.getLogger("service_discovery")
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, tuple[ServiceInfo, datetime]] = {}
        self.cache_all: Optional[tuple[List[ServiceInfo], datetime]] = None
        self.cache_by_type: Dict[ServiceType, tuple[List[ServiceInfo], datetime]] = {}
        self.heartbeat_task = None
    
    def get_strategy(self):
        """Get the underlying discovery strategy."""
        return ServiceDiscoveryFactory.get_strategy()
    
    async def register_service(self, service: ServiceInfo) -> ServiceInfo:
        """
        Register a service.
        
        Args:
            service: Service information to register
            
        Returns:
            The registered service information
            
        Raises:
            ServiceDiscoveryError: If registration fails
        """
        try:
            strategy = self.get_strategy()
            result = await strategy.register_service(service)
            
            # Update cache
            self.cache[service.service_id] = (result, datetime.now())
            self.cache_all = None  # Invalidate cache
            if service.type in self.cache_by_type:
                self.cache_by_type[service.type] = None  # Invalidate cache
                
            self.logger.info(f"Service {service.name} registered with ID {service.service_id}")
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to register service: {str(e)}")
            raise ServiceDiscoveryError(f"Failed to register service: {str(e)}")
    
    async def unregister_service(self, service_id: str) -> bool:
        """
        Unregister a service.
        
        Args:
            service_id: ID of the service to unregister
            
        Returns:
            True if unregistered, False if not found
            
        Raises:
            ServiceDiscoveryError: If unregistration fails
        """
        try:
            strategy = self.get_strategy()
            result = await strategy.unregister_service(service_id)
            
            # Update cache
            if service_id in self.cache:
                service_type = self.cache[service_id][0].type
                del self.cache[service_id]
                
                self.cache_all = None  # Invalidate cache
                if service_type in self.cache_by_type:
                    self.cache_by_type[service_type] = None  # Invalidate cache
            
            self.logger.info(f"Service {service_id} unregistered")
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to unregister service: {str(e)}")
            raise ServiceDiscoveryError(f"Failed to unregister service: {str(e)}")
    
    async def get_service(self, service_id: str) -> ServiceInfo:
        """
        Get information about a specific service.
        
        Args:
            service_id: ID of the service to get
            
        Returns:
            Service information
            
        Raises:
            ServiceNotFoundError: If the service is not found
            ServiceDiscoveryError: If retrieval fails
        """
        # Check cache first
        if service_id in self.cache:
            service, timestamp = self.cache[service_id]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return service
        
        # Get from discovery
        try:
            strategy = self.get_strategy()
            service = await strategy.get_service(service_id)
            
            if not service:
                raise ServiceNotFoundError(f"Service {service_id} not found")
            
            # Update cache
            self.cache[service_id] = (service, datetime.now())
            return service
        
        except ServiceNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get service {service_id}: {str(e)}")
            raise ServiceDiscoveryError(f"Failed to get service: {str(e)}")
    
    async def get_service_by_type(self, service_type: ServiceType) -> ServiceInfo:
        """
        Get a service of the specified type.
        
        If multiple services of the type are available, the first one is returned.
        In a production system, this would likely implement load balancing.
        
        Args:
            service_type: Type of service to get
            
        Returns:
            Service information
            
        Raises:
            ServiceNotFoundError: If no service of the type is found
            ServiceDiscoveryError: If retrieval fails
        """
        services = await self.find_services(service_type=service_type)
        
        if not services:
            raise ServiceNotFoundError(f"No service of type {service_type} found")
        
        # In a production system, this could implement load balancing
        return services[0]
    
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
            ServiceDiscoveryError: If search fails
        """
        # Check cache first
        cache_key = (service_type, include_offline)
        if service_type:
            if service_type in self.cache_by_type:
                services, timestamp = self.cache_by_type[service_type]
                if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                    # Filter by status if needed
                    if not include_offline:
                        return [s for s in services if s.status == ServiceStatus.ONLINE]
                    return services
        elif self.cache_all:
            services, timestamp = self.cache_all
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                # Filter by status if needed
                if not include_offline:
                    return [s for s in services if s.status == ServiceStatus.ONLINE]
                return services
        
        # Get from discovery
        try:
            strategy = self.get_strategy()
            services = await strategy.find_services(service_type=service_type, include_offline=include_offline)
            
            # Update cache
            if service_type:
                self.cache_by_type[service_type] = (services, datetime.now())
            else:
                self.cache_all = (services, datetime.now())
                
            # Update individual service cache
            for service in services:
                self.cache[service.service_id] = (service, datetime.now())
                
            return services
        
        except Exception as e:
            self.logger.error(f"Failed to find services: {str(e)}")
            raise ServiceDiscoveryError(f"Failed to find services: {str(e)}")
    
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
            ServiceDiscoveryError: If update fails
        """
        try:
            strategy = self.get_strategy()
            result = await strategy.update_service_status(service_id, status)
            
            # Update cache
            if service_id in self.cache:
                service, _ = self.cache[service_id]
                service.status = status
                self.cache[service_id] = (service, datetime.now())
                
            # Invalidate cache
            self.cache_all = None
            if service_id in self.cache:
                service_type = self.cache[service_id][0].type
                if service_type in self.cache_by_type:
                    self.cache_by_type[service_type] = None
            
            self.logger.info(f"Service {service_id} status updated to {status}")
            return result
        
        except ServiceNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update service status: {str(e)}")
            raise ServiceDiscoveryError(f"Failed to update service status: {str(e)}")
    
    async def update_heartbeat(self, service_id: str) -> bool:
        """
        Update the heartbeat timestamp for a service.
        
        Args:
            service_id: ID of the service to update
            
        Returns:
            True if updated
            
        Raises:
            ServiceNotFoundError: If the service is not found
            ServiceDiscoveryError: If update fails
        """
        try:
            strategy = self.get_strategy()
            result = await strategy.update_heartbeat(service_id)
            
            # Update cache if service is known
            if service_id in self.cache:
                service, _ = self.cache[service_id]
                service.last_heartbeat = datetime.now()
                service.status = ServiceStatus.ONLINE
                self.cache[service_id] = (service, datetime.now())
            
            self.logger.debug(f"Service {service_id} heartbeat updated")
            return result
        
        except ServiceNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update heartbeat: {str(e)}")
            raise ServiceDiscoveryError(f"Failed to update heartbeat: {str(e)}")
    
    async def check_service_health(self, service_id: str) -> ServiceStatus:
        """
        Check if a service is healthy based on heartbeat.
        
        Args:
            service_id: ID of the service to check
            
        Returns:
            Service status
            
        Raises:
            ServiceNotFoundError: If the service is not found
            ServiceDiscoveryError: If health check fails
        """
        try:
            service = await self.get_service(service_id)
            
            # Calculate time since last heartbeat
            time_since_heartbeat = datetime.now() - service.last_heartbeat
            max_heartbeat_age = timedelta(seconds=self.cache_ttl * 2)
            
            # Update status based on heartbeat age
            if time_since_heartbeat > max_heartbeat_age:
                service.status = ServiceStatus.OFFLINE
                
                # Update cache
                if service_id in self.cache:
                    self.cache[service_id] = (service, datetime.now())
                
                # Tell the discovery mechanism
                strategy = self.get_strategy()
                await strategy.update_service_status(service_id, ServiceStatus.OFFLINE)
            
            return service.status
        
        except ServiceNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to check service health: {str(e)}")
            raise ServiceDiscoveryError(f"Failed to check service health: {str(e)}")
    
    async def start_heartbeat_monitor(self, interval: int = 30) -> None:
        """
        Start the heartbeat monitor task.
        
        The monitor periodically checks the health of all registered services
        and updates their status.
        
        Args:
            interval: Check interval in seconds
        """
        if self.heartbeat_task is not None:
            self.logger.warning("Heartbeat monitor is already running")
            return
        
        async def monitor_heartbeats():
            self.logger.info("Heartbeat monitor started")
            while True:
                try:
                    # Get all services
                    services = await self.find_services(include_offline=True)
                    
                    # Check health of each service
                    for service in services:
                        try:
                            await self.check_service_health(service.service_id)
                        except Exception as e:
                            self.logger.error(f"Error checking health of service {service.service_id}: {str(e)}")
                    
                except Exception as e:
                    self.logger.error(f"Error in heartbeat monitor: {str(e)}")
                
                # Wait for next check
                await asyncio.sleep(interval)
        
        # Start the task
        self.heartbeat_task = asyncio.create_task(monitor_heartbeats())
    
    async def stop_heartbeat_monitor(self) -> None:
        """Stop the heartbeat monitor task."""
        if self.heartbeat_task is None:
            self.logger.warning("Heartbeat monitor is not running")
            return
        
        self.heartbeat_task.cancel()
        try:
            await self.heartbeat_task
        except asyncio.CancelledError:
            pass
        
        self.heartbeat_task = None
        self.logger.info("Heartbeat monitor stopped")
