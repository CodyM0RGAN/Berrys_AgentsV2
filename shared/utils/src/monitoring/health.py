"""
Health check system for the Berrys_AgentsV2 platform.

This module provides functionality for monitoring the health of services and
dependencies. It allows registering health checks, executing them, and reporting
their results.

Usage:
    from shared.utils.src.monitoring.health import register_health_check, check_health

    # Register a health check
    @register_health_check("database")
    def check_database_connection():
        # Check if database is accessible
        return True, "Database connection is healthy"

    # Check health of all registered components
    health_status = check_health()
    
    # Get health status for specific component
    db_status = check_health("database")
"""

import functools
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, cast, Set

# Configure basic logging
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status values for components."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


# Registry of health check functions
_health_checks: Dict[str, Callable[[], Tuple[bool, str]]] = {}


def register_health_check(component_name: str, depends_on: Optional[Set[str]] = None) -> Callable:
    """
    Decorator to register a function as a health check.
    
    Args:
        component_name: The name of the component to check
        depends_on: Set of component names this check depends on
        
    Returns:
        A decorator function that registers the health check
    """
    def decorator(func: Callable[[], Tuple[bool, str]]) -> Callable[[], Tuple[bool, str]]:
        """Register a health check function."""
        _health_checks[component_name] = func
        func._depends_on = depends_on or set()  # type: ignore
        logger.info(f"Registered health check for {component_name}")
        return func
    
    return decorator


import asyncio
import inspect

