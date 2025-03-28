"""
Retry utility with exponential backoff for handling transient failures.

This module provides utilities for retrying operations that may fail due to
transient issues such as network connectivity problems or service unavailability.
It implements exponential backoff with jitter to prevent the "thundering herd"
problem when multiple clients retry at the same time.
"""
import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, List, Optional, Type, TypeVar, Union

# Set up logger
logger = logging.getLogger(__name__)

# Type variable for the return type of the operation
T = TypeVar('T')

@dataclass
class RetryPolicy:
    """Configuration for retry behavior."""
    
    max_retries: int = 3
    """Maximum number of retry attempts."""
    
    base_delay: float = 0.5
    """Base delay in seconds between retries."""
    
    max_delay: float = 30.0
    """Maximum delay in seconds between retries."""
    
    retry_exceptions: List[Type[Exception]] = field(default_factory=list)
    """List of exception types that should trigger a retry."""
    
    jitter_factor: float = 0.1
    """Factor to apply random jitter to delay (0.0 to 1.0)."""


class MaxRetriesExceededError(Exception):
    """Exception raised when maximum retries are exceeded."""
    
    def __init__(self, attempts: int, last_error: Optional[Exception] = None):
        """
        Initialize MaxRetriesExceededError.
        
        Args:
            attempts: Number of attempts made
            last_error: Last exception that occurred
        """
        self.attempts = attempts
        self.last_error = last_error
        message = f"Operation failed after {attempts} attempts"
        if last_error:
            message += f": {str(last_error)}"
        super().__init__(message)


async def retry_with_backoff(
    operation: Callable[[], Awaitable[T]],
    policy: RetryPolicy,
    operation_name: Optional[str] = None,
    request_id: Optional[str] = None
) -> T:
    """
    Retry an asynchronous operation with exponential backoff.
    
    Args:
        operation: Async function to retry
        policy: Retry policy configuration
        operation_name: Name of the operation for logging
        request_id: Request ID for logging
        
    Returns:
        Result of the operation
        
    Raises:
        MaxRetriesExceededError: If maximum retries are exceeded
    """
    attempt = 0
    last_error = None
    operation_desc = operation_name or "operation"
    log_context = {"request_id": request_id} if request_id else {}
    
    while attempt <= policy.max_retries:
        try:
            # Attempt the operation
            if attempt > 0:
                logger.info(
                    f"Retry attempt {attempt}/{policy.max_retries} for {operation_desc}",
                    extra=log_context
                )
            
            return await operation()
        
        except Exception as e:
            attempt += 1
            last_error = e
            
            # Check if the exception should trigger a retry
            should_retry = False
            if not policy.retry_exceptions:
                # If no specific exceptions are specified, retry on any exception
                should_retry = True
            else:
                # Otherwise, only retry on specified exception types
                for exception_type in policy.retry_exceptions:
                    if isinstance(e, exception_type):
                        should_retry = True
                        break
            
            if not should_retry or attempt > policy.max_retries:
                # Don't retry if the exception is not in the retry list
                # or if we've exceeded the maximum number of retries
                logger.error(
                    f"Failed to execute {operation_desc} after {attempt} attempts: {str(e)}",
                    extra=log_context,
                    exc_info=True
                )
                raise MaxRetriesExceededError(attempt, last_error)
            
            # Calculate delay with exponential backoff and jitter
            delay = min(
                policy.base_delay * (2 ** (attempt - 1)),
                policy.max_delay
            )
            
            # Add jitter to prevent thundering herd
            jitter = random.uniform(-policy.jitter_factor, policy.jitter_factor)
            delay = delay * (1 + jitter)
            
            logger.warning(
                f"Attempt {attempt}/{policy.max_retries} for {operation_desc} failed: {str(e)}. "
                f"Retrying in {delay:.2f} seconds...",
                extra=log_context
            )
            
            # Wait before retrying
            await asyncio.sleep(delay)
    
    # This should never be reached due to the raise in the loop,
    # but it's here for completeness
    raise MaxRetriesExceededError(attempt, last_error)


def retry_with_backoff_sync(
    operation: Callable[[], T],
    policy: RetryPolicy,
    operation_name: Optional[str] = None,
    request_id: Optional[str] = None
) -> T:
    """
    Retry a synchronous operation with exponential backoff.
    
    Args:
        operation: Function to retry
        policy: Retry policy configuration
        operation_name: Name of the operation for logging
        request_id: Request ID for logging
        
    Returns:
        Result of the operation
        
    Raises:
        MaxRetriesExceededError: If maximum retries are exceeded
    """
    attempt = 0
    last_error = None
    operation_desc = operation_name or "operation"
    log_context = {"request_id": request_id} if request_id else {}
    
    while attempt <= policy.max_retries:
        try:
            # Attempt the operation
            if attempt > 0:
                logger.info(
                    f"Retry attempt {attempt}/{policy.max_retries} for {operation_desc}",
                    extra=log_context
                )
            
            return operation()
        
        except Exception as e:
            attempt += 1
            last_error = e
            
            # Check if the exception should trigger a retry
            should_retry = False
            if not policy.retry_exceptions:
                # If no specific exceptions are specified, retry on any exception
                should_retry = True
            else:
                # Otherwise, only retry on specified exception types
                for exception_type in policy.retry_exceptions:
                    if isinstance(e, exception_type):
                        should_retry = True
                        break
            
            if not should_retry or attempt > policy.max_retries:
                # Don't retry if the exception is not in the retry list
                # or if we've exceeded the maximum number of retries
                logger.error(
                    f"Failed to execute {operation_desc} after {attempt} attempts: {str(e)}",
                    extra=log_context,
                    exc_info=True
                )
                raise MaxRetriesExceededError(attempt, last_error)
            
            # Calculate delay with exponential backoff and jitter
            delay = min(
                policy.base_delay * (2 ** (attempt - 1)),
                policy.max_delay
            )
            
            # Add jitter to prevent thundering herd
            jitter = random.uniform(-policy.jitter_factor, policy.jitter_factor)
            delay = delay * (1 + jitter)
            
            logger.warning(
                f"Attempt {attempt}/{policy.max_retries} for {operation_desc} failed: {str(e)}. "
                f"Retrying in {delay:.2f} seconds...",
                extra=log_context
            )
            
            # Wait before retrying
            time.sleep(delay)
    
    # This should never be reached due to the raise in the loop,
    # but it's here for completeness
    raise MaxRetriesExceededError(attempt, last_error)
