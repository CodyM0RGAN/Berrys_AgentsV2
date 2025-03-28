# Error Handling Best Practices

> **Draft-of-Thought Documentation**: This document provides best practices for error handling across services in the Berrys_AgentsV2 system. It covers standardized error responses, error propagation, retry mechanisms, circuit breakers, and fallback strategies.

## Overview

Effective error handling is critical for building reliable and resilient distributed systems. This guide outlines best practices for handling errors across service boundaries in the Berrys_AgentsV2 system.

The key principles of our error handling strategy are:

1. **Consistency**: Use standardized error responses across all services
2. **Traceability**: Include request IDs and context in all error messages
3. **Resilience**: Implement retry mechanisms and circuit breakers
4. **Graceful Degradation**: Provide fallback mechanisms when services are unavailable
5. **Transparency**: Log detailed error information for troubleshooting

## Standardized Error Responses

All services should use the standardized error response models defined in `shared/models/src/api/errors.py`. These models ensure consistent error handling across the system.

### Error Response Structure

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field1": "Error details for field1",
      "field2": "Error details for field2"
    },
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-03-26T19:45:00Z"
  }
}
```

### Common Error Types

| Error Type | HTTP Status | Error Code | Use Case |
|------------|-------------|------------|----------|
| Validation Error | 400 | VALIDATION_ERROR | Invalid input data |
| Resource Not Found | 404 | RESOURCE_NOT_FOUND | Requested resource doesn't exist |
| Unauthorized | 401 | UNAUTHORIZED | Authentication required |
| Forbidden | 403 | FORBIDDEN | Permission denied |
| Conflict | 409 | CONFLICT | Resource conflict (e.g., duplicate) |
| Service Unavailable | 503 | SERVICE_UNAVAILABLE | Service is temporarily unavailable |
| Internal Server Error | 500 | INTERNAL_SERVER_ERROR | Unexpected server error |

### Implementation in FastAPI

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from shared.models.src.api.errors import (
    create_error_response,
    create_validation_error_response,
    create_resource_not_found_response
)
from shared.utils.src.request_id import get_request_id

app = FastAPI()

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = get_request_id(request)
    
    if exc.status_code == 404:
        error_response = create_resource_not_found_response(
            resource_type="Resource",
            resource_id=request.path_params.get("id", "unknown"),
            request_id=request_id
        )
    elif exc.status_code == 422:
        error_response = create_validation_error_response(
            validation_errors=exc.detail,
            request_id=request_id
        )
    else:
        error_response = create_error_response(
            code="API_ERROR",
            message=str(exc.detail),
            details={"status_code": exc.status_code},
            request_id=request_id
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    request_id = get_request_id(request)
    
    # Log the exception with request ID
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={"request_id": request_id},
        exc_info=True
    )
    
    # Return a standardized error response
    error_response = create_error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details={"error": str(exc)},
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response
    )
```

## Error Propagation

When propagating errors across service boundaries, follow these guidelines:

1. **Translate Errors**: Convert internal exceptions to appropriate HTTP status codes and error responses
2. **Preserve Context**: Include relevant context information in error details
3. **Include Request ID**: Always propagate the request ID for tracing
4. **Avoid Leaking Implementation Details**: Don't expose sensitive internal details in error messages

### Example: Error Translation

```python
async def get_project(project_id: str, request_id: str = None):
    try:
        # Call the project service
        return await project_service.get_project(project_id)
    except HTTPException as e:
        if e.status_code == 404:
            # Translate to ResourceNotFoundError
            raise ResourceNotFoundError(f"Project {project_id} not found")
        elif e.status_code >= 500:
            # Translate to ServiceUnavailableError
            raise ServiceUnavailableError(f"Project service unavailable: {str(e)}")
        # Re-raise other HTTP exceptions
        raise
    except Exception as e:
        # Log the exception with request ID
        logger.error(
            f"Error getting project {project_id}: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        # Translate to ServiceUnavailableError
        raise ServiceUnavailableError(f"Failed to get project: {str(e)}")
```

## Retry Mechanisms

Use the retry utility in `shared/utils/src/retry.py` to handle transient failures in service calls.

### Retry Policies

Define retry policies based on the type of operation:

| Operation Type | Max Retries | Base Delay | Max Delay | Jitter |
|----------------|-------------|------------|-----------|--------|
| Read Operations | 3 | 0.5s | 4s | 10% |
| Write Operations | 2 | 1s | 4s | 10% |
| Critical Operations | 5 | 0.2s | 8s | 10% |
| Background Tasks | 10 | 1s | 60s | 10% |

