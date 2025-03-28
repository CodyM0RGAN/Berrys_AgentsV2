"""
Circuit breaker implementation for handling service unavailability.

This module provides a circuit breaker implementation that can be used to prevent
cascading failures when services are unavailable. It implements the circuit breaker
pattern as described by Martin Fowler:
https://martinfowler.com/bliki/CircuitBreaker.html
"""
import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar

from shared.utils.src.exceptions import CircuitBreakerError

# Set up logger
logger = logging.getLogger(__name__)

# Type variable for the return type of the operation
T = TypeVar('T')

class CircuitState(Enum):
    """Possible states of a circuit breaker."""
    CLOSED = auto()  # Normal operation, requests are allowed
    OPEN = auto()    # Circuit is open, requests are not allowed
    HALF_OPEN = auto()  # Testing if the service is back online


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    
    failure_threshold: int = 5
    """Number of failures before opening the circuit."""
    
    recovery_timeout: float = 60.0
    """Time in seconds to wait before attempting recovery."""
    
    reset_timeout: float = 300.0
    """Time in seconds after which to reset failure count if no failures occur."""


class CircuitBreaker:
    """
    Implementation of the circuit breaker pattern.
    
    The circuit breaker prevents cascading failures by stopping requests to a
    service that is unavailable. It has three states:
    
    - CLOSED: Normal operation, requests are allowed
    - OPEN: Circuit is open, requests are not allowed
    - HALF_OPEN: Testing if the service is back online
    
    When the circuit is CLOSED, failures are counted. If the failure count
    exceeds the threshold, the circuit is opened. When the circuit is OPEN,
    all requests are rejected without attempting to call the service. After
    a recovery timeout, the circuit transitions to HALF_OPEN and allows a
    single request to test if the service is back online. If the request
    succeeds, the circuit is closed; if it fails, the circuit remains open.
    """
    
    # Global registry of circuit breakers
    _registry: Dict[str, 'CircuitBreaker'] = {}
    
    @classmethod
    def get_or_create(cls, name: str, config: Optional[CircuitBreakerConfig] = None) -> 'CircuitBreaker':
        """
        Get an existing circuit breaker or create a new one.
        
        Args:
            name: Name of the circuit breaker
            config: Configuration for the circuit breaker (only used if creating a new one)
            
        Returns:
            CircuitBreaker instance
        """
        if name not in cls._registry:
            cls._registry[name] = CircuitBreaker(name=name, config=config)
        return cls._registry[name]
    
    @classmethod
    def get_all(cls) -> Dict[str, 'CircuitBreaker']:
        """
        Get all registered circuit breakers.
        
        Returns:
            Dictionary of circuit breakers
        """
        return cls._registry.copy()
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize CircuitBreaker.
        
        Args:
            name: Name of the circuit breaker
            config: Configuration for the circuit breaker
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.last_success_time = 0.0
        self.last_state_change_time = time.time()
        
        # Register this circuit breaker
        self.__class__._registry[name] = self
    
    def record_success(self) -> None:
        """Record a successful operation."""
        self.last_success_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            # If we're in HALF_OPEN state and a request succeeds,
            # close the circuit and reset the failure count
            self._change_state(CircuitState.CLOSED)
            self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            # If we're in CLOSED state and it's been a while since the last failure,
            # reset the failure count
            if (self.last_failure_time > 0 and 
                time.time() - self.last_failure_time > self.config.reset_timeout):
                self.failure_count = 0
    
    def record_failure(self) -> None:
        """Record a failed operation."""
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            # If we're in CLOSED state, increment the failure count
            self.failure_count += 1
            
            # If we've exceeded the threshold, open the circuit
            if self.failure_count >= self.config.failure_threshold:
                self._change_state(CircuitState.OPEN)
        
        elif self.state == CircuitState.HALF_OPEN:
            # If we're in HALF_OPEN state and a request fails,
            # open the circuit again
            self._change_state(CircuitState.OPEN)
    
    def allow_request(self) -> bool:
        """
        Check if a request should be allowed.
        
        Returns:
            True if the request should be allowed, False otherwise
        """
        if self.state == CircuitState.CLOSED:
            # In CLOSED state, always allow requests
            return True
        
        elif self.state == CircuitState.OPEN:
            # In OPEN state, check if the recovery timeout has elapsed
            if time.time() - self.last_state_change_time > self.config.recovery_timeout:
                # If so, transition to HALF_OPEN state
                self._change_state(CircuitState.HALF_OPEN)
                return True
            return False
        
        elif self.state == CircuitState.HALF_OPEN:
            # In HALF_OPEN state, only allow one request at a time
            # This is a simplified implementation; in a real system,
            # you might want to use a semaphore to ensure only one
            # request is allowed at a time
            return True
        
        return False
    
    def _change_state(self, new_state: CircuitState) -> None:
        """
        Change the state of the circuit breaker.
        
        Args:
            new_state: New state
        """
        if self.state != new_state:
            logger.info(f"Circuit breaker '{self.name}' state changed from {self.state.name} to {new_state.name}")
            self.state = new_state
            self.last_state_change_time = time.time()
    
    async def execute(self, operation: Callable[[], Awaitable[T]], operation_name: Optional[str] = None) -> T:
        """
        Execute an operation with circuit breaker protection.
        
        Args:
            operation: Async function to execute
            operation_name: Name of the operation for logging
            
        Returns:
            Result of the operation
            
        Raises:
            CircuitBreakerError: If the circuit is open
            Exception: Any exception raised by the operation
        """
        operation_desc = operation_name or "operation"
        
        if not self.allow_request():
            logger.warning(f"Circuit breaker '{self.name}' is open, rejecting {operation_desc}")
            raise CircuitBreakerError(self.name)
        
        try:
            result = await operation()
            self.record_success()
            return result
        except Exception as e:
            logger.error(f"Operation {operation_desc} failed with circuit breaker '{self.name}': {str(e)}")
            self.record_failure()
            raise
    
    def execute_sync(self, operation: Callable[[], T], operation_name: Optional[str] = None) -> T:
        """
        Execute a synchronous operation with circuit breaker protection.
        
        Args:
            operation: Function to execute
            operation_name: Name of the operation for logging
            
        Returns:
            Result of the operation
            
        Raises:
            CircuitBreakerError: If the circuit is open
            Exception: Any exception raised by the operation
        """
        operation_desc = operation_name or "operation"
        
        if not self.allow_request():
            logger.warning(f"Circuit breaker '{self.name}' is open, rejecting {operation_desc}")
            raise CircuitBreakerError(self.name)
        
        try:
            result = operation()
            self.record_success()
            return result
        except Exception as e:
            logger.error(f"Operation {operation_desc} failed with circuit breaker '{self.name}': {str(e)}")
            self.record_failure()
            raise
