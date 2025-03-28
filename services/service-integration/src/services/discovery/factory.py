"""
Factory for creating service discovery strategies.

This module implements the Factory Pattern for creating service discovery strategies
based on configuration settings.
"""
from typing import Dict, Any, Optional
import logging

from ....config import settings
from ....exceptions import ServiceDiscoveryError
from .strategy import ServiceDiscoveryStrategy, create_discovery_strategy


class ServiceDiscoveryFactory:
    """
    Factory for creating service discovery strategies.
    
    This class provides a singleton instance of the appropriate service discovery
    strategy based on configuration settings.
    """
    
    _instance: Optional[ServiceDiscoveryStrategy] = None
    _logger = logging.getLogger("service_discovery.factory")
    
    @classmethod
    def get_strategy(cls) -> ServiceDiscoveryStrategy:
        """
        Get the service discovery strategy instance.
        
        If the instance doesn't exist, it will be created based on configuration settings.
        
        Returns:
            A ServiceDiscoveryStrategy instance
            
        Raises:
            ServiceDiscoveryError: If the strategy cannot be created
        """
        if cls._instance is None:
            try:
                strategy_type = settings.SERVICE_DISCOVERY_TYPE
                config: Dict[str, Any] = dict(settings.SERVICE_DISCOVERY_CONFIG)
                
                # Add Redis URL from settings if using Redis strategy
                if strategy_type.lower() == "redis":
                    config["url"] = settings.get_redis_url()
                
                cls._logger.info(f"Creating service discovery strategy: {strategy_type}")
                cls._instance = create_discovery_strategy(strategy_type, config)
                
            except Exception as e:
                cls._logger.error(f"Failed to create service discovery strategy: {str(e)}")
                raise ServiceDiscoveryError(f"Failed to create service discovery strategy: {str(e)}")
        
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """
        Reset the factory, clearing the cached strategy instance.
        
        This is primarily used for testing or when configuration changes.
        """
        cls._instance = None
        cls._logger.info("Service discovery factory reset")