### Example: Retry with Exponential Backoff

```python
from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError

async def get_data_with_retry(data_id: str, request_id: str = None):
    # Define retry policy
    policy = RetryPolicy(
        max_retries=3,
        base_delay=0.5,
        max_delay=4.0,
        retry_exceptions=[ServiceUnavailableError, ConnectionError],
        retry_on_result=lambda result: result.get("status") == "ERROR"
    )
    
    try:
        # Execute with retry
        return await retry_with_backoff(
            lambda: data_service.get_data(data_id),
            policy=policy,
            request_id=request_id
        )
    except MaxRetriesExceededError as e:
        # Log the failure
        logger.error(
            f"Max retries exceeded for data {data_id}",
            extra={"request_id": request_id, "attempts": e.attempts}
        )
        # Raise appropriate error
        raise ServiceUnavailableError(f"Failed to get data after {e.attempts} attempts")
```

### Using Retry Decorators

For frequently used operations, use the retry decorators:

```python
from shared.utils.src.retry import retryable_read_operation

@retryable_read_operation
async def get_user(user_id: str, request_id: str = None):
    return await user_service.get_user(user_id)
```

## Circuit Breakers

Use the circuit breaker utility in `shared/utils/src/circuit_breaker.py` to prevent cascading failures when services are unavailable.

### Circuit Breaker States

1. **Closed**: Normal operation, requests are allowed through
2. **Open**: Circuit is tripped, requests are blocked
3. **Half-Open**: Testing if the service is back online

### Example: Circuit Breaker Implementation

```python
from shared.utils.src.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException

# Create a circuit breaker
user_service_cb = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30,
    name="user-service"
)

async def get_user(user_id: str):
    try:
        # Execute operation with circuit breaker protection
        return await user_service_cb.execute(
            lambda: user_service.get_user(user_id)
        )
    except CircuitBreakerOpenException:
        # Handle the case where the circuit is open
        logger.warning(f"Circuit breaker open for user service")
        return fallback_user(user_id)
```

### Circuit Breaker Registry

Use the global circuit breaker registry to manage and monitor circuit breakers:

```python
from shared.utils.src.circuit_breaker import registry

# Get a circuit breaker from the registry
cb = registry.get_or_create(
    name="user-service",
    failure_threshold=5,
    recovery_timeout=30
)

# Get metrics for all circuit breakers
metrics = registry.get_all_metrics()
```

## Fallback Mechanisms

Use the cache fallback utility in `shared/utils/src/cache_fallback.py` to provide resilience when services are unavailable.

### Caching Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| CACHE_FIRST | Always return cached data if available | Non-critical data that doesn't need to be fresh |
| STALE_WHILE_REVALIDATE | Return stale data while fetching fresh data | UI components that can show stale data while refreshing |
| CACHE_OR_FETCH | Try cache first, fetch if not in cache | Standard read operations |
| FETCH_OR_CACHE | Try fetch first, use cache if fetch fails | Operations that need fresh data but can fall back to cache |

### Example: Cache Fallback Implementation

```python
from shared.utils.src.cache_fallback import CacheFallback, CacheStrategy

# Create a cache fallback instance
cache = CacheFallback(
    cache_key_prefix="user",
    ttl=3600,  # 1 hour
    strategy=CacheStrategy.STALE_WHILE_REVALIDATE
)

async def get_user_with_fallback(user_id: str, request_id: str = None):
    cache_key = f"user:{user_id}"
    
    try:
        # Try to get from cache or service
        user, from_cache = await cache.get_or_fetch(
            cache_key=cache_key,
            fetch_func=lambda: user_service.get_user(user_id),
            request_id=request_id
        )
        return user
    except ServiceUnavailableError:
        # Service is unavailable, try to get from cache
        cached_user = await cache.get(cache_key)
        if cached_user:
            logger.warning(
                f"Service unavailable, using cached user {user_id}",
                extra={"request_id": request_id}
            )
            return cached_user
        # No cached data available
        raise
```

### Using Cache Decorators

For frequently used operations, use the cache decorators:

```python
from shared.utils.src.cache_fallback import cached, CacheFallback, CacheStrategy

cache = CacheFallback(
    cache_key_prefix="user",
    ttl=3600,
    strategy=CacheStrategy.CACHE_OR_FETCH
)

@cached(
    cache_key_func=lambda user_id, **kwargs: f"user:{user_id}",
    cache_fallback=cache
)
async def get_user(user_id: str, request_id: str = None):
    return await user_service.get_user(user_id)
```

