"""
Redis caching utilities for Berrys_AgentsV2 platform.

This module provides caching functionality using Redis for the Berrys_AgentsV2
production environment. It includes decorators and utilities for implementing
caching at various levels of the application.
"""

import json
import hashlib
import time
import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast

import redis
from redis.exceptions import RedisError

# Type variables for generic function signatures
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

# Configure logging
logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache implementation for Berrys_AgentsV2 platform."""
    
    def __init__(
        self,
        host: str = 'redis.berrys-production.svc.cluster.local',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        prefix: str = 'berrys:cache:'
    ):
        """
        Initialize Redis cache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (if required)
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connection timeout in seconds
            prefix: Key prefix for all cache keys
        """
        self.prefix = prefix
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_connect_timeout,
                decode_responses=False  # Keep binary data for proper serialization
            )
            self.health_check()
            logger.info(f"Connected to Redis at {host}:{port} (db: {db})")
        except RedisError as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching will be disabled.")
            self.client = None
    
    def health_check(self) -> bool:
        """
        Check if Redis connection is healthy.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        if not self.client:
            return False
        
        try:
            return self.client.ping()
        except RedisError:
            return False
    
    def generate_key(self, prefix: str, *args: Any, **kwargs: Any) -> str:
        """
        Generate a cache key from prefix and function arguments.
        
        Args:
            prefix: Key prefix specific to the function being cached
            *args: Positional arguments to hash
            **kwargs: Keyword arguments to hash
            
        Returns:
            str: Generated cache key
        """
        key_parts = [self.prefix, prefix]
        
        # Hash positional arguments
        if args:
            key_parts.append(hashlib.md5(str(args).encode()).hexdigest())
        
        # Hash keyword arguments (sorted for consistency)
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.append(hashlib.md5(str(sorted_kwargs).encode()).hexdigest())
        
        return ":".join(key_parts)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Any: Cached value or None if key not found
        """
        if not self.client:
            return None
        
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Error retrieving from cache: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 300)
            
        Returns:
            bool: True if value was set, False otherwise
        """
        if not self.client:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            return bool(self.client.setex(key, ttl, serialized))
        except (RedisError, TypeError) as e:
            logger.warning(f"Error setting cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if value was deleted, False otherwise
        """
        if not self.client:
            return False
        
        try:
            return bool(self.client.delete(key))
        except RedisError as e:
            logger.warning(f"Error deleting from cache: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Key pattern to match
            
        Returns:
            int: Number of keys deleted
        """
        if not self.client:
            return 0
        
        try:
            keys = list(self.client.scan_iter(f"{self.prefix}{pattern}*"))
            if not keys:
                return 0
            return self.client.delete(*keys)
        except RedisError as e:
            logger.warning(f"Error deleting pattern from cache: {e}")
            return 0
    
    def cache_decorator(self, prefix: str, ttl: int = 300) -> Callable[[F], F]:
        """
        Decorator for caching function results.
        
        Args:
            prefix: Key prefix specific to the function being cached
            ttl: Time to live in seconds (default: 300)
            
        Returns:
            Decorator function
        """
        def decorator(func: F) -> F:
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                # Generate cache key
                cache_key = self.generate_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__} with key {cache_key}")
                    return cached_result
                
                # Execute function if not in cache
                logger.debug(f"Cache miss for {func.__name__} with key {cache_key}")
                result = await func(*args, **kwargs)
                
                # Store in cache
                self.set(cache_key, result, ttl)
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                # Generate cache key
                cache_key = self.generate_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__} with key {cache_key}")
                    return cached_result
                
                # Execute function if not in cache
                logger.debug(f"Cache miss for {func.__name__} with key {cache_key}")
                result = func(*args, **kwargs)
                
                # Store in cache
                self.set(cache_key, result, ttl)
                
                return result
            
            # Choose the appropriate wrapper based on whether the function is async
            if asyncio_is_coroutine_function(func):
                return cast(F, async_wrapper)
            return cast(F, sync_wrapper)
        
        return decorator
    
    def invalidate_cache(self, prefix: str, *args: Any, **kwargs: Any) -> bool:
        """
        Invalidate specific cache key.
        
        Args:
            prefix: Key prefix specific to the function being cached
            *args: Positional arguments to hash
            **kwargs: Keyword arguments to hash
            
        Returns:
            bool: True if cache was invalidated, False otherwise
        """
        cache_key = self.generate_key(prefix, *args, **kwargs)
        return self.delete(cache_key)
    
    def invalidate_cache_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache keys matching pattern.
        
        Args:
            pattern: Key pattern to match
            
        Returns:
            int: Number of keys invalidated
        """
        return self.delete_pattern(pattern)


# Helper to check if a function is a coroutine
def asyncio_is_coroutine_function(func: Callable[..., Any]) -> bool:
    """
    Check if a function is a coroutine function.
    
    Args:
        func: Function to check
        
    Returns:
        bool: True if function is a coroutine function, False otherwise
    """
    import inspect
    return inspect.iscoroutinefunction(func)


# Simplified usage example:

# Initialize cache
# cache = RedisCache()

# # Decorator usage
# @cache.cache_decorator(prefix="user_projects", ttl=600)
# async def get_user_projects(user_id: str):
#     # Database query would go here
#     return [{"id": "1", "name": "Project 1"}, {"id": "2", "name": "Project 2"}]

# # Invalidation example
# def update_project(project_id: str, data: Dict[str, Any]):
#     # Update database...
#     # Then invalidate cache
#     cache.invalidate_cache_pattern(f"user_projects:*")
#     return {"success": True}
