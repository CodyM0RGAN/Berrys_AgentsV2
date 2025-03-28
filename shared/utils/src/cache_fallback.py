"""
Cache fallback implementation for handling service unavailability.

This module provides a cache fallback implementation that can be used to provide
resilience when services are unavailable. It caches service responses and falls
back to cached data when services are unavailable.
"""
import asyncio
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple, TypeVar, Union

# Set up logger
logger = logging.getLogger(__name__)

# Type variable for the return type of the operation
T = TypeVar('T')

class CacheStrategy(Enum):
    """Possible cache strategies."""
    CACHE_FIRST = auto()  # Try cache first, then service
    SERVICE_FIRST = auto()  # Try service first, then cache
    STALE_WHILE_REVALIDATE = auto()  # Return from cache, then update cache in background


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    
    data: Any
    """Cached data."""
    
    timestamp: float
    """Timestamp when the data was cached."""
    
    ttl: float
    """Time-to-live in seconds."""
    
    @property
    def is_fresh(self) -> bool:
        """Check if the cache entry is still fresh."""
        return time.time() - self.timestamp < self.ttl
    
    @property
    def age(self) -> float:
        """Get the age of the cache entry in seconds."""
        return time.time() - self.timestamp


class CacheFallback:
    """
    Implementation of cache fallback for service unavailability.
    
    This class provides a way to cache service responses and fall back to
    cached data when services are unavailable. It supports different cache
    strategies:
    
    - CACHE_FIRST: Try cache first, then service
    - SERVICE_FIRST: Try service first, then cache
    - STALE_WHILE_REVALIDATE: Return from cache, then update cache in background
    """
    
    def __init__(
        self,
        cache_key_prefix: str,
        ttl: float = 3600.0,  # 1 hour
        strategy: CacheStrategy = CacheStrategy.SERVICE_FIRST,
        redis_client: Optional[Any] = None
    ):
        """
        Initialize CacheFallback.
        
        Args:
            cache_key_prefix: Prefix for cache keys
            ttl: Time-to-live in seconds
            strategy: Cache strategy
            redis_client: Redis client (optional)
        """
        self.cache_key_prefix = cache_key_prefix
        self.ttl = ttl
        self.strategy = strategy
        self.redis_client = redis_client
        
        # In-memory cache for when Redis is not available
        self._memory_cache: Dict[str, CacheEntry] = {}
    
    def _get_full_key(self, cache_key: str) -> str:
        """
        Get the full cache key with prefix.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Full cache key
        """
        return f"{self.cache_key_prefix}:{cache_key}"
    
    async def get(self, cache_key: str) -> Optional[Any]:
        """
        Get data from cache.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached data or None if not found
        """
        full_key = self._get_full_key(cache_key)
        
        # Try Redis first if available
        if self.redis_client:
            try:
                data = await self.redis_client.get(full_key)
                if data:
                    entry_dict = json.loads(data)
                    entry = CacheEntry(
                        data=entry_dict['data'],
                        timestamp=entry_dict['timestamp'],
                        ttl=entry_dict['ttl']
                    )
                    
                    if entry.is_fresh:
                        logger.debug(f"Cache hit for key {full_key} (Redis)")
                        return entry.data
                    else:
                        logger.debug(f"Cache expired for key {full_key} (Redis)")
                        return None
                else:
                    logger.debug(f"Cache miss for key {full_key} (Redis)")
                    return None
            except Exception as e:
                logger.warning(f"Error getting from Redis cache: {str(e)}")
        
        # Fall back to memory cache
        if full_key in self._memory_cache:
            entry = self._memory_cache[full_key]
            if entry.is_fresh:
                logger.debug(f"Cache hit for key {full_key} (memory)")
                return entry.data
            else:
                logger.debug(f"Cache expired for key {full_key} (memory)")
                del self._memory_cache[full_key]
                return None
        
        logger.debug(f"Cache miss for key {full_key} (memory)")
        return None
    
    async def set(self, cache_key: str, data: Any, ttl: Optional[float] = None) -> None:
        """
        Set data in cache.
        
        Args:
            cache_key: Cache key
            data: Data to cache
            ttl: Time-to-live in seconds (optional, defaults to instance ttl)
        """
        full_key = self._get_full_key(cache_key)
        entry = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl=ttl or self.ttl
        )
        
        # Try Redis first if available
        if self.redis_client:
            try:
                entry_dict = {
                    'data': data,
                    'timestamp': entry.timestamp,
                    'ttl': entry.ttl
                }
                await self.redis_client.setex(
                    full_key,
                    int(entry.ttl),
                    json.dumps(entry_dict)
                )
                logger.debug(f"Set cache for key {full_key} (Redis)")
            except Exception as e:
                logger.warning(f"Error setting Redis cache: {str(e)}")
        
        # Always set in memory cache as well
        self._memory_cache[full_key] = entry
        logger.debug(f"Set cache for key {full_key} (memory)")
    
    async def get_or_fetch(
        self,
        cache_key: str,
        fetch_func: Callable[[], Awaitable[T]],
        ttl: Optional[float] = None,
        strategy: Optional[CacheStrategy] = None,
        request_id: Optional[str] = None
    ) -> Tuple[T, bool]:
        """
        Get data from cache or fetch from service.
        
        Args:
            cache_key: Cache key
            fetch_func: Function to fetch data from service
            ttl: Time-to-live in seconds (optional, defaults to instance ttl)
            strategy: Cache strategy (optional, defaults to instance strategy)
            request_id: Request ID for logging
            
        Returns:
            Tuple of (data, from_cache) where from_cache is True if the data
            came from the cache
        """
        log_context = {"request_id": request_id} if request_id else {}
        strategy = strategy or self.strategy
        
        if strategy == CacheStrategy.CACHE_FIRST:
            # Try cache first, then service
            cached_data = await self.get(cache_key)
            if cached_data is not None:
                logger.info(f"Using cached data for key {cache_key}", extra=log_context)
                return cached_data, True
            
            try:
                logger.info(f"Fetching data for key {cache_key}", extra=log_context)
                data = await fetch_func()
                await self.set(cache_key, data, ttl)
                return data, False
            except Exception as e:
                logger.error(f"Error fetching data for key {cache_key}: {str(e)}", extra=log_context)
                raise
        
        elif strategy == CacheStrategy.SERVICE_FIRST:
            # Try service first, then cache
            try:
                logger.info(f"Fetching data for key {cache_key}", extra=log_context)
                data = await fetch_func()
                await self.set(cache_key, data, ttl)
                return data, False
            except Exception as e:
                logger.warning(
                    f"Error fetching data for key {cache_key}: {str(e)}, falling back to cache",
                    extra=log_context
                )
                cached_data = await self.get(cache_key)
                if cached_data is not None:
                    logger.info(f"Using cached data for key {cache_key}", extra=log_context)
                    return cached_data, True
                else:
                    logger.error(f"No cached data available for key {cache_key}", extra=log_context)
                    raise
        
        elif strategy == CacheStrategy.STALE_WHILE_REVALIDATE:
            # Return from cache, then update cache in background
            cached_data = await self.get(cache_key)
            
            async def update_cache():
                try:
                    logger.info(f"Updating cache for key {cache_key}", extra=log_context)
                    data = await fetch_func()
                    await self.set(cache_key, data, ttl)
                except Exception as e:
                    logger.error(f"Error updating cache for key {cache_key}: {str(e)}", extra=log_context)
            
            if cached_data is not None:
                # Schedule cache update in background
                asyncio.create_task(update_cache())
                logger.info(f"Using cached data for key {cache_key}", extra=log_context)
                return cached_data, True
            else:
                # No cached data, fetch synchronously
                try:
                    logger.info(f"Fetching data for key {cache_key}", extra=log_context)
                    data = await fetch_func()
                    await self.set(cache_key, data, ttl)
                    return data, False
                except Exception as e:
                    logger.error(f"Error fetching data for key {cache_key}: {str(e)}", extra=log_context)
                    raise
        
        else:
            raise ValueError(f"Unknown cache strategy: {strategy}")
