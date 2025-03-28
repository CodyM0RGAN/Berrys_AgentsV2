"""
Service discovery strategies for different discovery mechanisms.

This module implements the Strategy Pattern for service discovery,
allowing different service discovery backends (Redis, Consul, etcd, etc.)
to be used interchangeably.
"""
import abc
import json
import logging
from typing import Dict, List, Optional, Any, Type
import asyncio
import aioredis
import time
from datetime import datetime

from ....models.api import ServiceInfo, ServiceType, ServiceStatus
from ....exceptions import ServiceDiscoveryError, ServiceNotFoundError


class ServiceDiscoveryStrategy(abc.ABC):
    """
    Abstract base class for service discovery strategies.
    
    This defines the interface that all concrete strategies must implement.
    """
    
    @abc.abstractmethod
    async def register_service(self, service: ServiceInfo) -> ServiceInfo:
        """Register a service with the discovery mechanism."""
        pass
    
    @abc.abstractmethod
    async def unregister_service(self, service_id: str) -> bool:
        """Unregister a service from the discovery mechanism."""
        pass
    
    @abc.abstractmethod
    async def get_service(self, service_id: str) -> Optional[ServiceInfo]:
        """Get information about a specific service."""
        pass
    
    @abc.abstractmethod
    async def find_services(
        self, 
        service_type: Optional[ServiceType] = None,
        include_offline: bool = False
    ) -> List[ServiceInfo]:
        """Find services matching the specified criteria."""
        pass
    
    @abc.abstractmethod
    async def update_service_status(self, service_id: str, status: ServiceStatus) -> bool:
        """Update the status of a service."""
        pass
    
    @abc.abstractmethod
    async def update_heartbeat(self, service_id: str) -> bool:
        """Update the heartbeat timestamp for a service."""
        pass


