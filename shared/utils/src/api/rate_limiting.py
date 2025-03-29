"""
Rate limiting middleware and utilities for Berrys_AgentsV2 platform.

This module provides rate limiting middleware and utilities for API endpoints
in the Berrys_AgentsV2 production environment. It uses Redis as a backend for
tracking rate limits across distributed instances.
"""

import time
import logging
import json
from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast

# Import Redis client
try:
    import redis
    from redis.exceptions import RedisError
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    logging.warning("Redis not available, in-memory rate limiting will be used")

# Try to import FastAPI components if available
try:
    from fastapi import Request, Response, HTTPException, Depends
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    logging.warning("FastAPI not available, FastAPI middleware will not be available")

# Define logger
logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    
    requests: int = 100  # Number of requests allowed in window
    window: int = 60     # Time window in seconds
    tier: str = "default"  # Rate limit tier


class RateLimitKey:
    """Utility class for generating rate limit keys."""
    
    @staticmethod
    def from_request(request: Any, tier: str = "default") -> str:
        """
        Generate a rate limit key from a request.
        
        Args:
            request: HTTP request
            tier: Rate limit tier
            
        Returns:
            str: Rate limit key
        """
        # For FastAPI requests
        if hasattr(request, "client") and hasattr(request.client, "host"):
            client_ip = request.client.host
            if hasattr(request, "url") and hasattr(request.url, "path"):
                path = request.url.path
                return f"ratelimit:{tier}:{client_ip}:{path}"
            
        # Generic fallback
        return f"ratelimit:{tier}:generic:{id(request)}"
    
    @staticmethod
    def from_client_id(client_id: str, resource: str, tier: str = "default") -> str:
        """
        Generate a rate limit key from a client ID and resource.
        
        Args:
            client_id: Client identifier (e.g., API key, user ID)
            resource: Resource being accessed
            tier: Rate limit tier
            
        Returns:
            str: Rate limit key
        """
        return f"ratelimit:{tier}:{client_id}:{resource}"


