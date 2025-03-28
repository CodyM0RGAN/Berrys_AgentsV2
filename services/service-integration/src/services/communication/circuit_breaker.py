"""
Circuit Breaker implementation for service resilience.

This module implements the Circuit Breaker pattern to prevent cascading failures
in distributed systems by stopping requests to failing services until they recover.
"""
from enum import Enum
from typing import Callable, Any, Dict, TypeVar, Generic, Awaitable, Optional
import time
import asyncio
import logging
from datetime import datetime, timedelta

T = TypeVar('T')


class CircuitState(str, Enum):
    """States of a circuit breaker."""
    CLOSED = "CLOSED"     # Normal operation, requests pass through
    OPEN = "OPEN"         # Circuit is tripped, all requests fail fast
    HALF_OPEN = "HALF_OPEN"  # Testing if service is recovered


class CircuitOpenError(Exception):
    """Exception raised when the circuit is open."""
    pass


class CircuitBreaker:
    """
    Circuit Breaker implementation.
    
    This class implements the Circuit Breaker pattern for improving resilience
    in distributed systems by preventing requests to failing services until
    they recover.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout: int = 30,
        half_open_max_calls: int = 3
    ):
        """
        Initialize the circuit breaker.
        
        Args:
            name: Name of the circuit breaker (typically the service name)
            failure_threshold: Number of failures before opening the circuit
            reset_timeout: Time in seconds before trying to close the circuit again
            half_open_max_calls: Maximum number of calls in half-open state
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_call_count = 0
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger(f"circuit_breaker.{name}")
        
    async def execute(self, operation: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        """
        Execute an operation with circuit breaker protection.
        
        Args:
            operation: Async function to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            The result of the operation
            
        Raises:
            CircuitOpenError: If the circuit is open
            Exception: Any exception raised by the operation
        """
        await self._check_state_transition()
        
        async with self.lock:
            if self.state == CircuitState.OPEN:
                self.logger.warning(f"Circuit {self.name} is OPEN, failing fast")
                raise CircuitOpenError(f"Circuit {self.name} is open")
                
            if self.state == CircuitState.HALF_OPEN and self.half_open_call_count >= self.half_open_max_calls:
                self.logger.warning(f"Circuit {self.name} is HALF_OPEN but max test calls reached")
                raise CircuitOpenError(f"Circuit {self.name} is half-open and at test call limit")
                
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_call_count += 1
                self.logger.info(f"Circuit {self.name} is HALF_OPEN, test call {self.half_open_call_count}/{self.half_open_max_calls}")
                
        try:
            start_time = time.time()
            result = await operation(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Operation succeeded
            async with self.lock:
                if self.state == CircuitState.HALF_OPEN:
                    self.logger.info(f"Circuit {self.name} test call succeeded, closing circuit")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.half_open_call_count = 0
                elif self.state == CircuitState.CLOSED:
                    # Reset failure count on success
                    self.failure_count = 0
                    
            self.logger.debug(f"Circuit {self.name} call succeeded in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            # Operation failed
            async with self.lock:
                self.last_failure_time = datetime.now()
                
                if self.state == CircuitState.HALF_OPEN:
                    self.logger.warning(f"Circuit {self.name} test call failed, reopening circuit: {str(e)}")
                    self.state = CircuitState.OPEN
                    self.half_open_call_count = 0
                    
                elif self.state == CircuitState.CLOSED:
                    self.failure_count += 1
                    self.logger.warning(f"Circuit {self.name} failure count: {self.failure_count}/{self.failure_threshold}: {str(e)}")
                    
                    if self.failure_count >= self.failure_threshold:
                        self.logger.error(f"Circuit {self.name} tripped OPEN: failure threshold reached")
                        self.state = CircuitState.OPEN
            
            # Re-raise the original exception
            raise
            
    async def _check_state_transition(self):
        """Check if state should transition from OPEN to HALF_OPEN."""
        if self.state != CircuitState.OPEN or not self.last_failure_time:
            return
            
        # Check if reset timeout has passed
        time_since_failure = datetime.now() - self.last_failure_time
        if time_since_failure >= timedelta(seconds=self.reset_timeout):
            async with self.lock:
                if self.state == CircuitState.OPEN:  # Check again under the lock
                    self.logger.info(f"Circuit {self.name} transitioning from OPEN to HALF_OPEN, {time_since_failure.total_seconds():.2f}s since last failure")
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_call_count = 0
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the circuit breaker.
        
        Returns:
            Dict with the current state information
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "half_open_call_count": self.half_open_call_count,
            "failure_threshold": self.failure_threshold,
            "reset_timeout": self.reset_timeout,
            "half_open_max_calls": self.half_open_max_calls
        }


class CircuitBreakerRegistry:
    """
    Registry for circuit breakers.
    
    This class maintains a registry of circuit breakers by name to avoid
    creating multiple instances for the same service.
    """
    
    _circuit_breakers: Dict[str, CircuitBreaker] = {}
    _logger = logging.getLogger("circuit_breaker.registry")
    
    @classmethod
    def get_circuit_breaker(
        cls,
        name: str,
        failure_threshold: int = 5,
        reset_timeout: int = 30,
        half_open_max_calls: int = 3
    ) -> CircuitBreaker:
        """
        Get or create a circuit breaker by name.
        
        Args:
            name: Name of the circuit breaker
            failure_threshold: Number of failures before opening the circuit
            reset_timeout: Time in seconds before trying to close the circuit again
            half_open_max_calls: Maximum number of calls in half-open state
            
        Returns:
            A CircuitBreaker instance
        """
        if name not in cls._circuit_breakers:
            cls._logger.info(f"Creating new circuit breaker: {name}")
            cls._circuit_breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                reset_timeout=reset_timeout,
                half_open_max_calls=half_open_max_calls
            )
        
        return cls._circuit_breakers[name]
    
    @classmethod
    def get_all_circuit_breakers(cls) -> Dict[str, CircuitBreaker]:
        """
        Get all registered circuit breakers.
        
        Returns:
            Dict of circuit breakers by name
        """
        return cls._circuit_breakers.copy()
    
    @classmethod
    def reset_all(cls) -> None:
        """Reset all circuit breakers to their initial state."""
        cls._circuit_breakers.clear()
        cls._logger.info("All circuit breakers reset")