## Request ID Propagation

Use the request ID middleware and utilities in `shared/utils/src/request_id.py` to ensure consistent request tracking across services.

### Example: Request ID Propagation

```python
from fastapi import FastAPI, Request
from shared.utils.src.request_id import RequestIdMiddleware, get_request_id, propagate_request_id
import httpx

app = FastAPI()
app.add_middleware(RequestIdMiddleware)

@app.get("/users/{user_id}/projects")
async def get_user_projects(user_id: str, request: Request):
    # Get the request ID from the request
    request_id = get_request_id(request)
    
    # Log with request ID
    logger.info(
        f"Getting projects for user {user_id}",
        extra={"request_id": request_id}
    )
    
    # Propagate request ID to downstream service
    headers = propagate_request_id({}, request)
    
    # Make request to downstream service
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://project-service/projects?user_id={user_id}",
            headers=headers
        )
    
    return response.json()
```

## Logging Best Practices

Always include the request ID in log messages for traceability:

```python
from shared.utils.src.request_id import request_id_logging_context

# Create logging context with request ID
log_context = request_id_logging_context(request_id)

# Log with request ID
logger.info(
    f"Processing request for user {user_id}",
    extra=log_context
)

# Log error with request ID
logger.error(
    f"Error processing request: {str(e)}",
    extra=log_context,
    exc_info=True
)
```

## Putting It All Together

The example below demonstrates how to combine all these error handling techniques:

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from shared.utils.src.request_id import RequestIdMiddleware, get_request_id
from shared.utils.src.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from shared.utils.src.retry import retry_with_backoff, RetryPolicy, MaxRetriesExceededError
from shared.utils.src.cache_fallback import CacheFallback, CacheStrategy
from shared.models.src.api.errors import (
    create_error_response,
    create_resource_not_found_response,
    create_service_unavailable_response
)

app = FastAPI()
app.add_middleware(RequestIdMiddleware)

# Create circuit breaker
user_service_cb = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30,
    name="user-service"
)

# Create cache fallback
user_cache = CacheFallback(
    cache_key_prefix="user",
    ttl=3600,
    strategy=CacheStrategy.STALE_WHILE_REVALIDATE
)

@app.get("/users/{user_id}")
async def get_user(user_id: str, request: Request):
    request_id = get_request_id(request)
    log_context = {"request_id": request_id, "user_id": user_id}
    
    try:
        # Define retry policy
        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError, ConnectionError]
        )
        
        # Define the operation to execute
        async def get_user_operation():
            try:
                return await user_service.get_user(user_id)
            except HTTPException as e:
                if e.status_code == 404:
                    raise ResourceNotFoundError(f"User {user_id} not found")
                elif e.status_code >= 500:
                    raise ServiceUnavailableError(f"User service unavailable: {str(e)}")
                raise
        
        # Try to get from cache or service with retry and circuit breaker
        cache_key = f"user:{user_id}"
        
        try:
            # Try to get from cache or service
            user, from_cache = await user_cache.get_or_fetch(
                cache_key=cache_key,
                fetch_func=lambda: user_service_cb.execute(
                    lambda: retry_with_backoff(
                        operation=get_user_operation,
                        policy=retry_policy,
                        request_id=request_id
                    )
                ),
                request_id=request_id
            )
            
            if from_cache:
                logger.info(f"Retrieved user {user_id} from cache", extra=log_context)
            else:
                logger.info(f"Retrieved user {user_id} from service", extra=log_context)
                
            return user
        except (ServiceUnavailableError, CircuitBreakerOpenException, MaxRetriesExceededError) as e:
            # Service is unavailable, try to get from cache
            cached_user = await user_cache.get(cache_key)
            
            if cached_user:
                logger.warning(
                    f"Service unavailable, using cached user {user_id}",
                    extra=log_context
                )
                return cached_user
                
            # No cached data available
            logger.error(
                f"Service unavailable and no cached data for user {user_id}",
                extra=log_context
            )
            
            # Return service unavailable response
            error_response = create_service_unavailable_response(
                service_name="User Service",
                message=str(e),
                request_id=request_id
            )
            return JSONResponse(status_code=503, content=error_response)
        except ResourceNotFoundError:
            # Return 404 response
            error_response = create_resource_not_found_response(
                resource_type="User",
                resource_id=user_id,
                request_id=request_id
            )
            return JSONResponse(status_code=404, content=error_response)
    except Exception as e:
        # Log unexpected errors
        logger.error(
            f"Unexpected error: {str(e)}",
            extra=log_context,
            exc_info=True
        )
        
        # Return 500 response
        error_response = create_error_response(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            details={"error": str(e)},
            request_id=request_id
        )
        return JSONResponse(status_code=500, content=error_response)