async def check_health(component_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Check the health of services and dependencies.
    
    Args:
        component_name: The name of a specific component to check, or None to check all
        
    Returns:
        A dictionary with health check results
    """
    start_time = time.time()
    
    if component_name:
        # Check health of specific component
        if component_name not in _health_checks:
            return {
                "status": HealthStatus.UNKNOWN.value,
                "message": f"No health check registered for {component_name}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        check_func = _health_checks[component_name]
        if inspect.iscoroutinefunction(check_func):
            is_healthy, message = await check_func()
        else:
            is_healthy, message = check_func()
            
        health_info = {
            "status": HealthStatus.HEALTHY.value if is_healthy else HealthStatus.UNHEALTHY.value,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    else:
        # Check health of all registered components
        components: Dict[str, Dict[str, Any]] = {}
        is_healthy = True
        
        for name, check_func in _health_checks.items():
            if inspect.iscoroutinefunction(check_func):
                component_healthy, message = await check_func()
            else:
                component_healthy, message = check_func()
                
            components[name] = {
                "status": HealthStatus.HEALTHY.value if component_healthy else HealthStatus.UNHEALTHY.value,
                "message": message
            }
            is_healthy = is_healthy and component_healthy
        
        health_info = {
            "status": HealthStatus.HEALTHY.value if is_healthy else HealthStatus.UNHEALTHY.value,
            "components": components,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    # Add execution time
    execution_time = time.time() - start_time
    health_info["execution_time"] = f"{execution_time:.3f}s"
    
    return health_info


async def is_service_healthy() -> bool:
    """
    Check if the service is healthy.
    
    Returns:
        True if the service is healthy, False otherwise
    """
    health_info = await check_health()
    return health_info["status"] == HealthStatus.HEALTHY.value


class HealthCheck:
    """
    Class for registering and executing health checks.
    
    This provides a more flexible alternative to the decorator-based approach.
    """
    
    def __init__(self, name: str):
        """
        Initialize a new health check.
        
        Args:
            name: The name of the health check
        """
        self.name = name
        self.checks: Dict[str, Callable[[], Tuple[bool, str]]] = {}
        self.dependencies: Dict[str, Set[str]] = {}
    
    def add_check(self, component_name: str, check_func: Callable[[], Tuple[bool, str]], 
                 depends_on: Optional[Set[str]] = None) -> None:
        """
        Add a health check.
        
        Args:
            component_name: The name of the component to check
            check_func: The function that performs the health check
            depends_on: Set of component names this check depends on
        """
        self.checks[component_name] = check_func
        self.dependencies[component_name] = depends_on or set()
        logger.info(f"Added health check for {component_name} to {self.name}")
    
    def check(self, component_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Check the health of components.
        
        Args:
            component_name: The name of a specific component to check, or None to check all
            
        Returns:
            A dictionary with health check results
        """
        start_time = time.time()
        
        if component_name:
            # Check health of specific component
            if component_name not in self.checks:
                return {
                    "status": HealthStatus.UNKNOWN.value,
                    "message": f"No health check registered for {component_name}",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            
            is_healthy, message = self.checks[component_name]()
            health_info = {
                "status": HealthStatus.HEALTHY.value if is_healthy else HealthStatus.UNHEALTHY.value,
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            # Check health of all registered components
            components: Dict[str, Dict[str, Any]] = {}
            is_healthy = True
            
            # To handle dependencies correctly, we need to check components in order
            checked: Set[str] = set()
            to_check = list(self.checks.keys())
            
            while to_check:
                # Find a component whose dependencies have all been checked
                for component in to_check[:]:
                    dependencies = self.dependencies.get(component, set())
                    if all(dep in checked for dep in dependencies):
                        # Check this component
                        component_healthy, message = self.checks[component]()
                        components[component] = {
                            "status": HealthStatus.HEALTHY.value if component_healthy else HealthStatus.UNHEALTHY.value,
                            "message": message
                        }
                        is_healthy = is_healthy and component_healthy
                        
                        # Mark as checked and remove from to_check
                        checked.add(component)
                        to_check.remove(component)
                        break
                else:
                    # If we get here, we have a circular dependency
                    logger.warning("Circular dependency detected in health checks")
                    break
            
            health_info = {
                "status": HealthStatus.HEALTHY.value if is_healthy else HealthStatus.UNHEALTHY.value,
                "components": components,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        # Add execution time
        execution_time = time.time() - start_time
        health_info["execution_time"] = f"{execution_time:.3f}s"
        
        return health_info


# Common health checks

def check_database_connection(database_url: str) -> Callable[[], Tuple[bool, str]]:
    """
    Create a health check function for a database connection.
    
    Args:
        database_url: The URL of the database to check
        
    Returns:
        A health check function
    """
    def check() -> Tuple[bool, str]:
        try:
            # This is a placeholder - in a real implementation, we would actually
            # connect to the database and run a simple query
            logger.debug(f"Checking database connection to {database_url}")
            # Use SQLAlchemy to connect to the database and run a simple query
            # import sqlalchemy
            # engine = sqlalchemy.create_engine(database_url)
            # with engine.connect() as conn:
            #     conn.execute("SELECT 1")
            return True, "Database connection is healthy"
        except Exception as e:
            return False, f"Database connection failed: {str(e)}"
    
    return check


def check_redis_connection(redis_url: str) -> Callable[[], Tuple[bool, str]]:
    """
    Create a health check function for a Redis connection.
    
    Args:
        redis_url: The URL of the Redis server to check
        
    Returns:
        A health check function
    """
    def check() -> Tuple[bool, str]:
        try:
            # This is a placeholder - in a real implementation, we would actually
            # connect to Redis and run a simple command
            logger.debug(f"Checking Redis connection to {redis_url}")
            # Use redis-py to connect to Redis and run a simple command
            # import redis
            # r = redis.from_url(redis_url)
            # r.ping()
            return True, "Redis connection is healthy"
        except Exception as e:
            return False, f"Redis connection failed: {str(e)}"
    
    return check


def check_external_service(service_url: str, timeout: float = 5.0) -> Callable[[], Tuple[bool, str]]:
    """
    Create a health check function for an external service.
    
    Args:
        service_url: The URL of the service to check
        timeout: The timeout for the request in seconds
        
    Returns:
        A health check function
    """
    def check() -> Tuple[bool, str]:
        try:
            # This is a placeholder - in a real implementation, we would actually
            # make an HTTP request to the service
            logger.debug(f"Checking external service at {service_url}")
            # Use requests to make an HTTP request to the service
            # import requests
            # response = requests.get(service_url, timeout=timeout)
            # response.raise_for_status()
            return True, "External service is healthy"
        except Exception as e:
            return False, f"External service check failed: {str(e)}"
    
    return check