class RedisServiceDiscoveryStrategy(ServiceDiscoveryStrategy):
    """
    Redis-based implementation of service discovery.
    
    Services are stored as serialized JSON in Redis keys, with TTL for automatic
    expiry of stale services.
    """
    
    def __init__(self, redis_url: str, service_ttl: int = 60, namespace: str = "service:"):
        """
        Initialize the Redis service discovery strategy.
        
        Args:
            redis_url: Redis connection URL
            service_ttl: TTL for service keys in seconds
            namespace: Namespace prefix for Redis keys
        """
        self.redis_url = redis_url
        self.service_ttl = service_ttl
        self.namespace = namespace
        self.redis = None
        self.logger = logging.getLogger("service_discovery.redis")
    
    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection."""
        if self.redis is None or self.redis.closed:
            try:
                self.redis = await aioredis.from_url(self.redis_url)
            except Exception as e:
                self.logger.error(f"Failed to connect to Redis: {str(e)}")
                raise ServiceDiscoveryError(f"Redis connection error: {str(e)}")
        return self.redis
    
    def _service_key(self, service_id: str) -> str:
        """Get the Redis key for a service."""
        return f"{self.namespace}{service_id}"
    
    def _type_index_key(self, service_type: ServiceType) -> str:
        """Get the Redis key for a service type index."""
        return f"{self.namespace}type:{service_type.value}"
    
    async def register_service(self, service: ServiceInfo) -> ServiceInfo:
        """Register a service with Redis."""
        redis = await self._get_redis()
        key = self._service_key(service.service_id)
        type_index = self._type_index_key(service.type)
        
        # Set current time for registration and heartbeat
        now = datetime.now()
        service.registered_at = now
        service.last_heartbeat = now
        service.status = ServiceStatus.ONLINE
        
        try:
            # Store service info
            service_data = service.json()
            pipe = redis.pipeline()
            await pipe.set(key, service_data, ex=self.service_ttl)
            await pipe.sadd(type_index, service.service_id)
            await pipe.execute()
            
            self.logger.info(f"Service {service.name} registered with ID {service.service_id}")
            return service
            
        except Exception as e:
            self.logger.error(f"Failed to register service: {str(e)}")
            raise ServiceDiscoveryError(f"Service registration error: {str(e)}")
    
    async def unregister_service(self, service_id: str) -> bool:
        """Unregister a service from Redis."""
        redis = await self._get_redis()
        key = self._service_key(service_id)
        
        try:
            # Get service info first to remove from type index
            service_data = await redis.get(key)
            if not service_data:
                return False
            
            service = ServiceInfo.parse_raw(service_data)
            type_index = self._type_index_key(service.type)
            
            # Remove service
            pipe = redis.pipeline()
            await pipe.srem(type_index, service_id)
            await pipe.delete(key)
            await pipe.execute()
            
            self.logger.info(f"Service {service_id} unregistered")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister service: {str(e)}")
            raise ServiceDiscoveryError(f"Service unregistration error: {str(e)}")
    
    async def get_service(self, service_id: str) -> Optional[ServiceInfo]:
        """Get information about a specific service from Redis."""
        redis = await self._get_redis()
        key = self._service_key(service_id)
        
        try:
            service_data = await redis.get(key)
            if not service_data:
                return None
            
            return ServiceInfo.parse_raw(service_data)
            
        except Exception as e:
            self.logger.error(f"Failed to get service {service_id}: {str(e)}")
            raise ServiceDiscoveryError(f"Service retrieval error: {str(e)}")
    
    async def find_services(
        self, 
        service_type: Optional[ServiceType] = None,
        include_offline: bool = False
    ) -> List[ServiceInfo]:
        """Find services matching the criteria in Redis."""
        redis = await self._get_redis()
        result = []
        
        try:
            # If type is specified, use the type index
            if service_type:
                type_index = self._type_index_key(service_type)
                service_ids = await redis.smembers(type_index)
            else:
                # Otherwise, scan all services
                cursor = 0
                service_ids = set()
                pattern = f"{self.namespace}*"
                while True:
                    cursor, keys = await redis.scan(cursor, match=pattern)
                    for key in keys:
                        if key.startswith(f"{self.namespace}type:".encode()):
                            # Skip type index keys
                            continue
                        # Extract service ID from key
                        service_id = key.decode("utf-8").replace(self.namespace, "")
                        service_ids.add(service_id)
                    if cursor == 0:
                        break
            
            # Get service info for each ID
            for service_id in service_ids:
                service = await self.get_service(service_id)
                if service:
                    # Filter by status if requested
                    if not include_offline and service.status != ServiceStatus.ONLINE:
                        continue
                    result.append(service)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to find services: {str(e)}")
            raise ServiceDiscoveryError(f"Service search error: {str(e)}")
    
    async def update_service_status(self, service_id: str, status: ServiceStatus) -> bool:
        """Update the status of a service in Redis."""
        redis = await self._get_redis()
        key = self._service_key(service_id)
        
        try:
            # Get service info
            service_data = await redis.get(key)
            if not service_data:
                raise ServiceNotFoundError(f"Service {service_id} not found")
            
            service = ServiceInfo.parse_raw(service_data)
            service.status = status
            
            # Update service
            await redis.set(key, service.json(), ex=self.service_ttl)
            
            self.logger.info(f"Service {service_id} status updated to {status}")
            return True
            
        except ServiceNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update service status: {str(e)}")
            raise ServiceDiscoveryError(f"Service status update error: {str(e)}")
    
    async def update_heartbeat(self, service_id: str) -> bool:
        """Update the heartbeat timestamp for a service in Redis."""
        redis = await self._get_redis()
        key = self._service_key(service_id)
        
        try:
            # Get service info
            service_data = await redis.get(key)
            if not service_data:
                raise ServiceNotFoundError(f"Service {service_id} not found")
            
            service = ServiceInfo.parse_raw(service_data)
            service.last_heartbeat = datetime.now()
            service.status = ServiceStatus.ONLINE
            
            # Update service and refresh TTL
            await redis.set(key, service.json(), ex=self.service_ttl)
            
            self.logger.debug(f"Service {service_id} heartbeat updated")
            return True
            
        except ServiceNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update heartbeat: {str(e)}")
            raise ServiceDiscoveryError(f"Heartbeat update error: {str(e)}")


# Factory function to create the appropriate strategy
def create_discovery_strategy(strategy_type: str, config: Dict[str, Any]) -> ServiceDiscoveryStrategy:
    """
    Create a service discovery strategy based on the specified type.
    
    Args:
        strategy_type: Type of discovery strategy ("redis", "consul", "etcd")
        config: Configuration for the strategy
    
    Returns:
        A ServiceDiscoveryStrategy instance
    
    Raises:
        ValueError: If the strategy type is not supported
    """
    if strategy_type.lower() == "redis":
        return RedisServiceDiscoveryStrategy(
            redis_url=config.get("url", "redis://localhost:6379/0"),
            service_ttl=config.get("ttl", 60),
            namespace=config.get("namespace", "service:")
        )
    # Add more strategies as needed (Consul, etcd, etc.)
    else:
        raise ValueError(f"Unsupported service discovery strategy: {strategy_type}")