```

## Common Error Handling Patterns

### 1. Service Client Pattern

Create service clients that handle error translation and retry logic:

```python
class UserServiceClient:
    def __init__(self):
        self.base_url = "http://user-service:8000"
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30,
            name="user-service"
        )
        self.cache = CacheFallback(
            cache_key_prefix="user",
            ttl=3600,
            strategy=CacheStrategy.STALE_WHILE_REVALIDATE
        )
    
    async def get_user(self, user_id: str, request_id: str = None):
        cache_key = f"user:{user_id}"
        log_context = {"request_id": request_id, "user_id": user_id}
        
        # Define retry policy
        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[HTTPException]
        )
        
        # Define the operation to execute
        async def operation():
            headers = {"X-Request-ID": request_id} if request_id else {}
            
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(
                        f"{self.base_url}/users/{user_id}",
                        headers=headers
                    )
                    
                    if response.status_code == 404:
                        raise ResourceNotFoundError(f"User {user_id} not found")
                    elif response.status_code >= 500:
                        raise ServiceUnavailableError(f"User service unavailable: {response.text}")
                    
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPError as e:
                    raise ServiceUnavailableError(f"HTTP error: {str(e)}")
        
        try:
            # Try to get from cache or service
            user, from_cache = await self.cache.get_or_fetch(
                cache_key=cache_key,
                fetch_func=lambda: self.circuit_breaker.execute(
                    lambda: retry_with_backoff(
                        operation=operation,
                        policy=retry_policy,
                        request_id=request_id
                    )
                ),
                request_id=request_id
            )
            return user
        except (ServiceUnavailableError, CircuitBreakerOpenException) as e:
            # Service is unavailable, try to get from cache
            cached_user = await self.cache.get(cache_key)
            if cached_user:
                logger.warning(
                    f"Service unavailable, using cached user {user_id}",
                    extra=log_context
                )
                return cached_user
            # No cached data available
            raise ServiceUnavailableError(f"User service unavailable and no cached data available")
```

### 2. Middleware Pattern

Use middleware to handle common error handling tasks:

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi.responses import JSONResponse
from shared.models.src.api.errors import create_error_response

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = get_request_id(request)
        
        try:
            # Process the request
            response = await call_next(request)
            return response
        except ResourceNotFoundError as e:
            # Handle resource not found errors
            error_response = create_resource_not_found_response(
                resource_type="Resource",
                resource_id=request.path_params.get("id", "unknown"),
                message=str(e),
                request_id=request_id
            )
            return JSONResponse(status_code=404, content=error_response)
        except ServiceUnavailableError as e:
            # Handle service unavailable errors
            error_response = create_service_unavailable_response(
                service_name="Service",
                message=str(e),
                request_id=request_id
            )
            return JSONResponse(status_code=503, content=error_response)
        except Exception as e:
            # Log unexpected errors
            logger.error(
                f"Unexpected error: {str(e)}",
                extra={"request_id": request_id},
                exc_info=True
            )
            
            # Return 500 response
            error_response = create_error_response(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
                details={"error": str(e)},
                request_id=request_id
            )
            return JSONResponse(status_code=500, content=error_response)
```

## Conclusion

By following these error handling best practices, you can build more reliable and resilient services that gracefully handle failures and provide a better experience for users.

Remember the key principles:

1. **Consistency**: Use standardized error responses
2. **Traceability**: Include request IDs in all error messages
3. **Resilience**: Implement retry mechanisms and circuit breakers
4. **Graceful Degradation**: Provide fallback mechanisms
5. **Transparency**: Log detailed error information

For a complete example of these error handling techniques, see the [Cross-Service Communication Example](examples/cross-service-communication-example.py).

## Related Documentation

- [Cross-Service Communication Improvements](cross-service-communication-improvements.md)
- [Entity Representation Alignment](entity-representation-alignment.md)
- [Adapter Usage Examples](adapter-usage-examples.md)
- [Troubleshooting Guide](troubleshooting-guide.md)
