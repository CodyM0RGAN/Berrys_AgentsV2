"""
Shared utilities for the Berrys_AgentsV2 system.

This package contains utilities that can be used across all services in the
system. It provides standardized implementations for common functionality
such as error handling, retry mechanisms, circuit breakers, and more.
"""

# Import and re-export key utilities
from shared.utils.src.exceptions import (
    ServiceAuthenticationError as AuthenticationError,
    ServiceAuthorizationError as AuthorizationError,
    ServiceBadRequestError as BadRequestError,
    ServiceError as BaseServiceException,
    CircuitBreakerOpenError as CircuitBreakerError,
    DatabaseError,
    ServiceInternalError as InternalServerError,
    ServiceNotFoundError as ResourceNotFoundError,
    ServiceUnavailableError,
    ServiceTimeoutError as TimeoutError,
    ValidationError,
)

from shared.utils.src.retry import (
    RetryPolicy,
    MaxRetriesExceededError,
    retry_with_backoff,
    retry_with_backoff_sync,
)

from shared.utils.src.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)

from shared.utils.src.cache_fallback import (
    CacheFallback,
    CacheStrategy,
    CacheEntry,
)

from shared.utils.src.request_id import (
    get_request_id,
    set_request_id,
    generate_request_id,
    RequestIdMiddleware,
    FlaskRequestIdMiddleware,
    RequestIdFilter,
    setup_request_id_logging,
    add_request_id_middleware,
    get_request_id_header,
)

from shared.utils.src.exception_middleware import (
    create_error_response,
    exception_to_http_response,
    ExceptionHandlingMiddleware,
    add_exception_handlers,
)

# Define __all__ to control what gets imported with "from shared.utils.src import *"
__all__ = [
    # Exceptions
    'AuthenticationError',
    'AuthorizationError',
    'BadRequestError',
    'BaseServiceException',
    'CircuitBreakerError',
    'DatabaseError',
    'InternalServerError',
    'ResourceNotFoundError',
    'ServiceUnavailableError',
    'TimeoutError',
    'ValidationError',
    
    # Retry
    'RetryPolicy',
    'MaxRetriesExceededError',
    'retry_with_backoff',
    'retry_with_backoff_sync',
    
    # Circuit Breaker
    'CircuitBreaker',
    'CircuitBreakerConfig',
    'CircuitState',
    
    # Cache Fallback
    'CacheFallback',
    'CacheStrategy',
    'CacheEntry',
    
    # Request ID
    'get_request_id',
    'set_request_id',
    'generate_request_id',
    'RequestIdMiddleware',
    'FlaskRequestIdMiddleware',
    'RequestIdFilter',
    'setup_request_id_logging',
    'add_request_id_middleware',
    'get_request_id_header',
    
    # Exception Middleware
    'create_error_response',
    'exception_to_http_response',
    'ExceptionHandlingMiddleware',
    'add_exception_handlers',
]
