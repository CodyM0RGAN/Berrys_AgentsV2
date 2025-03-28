"""
Redis utility module for Berrys_AgentsV2.

This module provides utilities for working with Redis, including client creation and common operations.
"""

import logging
import redis.asyncio as redis
from typing import Optional, Dict, Any, List, Tuple, Union

logger = logging.getLogger(__name__)


def get_redis_client(redis_url: str) -> redis.Redis:
    """
    Get a Redis client.
    
    Args:
        redis_url: Redis URL
        
    Returns:
        Redis client
    """
    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        logger.info(f"Connected to Redis at {redis_url}")
        return redis_client
    except Exception as e:
        logger.error(f"Error connecting to Redis at {redis_url}: {str(e)}")
        raise


class RedisCache:
    """
    Redis cache utility.
    
    This class provides a simple interface for caching data in Redis.
    """
    
    def __init__(self, redis_client: redis.Redis, prefix: str = "cache"):
        """
        Initialize the Redis cache.
        
        Args:
            redis_client: Redis client
            prefix: Key prefix
        """
        self.redis_client = redis_client
        self.prefix = prefix
    
    async def get(self, key: str) -> Optional[str]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            return await self.redis_client.get(f"{self.prefix}:{key}")
        except Exception as e:
            logger.error(f"Error getting value for key {key} from Redis: {str(e)}")
            return None
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if ttl:
                await self.redis_client.setex(f"{self.prefix}:{key}", ttl, value)
            else:
                await self.redis_client.set(f"{self.prefix}:{key}", value)
            return True
        except Exception as e:
            logger.error(f"Error setting value for key {key} in Redis: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.redis_client.delete(f"{self.prefix}:{key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if the key exists, False otherwise
        """
        try:
            return bool(await self.redis_client.exists(f"{self.prefix}:{key}"))
        except Exception as e:
            logger.error(f"Error checking if key {key} exists in Redis: {str(e)}")
            return False
    
    async def ttl(self, key: str) -> int:
        """
        Get the time to live for a key.
        
        Args:
            key: Cache key
            
        Returns:
            Time to live in seconds, -1 if the key exists but has no TTL, -2 if the key does not exist
        """
        try:
            return await self.redis_client.ttl(f"{self.prefix}:{key}")
        except Exception as e:
            logger.error(f"Error getting TTL for key {key} from Redis: {str(e)}")
            return -2
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set the time to live for a key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return bool(await self.redis_client.expire(f"{self.prefix}:{key}", ttl))
        except Exception as e:
            logger.error(f"Error setting TTL for key {key} in Redis: {str(e)}")
            return False


class RedisLock:
    """
    Redis lock utility.
    
    This class provides a simple interface for distributed locks using Redis.
    """
    
    def __init__(self, redis_client: redis.Redis, prefix: str = "lock"):
        """
        Initialize the Redis lock.
        
        Args:
            redis_client: Redis client
            prefix: Key prefix
        """
        self.redis_client = redis_client
        self.prefix = prefix
    
    async def acquire(self, key: str, ttl: int = 60) -> bool:
        """
        Acquire a lock.
        
        Args:
            key: Lock key
            ttl: Time to live in seconds
            
        Returns:
            True if the lock was acquired, False otherwise
        """
        try:
            return bool(await self.redis_client.set(f"{self.prefix}:{key}", "1", nx=True, ex=ttl))
        except Exception as e:
            logger.error(f"Error acquiring lock for key {key} in Redis: {str(e)}")
            return False
    
    async def release(self, key: str) -> bool:
        """
        Release a lock.
        
        Args:
            key: Lock key
            
        Returns:
            True if the lock was released, False otherwise
        """
        try:
            await self.redis_client.delete(f"{self.prefix}:{key}")
            return True
        except Exception as e:
            logger.error(f"Error releasing lock for key {key} in Redis: {str(e)}")
            return False
    
    async def is_locked(self, key: str) -> bool:
        """
        Check if a lock is held.
        
        Args:
            key: Lock key
            
        Returns:
            True if the lock is held, False otherwise
        """
        try:
            return bool(await self.redis_client.exists(f"{self.prefix}:{key}"))
        except Exception as e:
            logger.error(f"Error checking if lock for key {key} is held in Redis: {str(e)}")
            return False


class RedisPubSub:
    """
    Redis publish-subscribe utility.
    
    This class provides a simple interface for publish-subscribe messaging using Redis.
    """
    
    def __init__(self, redis_client: redis.Redis, prefix: str = "pubsub"):
        """
        Initialize the Redis publish-subscribe utility.
        
        Args:
            redis_client: Redis client
            prefix: Channel prefix
        """
        self.redis_client = redis_client
        self.prefix = prefix
    
    async def publish(self, channel: str, message: str) -> int:
        """
        Publish a message to a channel.
        
        Args:
            channel: Channel name
            message: Message to publish
            
        Returns:
            Number of clients that received the message
        """
        try:
            return await self.redis_client.publish(f"{self.prefix}:{channel}", message)
        except Exception as e:
            logger.error(f"Error publishing message to channel {channel} in Redis: {str(e)}")
            return 0
    
    async def subscribe(self, *channels: str) -> redis.client.PubSub:
        """
        Subscribe to one or more channels.
        
        Args:
            *channels: Channel names
            
        Returns:
            PubSub object
        """
        try:
            pubsub = self.redis_client.pubsub()
            prefixed_channels = [f"{self.prefix}:{channel}" for channel in channels]
            await pubsub.subscribe(*prefixed_channels)
            return pubsub
        except Exception as e:
            logger.error(f"Error subscribing to channels {channels} in Redis: {str(e)}")
            raise
    
    async def psubscribe(self, *patterns: str) -> redis.client.PubSub:
        """
        Subscribe to one or more channel patterns.
        
        Args:
            *patterns: Channel patterns
            
        Returns:
            PubSub object
        """
        try:
            pubsub = self.redis_client.pubsub()
            prefixed_patterns = [f"{self.prefix}:{pattern}" for pattern in patterns]
            await pubsub.psubscribe(*prefixed_patterns)
            return pubsub
        except Exception as e:
            logger.error(f"Error subscribing to patterns {patterns} in Redis: {str(e)}")
            raise
