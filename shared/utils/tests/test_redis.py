"""
Tests for the Redis utility module.
"""

import pytest
import asyncio
import json
from typing import Dict, Any, List

from ..src.redis import (
    get_redis_client,
    RedisCache,
    RedisLock,
    RedisPubSub,
)


@pytest.fixture
async def redis_client():
    """
    Fixture for Redis client.
    
    This uses the actual Redis instance for testing.
    """
    # Use the test database (1) to avoid conflicts with development data
    redis_url = "redis://localhost:6379/1"
    client = get_redis_client(redis_url)
    
    # Clear the test database before each test
    await client.flushdb()
    
    yield client
    
    # Clean up after the test
    await client.flushdb()
    await client.close()


@pytest.mark.asyncio
async def test_redis_client(redis_client):
    """
    Test Redis client.
    """
    # Set a value
    await redis_client.set("test_key", "test_value")
    
    # Get the value
    value = await redis_client.get("test_key")
    
    # Check the value
    assert value == "test_value"


@pytest.mark.asyncio
async def test_redis_cache(redis_client):
    """
    Test RedisCache.
    """
    # Create a cache
    cache = RedisCache(redis_client, "test_cache")
    
    # Set a value
    await cache.set("test_key", "test_value")
    
    # Get the value
    value = await cache.get("test_key")
    
    # Check the value
    assert value == "test_value"
    
    # Check if the key exists
    exists = await cache.exists("test_key")
    assert exists is True
    
    # Set a value with TTL
    await cache.set("test_key_ttl", "test_value_ttl", 1)
    
    # Get the TTL
    ttl = await cache.ttl("test_key_ttl")
    assert ttl > 0
    
    # Wait for the key to expire
    await asyncio.sleep(1.1)
    
    # Check if the key exists
    exists = await cache.exists("test_key_ttl")
    assert exists is False
    
    # Delete a key
    await cache.delete("test_key")
    
    # Check if the key exists
    exists = await cache.exists("test_key")
    assert exists is False


@pytest.mark.asyncio
async def test_redis_lock(redis_client):
    """
    Test RedisLock.
    """
    # Create a lock
    lock = RedisLock(redis_client, "test_lock")
    
    # Acquire the lock
    acquired = await lock.acquire("test_key")
    assert acquired is True
    
    # Check if the lock is held
    is_locked = await lock.is_locked("test_key")
    assert is_locked is True
    
    # Try to acquire the lock again
    acquired = await lock.acquire("test_key")
    assert acquired is False
    
    # Release the lock
    await lock.release("test_key")
    
    # Check if the lock is held
    is_locked = await lock.is_locked("test_key")
    assert is_locked is False
    
    # Acquire the lock with TTL
    acquired = await lock.acquire("test_key_ttl", 1)
    assert acquired is True
    
    # Wait for the lock to expire
    await asyncio.sleep(1.1)
    
    # Check if the lock is held
    is_locked = await lock.is_locked("test_key_ttl")
    assert is_locked is False


@pytest.mark.asyncio
async def test_redis_pubsub(redis_client):
    """
    Test RedisPubSub.
    """
    # Create a pubsub
    pubsub = RedisPubSub(redis_client, "test_pubsub")
    
    # Create a message handler
    messages = []
    
    async def message_handler():
        # Subscribe to a channel
        ps = await pubsub.subscribe("test_channel")
        
        # Process messages
        async for message in ps.listen():
            if message["type"] == "message":
                messages.append(message["data"])
                if message["data"] == "stop":
                    break
    
    # Start the message handler
    task = asyncio.create_task(message_handler())
    
    # Wait for the subscription to be established
    await asyncio.sleep(0.1)
    
    # Publish a message
    await pubsub.publish("test_channel", "test_message")
    
    # Publish another message
    await pubsub.publish("test_channel", "stop")
    
    # Wait for the message handler to finish
    await task
    
    # Check the messages
    assert messages == ["test_message", "stop"]


@pytest.mark.asyncio
async def test_redis_pubsub_pattern(redis_client):
    """
    Test RedisPubSub with pattern subscription.
    """
    # Create a pubsub
    pubsub = RedisPubSub(redis_client, "test_pubsub")
    
    # Create a message handler
    messages = []
    
    async def message_handler():
        # Subscribe to a pattern
        ps = await pubsub.psubscribe("test_*")
        
        # Process messages
        async for message in ps.listen():
            if message["type"] == "pmessage":
                messages.append((message["channel"], message["data"]))
                if message["data"] == "stop":
                    break
    
    # Start the message handler
    task = asyncio.create_task(message_handler())
    
    # Wait for the subscription to be established
    await asyncio.sleep(0.1)
    
    # Publish messages to different channels
    await pubsub.publish("test_channel1", "message1")
    await pubsub.publish("test_channel2", "message2")
    await pubsub.publish("other_channel", "message3")  # Should not be received
    await pubsub.publish("test_channel1", "stop")
    
    # Wait for the message handler to finish
    await task
    
    # Check the messages
    assert len(messages) == 3
    assert messages[0][0] == "test_pubsub:test_channel1"
    assert messages[0][1] == "message1"
    assert messages[1][0] == "test_pubsub:test_channel2"
    assert messages[1][1] == "message2"
    assert messages[2][0] == "test_pubsub:test_channel1"
    assert messages[2][1] == "stop"