class RateLimiter:
    """Rate limiter implementation."""
    
    def __init__(
        self,
        redis_host: str = "redis.berrys-production.svc.cluster.local",
        redis_port: int = 6379,
        redis_db: int = 2,
        redis_password: Optional[str] = None,
        prefix: str = "berrys:ratelimit:",
        fallback_to_memory: bool = True
    ):
        """
        Initialize rate limiter.
        
        Args:
            redis_host: Redis host
            redis_port: Redis port
            redis_db: Redis database number
            redis_password: Redis password
            prefix: Prefix for rate limit keys
            fallback_to_memory: Whether to fall back to in-memory rate limiting if Redis is unavailable
        """
        self.prefix = prefix
        self._rate_limit_configs: Dict[str, RateLimitConfig] = {
            "default": RateLimitConfig(100, 60, "default"),
            "low": RateLimitConfig(50, 60, "low"),
            "high": RateLimitConfig(200, 60, "high"),
            "critical": RateLimitConfig(500, 60, "critical"),
            "unlimited": RateLimitConfig(100000, 60, "unlimited")
        }
        self._in_memory_counters: Dict[str, Dict[int, int]] = {}
        
        # Initialize Redis client if available
        self.redis_client = None
        if HAS_REDIS:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password,
                    socket_timeout=2,
                    socket_connect_timeout=2,
                    decode_responses=False
                )
                # Verify Redis connection
                self.redis_client.ping()
                logger.info(f"Connected to Redis for rate limiting at {redis_host}:{redis_port}")
            except (RedisError, Exception) as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                self.redis_client = None
                if not fallback_to_memory:
                    raise RuntimeError("Failed to connect to Redis and fallback is disabled")
        
        if self.redis_client is None and fallback_to_memory:
            logger.warning("Using in-memory rate limiting (not suitable for distributed deployment)")
    
    def add_limit_tier(self, tier: str, config: RateLimitConfig) -> None:
        """
        Add or update a rate limit tier configuration.
        
        Args:
            tier: Rate limit tier name
            config: Rate limit configuration
        """
        self._rate_limit_configs[tier] = config
    
    def _check_redis_limit(self, key: str, tier: str = "default") -> Tuple[bool, Dict[str, Any]]:
        """
        Check rate limit using Redis.
        
        Args:
            key: Rate limit key
            tier: Rate limit tier
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (allowed, limit_info)
        """
        limit_config = self._rate_limit_configs.get(tier, self._rate_limit_configs["default"])
        
        # Get the full key with prefix
        full_key = f"{self.prefix}{key}"
        
        # Get current timestamp
        now = int(time.time())
        window_start = now - limit_config.window
        
        try:
            # Add current request to sliding window
            pipeline = self.redis_client.pipeline()
            pipeline.zadd(full_key, {str(now): now})
            pipeline.zremrangebyscore(full_key, 0, window_start)
            pipeline.zcard(full_key)
            pipeline.expire(full_key, limit_config.window + 10)  # Add buffer
            _, _, request_count, _ = pipeline.execute()
            
            # Calculate remaining requests
            remaining = max(0, limit_config.requests - request_count)
            
            # Get reset time
            if request_count > 0 and request_count >= limit_config.requests:
                # Calculate when the oldest request expires
                oldest_requests = self.redis_client.zrange(
                    full_key, 0, 0, withscores=True
                )
                if oldest_requests:
                    oldest_time = int(float(oldest_requests[0][1]))
                    reset_time = oldest_time + limit_config.window - now
                else:
                    reset_time = limit_config.window
            else:
                reset_time = limit_config.window
            
            # Check if rate limit exceeded
            allowed = request_count <= limit_config.requests
            
            # Limit info
            limit_info = {
                "allowed": allowed,
                "limit": limit_config.requests,
                "remaining": remaining,
                "reset": reset_time,
                "window": limit_config.window
            }
            
            return allowed, limit_info
            
        except Exception as e:
            logger.warning(f"Redis rate limiting error: {e}, falling back to memory")
            return self._check_memory_limit(key, tier)
    
    def _check_memory_limit(self, key: str, tier: str = "default") -> Tuple[bool, Dict[str, Any]]:
        """
        Check rate limit using in-memory counters.
        
        Args:
            key: Rate limit key
            tier: Rate limit tier
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (allowed, limit_info)
        """
        limit_config = self._rate_limit_configs.get(tier, self._rate_limit_configs["default"])
        
        # Initialize counter if needed
        if key not in self._in_memory_counters:
            self._in_memory_counters[key] = {}
        
        # Get current timestamp (minute-based for simplicity)
        now = int(time.time())
        current_minute = now // 60
        
        # Clean up old entries
        window_start_minute = current_minute - (limit_config.window // 60) - 1
        for minute in list(self._in_memory_counters[key].keys()):
            if minute <= window_start_minute:
                del self._in_memory_counters[key][minute]
        
        # Count requests in current window
        request_count = sum(
            count for minute, count in self._in_memory_counters[key].items()
            if minute > window_start_minute
        )
        
        # Increment counter for current minute
        if current_minute not in self._in_memory_counters[key]:
            self._in_memory_counters[key][current_minute] = 0
        self._in_memory_counters[key][current_minute] += 1
        
        # Increment request count to include current request
        request_count += 1
        
        # Calculate remaining requests
        remaining = max(0, limit_config.requests - request_count)
        
        # Determine reset time (simplified for in-memory)
        reset_time = 60 - (now % 60)
        
        # Check if rate limit exceeded
        allowed = request_count <= limit_config.requests
        
        # Limit info
        limit_info = {
            "allowed": allowed,
            "limit": limit_config.requests,
            "remaining": remaining,
            "reset": reset_time,
            "window": limit_config.window
        }
        
        return allowed, limit_info
    
    def check_rate_limit(self, key: str, tier: str = "default") -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a request is allowed under rate limits.
        
        Args:
            key: Rate limit key
            tier: Rate limit tier
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (allowed, limit_info)
        """
        # Use Redis if available, otherwise use in-memory
        if self.redis_client:
            return self._check_redis_limit(key, tier)
        else:
            return self._check_memory_limit(key, tier)


if HAS_FASTAPI:
    class RateLimitMiddleware(BaseHTTPMiddleware):
        """FastAPI middleware for rate limiting."""
        
        def __init__(
            self,
            app: Any,
            limiter: Optional[RateLimiter] = None,
            default_tier: str = "default",
            tier_key_header: str = "X-Rate-Limit-Tier",
            exclude_paths: Optional[List[str]] = None,
            status_code: int = 429,
            error_message: str = "Rate limit exceeded"
        ):
            """
            Initialize rate limit middleware.
            
            Args:
                app: FastAPI application
                limiter: Rate limiter instance
                default_tier: Default rate limit tier
                tier_key_header: Header for specifying rate limit tier
                exclude_paths: Paths to exclude from rate limiting
                status_code: HTTP status code for rate limit exceeded
                error_message: Error message for rate limit exceeded
            """
            super().__init__(app)
            self.limiter = limiter or RateLimiter()
            self.default_tier = default_tier
            self.tier_key_header = tier_key_header
            self.exclude_paths = exclude_paths or []
            self.status_code = status_code
            self.error_message = error_message
        
        async def dispatch(self, request: Request, call_next: Callable) -> Response:
            """
            Dispatch request with rate limiting.
            
            Args:
                request: FastAPI request
                call_next: Next middleware or route handler
                
            Returns:
                Response: HTTP response
            """
            # Skip excluded paths
            for exclude_path in self.exclude_paths:
                if request.url.path.startswith(exclude_path):
                    return await call_next(request)
            
            # Determine rate limit tier
            tier = request.headers.get(self.tier_key_header, self.default_tier)
            
            # Generate rate limit key
            key = RateLimitKey.from_request(request, tier)
            
            # Check rate limit
            allowed, limit_info = self.limiter.check_rate_limit(key, tier)
            
            # Apply rate limit headers to all responses
            response = await call_next(request) if allowed else JSONResponse(
                status_code=self.status_code,
                content={"detail": self.error_message}
            )
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(limit_info["reset"])
            
            if not allowed:
                response.headers["Retry-After"] = str(limit_info["reset"])
            
            return response
    
    def rate_limit_dependency(tier: str = "default") -> Callable:
        """
        Create a dependency for rate limiting specific endpoints.
        
        Args:
            tier: Rate limit tier
            
        Returns:
            Callable: FastAPI dependency
        """
        limiter = RateLimiter()
        
        async def check_rate_limit(request: Request) -> None:
            """
            Check rate limit for request.
            
            Args:
                request: FastAPI request
                
            Raises:
                HTTPException: If rate limit exceeded
            """
            key = RateLimitKey.from_request(request, tier)
            allowed, limit_info = limiter.check_rate_limit(key, tier)
            
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(limit_info["limit"]),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(limit_info["reset"]),
                        "Retry-After": str(limit_info["reset"])
                    }
                )
        
        return Depends(check_rate_limit)


# Usage example with FastAPI:
"""
from fastapi import FastAPI, Depends
from shared.utils.src.api.rate_limiting import RateLimiter, RateLimitMiddleware, rate_limit_dependency

app = FastAPI()

# Apply rate limiting middleware to all routes
limiter = RateLimiter(redis_host="redis-service", redis_db=2)
app.add_middleware(
    RateLimitMiddleware,
    limiter=limiter,
    default_tier="default",
    exclude_paths=["/health", "/metrics"]
)

# Public endpoint with default rate limit
@app.get("/public")
async def public_endpoint():
    return {"message": "Public data"}

# API endpoint with higher rate limit
@app.get("/api/v1/data", dependencies=[rate_limit_dependency("high")])
async def api_endpoint():
    return {"message": "API data"}

# Expensive endpoint with lower rate limit
@app.get("/api/v1/expensive", dependencies=[rate_limit_dependency("low")])
async def expensive_endpoint():
    return {"message": "Expensive operation result"}
"""
