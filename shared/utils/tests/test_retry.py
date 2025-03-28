"""
Tests for the retry utility.

This module contains tests for the retry utility in shared/utils/src/retry.py.
"""
import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from shared.utils.src.retry import (
    RetryPolicy,
    MaxRetriesExceededError,
    retry_with_backoff,
    retry_with_backoff_sync
)


class TestRetryPolicy(unittest.TestCase):
    """Test cases for RetryPolicy."""
    
    def test_default_values(self):
        """Test default values for RetryPolicy."""
        policy = RetryPolicy()
        self.assertEqual(policy.max_retries, 3)
        self.assertEqual(policy.base_delay, 0.5)
        self.assertEqual(policy.max_delay, 30.0)
        self.assertEqual(policy.retry_exceptions, [])
        self.assertEqual(policy.jitter_factor, 0.1)
    
    def test_custom_values(self):
        """Test custom values for RetryPolicy."""
        policy = RetryPolicy(
            max_retries=5,
            base_delay=1.0,
            max_delay=10.0,
            retry_exceptions=[ValueError, TypeError],
            jitter_factor=0.2
        )
        self.assertEqual(policy.max_retries, 5)
        self.assertEqual(policy.base_delay, 1.0)
        self.assertEqual(policy.max_delay, 10.0)
        self.assertEqual(policy.retry_exceptions, [ValueError, TypeError])
        self.assertEqual(policy.jitter_factor, 0.2)


class TestMaxRetriesExceededError(unittest.TestCase):
    """Test cases for MaxRetriesExceededError."""
    
    def test_init_without_last_error(self):
        """Test initialization without last_error."""
        error = MaxRetriesExceededError(attempts=3)
        self.assertEqual(error.attempts, 3)
        self.assertIsNone(error.last_error)
        self.assertEqual(str(error), "Operation failed after 3 attempts")
    
    def test_init_with_last_error(self):
        """Test initialization with last_error."""
        last_error = ValueError("Invalid value")
        error = MaxRetriesExceededError(attempts=3, last_error=last_error)
        self.assertEqual(error.attempts, 3)
        self.assertEqual(error.last_error, last_error)
        self.assertEqual(str(error), "Operation failed after 3 attempts: Invalid value")


class TestRetryWithBackoff(unittest.IsolatedAsyncioTestCase):
    """Test cases for retry_with_backoff."""
    
    async def test_success_first_attempt(self):
        """Test successful operation on first attempt."""
        # Mock operation that succeeds
        mock_operation = AsyncMock(return_value="success")
        
        # Create retry policy
        policy = RetryPolicy(max_retries=3)
        
        # Call retry_with_backoff
        result = await retry_with_backoff(mock_operation, policy, "test_operation")
        
        # Verify operation was called once
        mock_operation.assert_called_once()
        
        # Verify result
        self.assertEqual(result, "success")
    
    async def test_success_after_retry(self):
        """Test successful operation after retry."""
        # Mock operation that fails once then succeeds
        mock_operation = AsyncMock(side_effect=[ValueError("Error"), "success"])
        
        # Create retry policy
        policy = RetryPolicy(max_retries=3)
        
        # Call retry_with_backoff
        result = await retry_with_backoff(mock_operation, policy, "test_operation")
        
        # Verify operation was called twice
        self.assertEqual(mock_operation.call_count, 2)
        
        # Verify result
        self.assertEqual(result, "success")
    
    async def test_max_retries_exceeded(self):
        """Test operation that exceeds max retries."""
        # Mock operation that always fails
        error = ValueError("Error")
        mock_operation = AsyncMock(side_effect=error)
        
        # Create retry policy
        policy = RetryPolicy(max_retries=2)
        
        # Call retry_with_backoff and verify it raises MaxRetriesExceededError
        with self.assertRaises(MaxRetriesExceededError) as context:
            await retry_with_backoff(mock_operation, policy, "test_operation")
        
        # Verify operation was called max_retries + 1 times
        self.assertEqual(mock_operation.call_count, 3)
        
        # Verify error details
        self.assertEqual(context.exception.attempts, 3)
        self.assertEqual(context.exception.last_error, error)
    
    async def test_retry_specific_exceptions(self):
        """Test retry with specific exceptions."""
        # Mock operation that raises different exceptions
        mock_operation = AsyncMock(side_effect=[
            ValueError("Error"),  # Should retry
            TypeError("Error"),   # Should not retry
            "success"
        ])
        
        # Create retry policy with specific retry exceptions
        policy = RetryPolicy(max_retries=3, retry_exceptions=[ValueError])
        
        # Call retry_with_backoff and verify it raises TypeError
        with self.assertRaises(MaxRetriesExceededError) as context:
            await retry_with_backoff(mock_operation, policy, "test_operation")
        
        # Verify operation was called twice (initial + 1 retry)
        self.assertEqual(mock_operation.call_count, 2)
        
        # Verify error details
        self.assertEqual(context.exception.attempts, 2)
        self.assertIsInstance(context.exception.last_error, TypeError)
    
    @patch("asyncio.sleep")
    async def test_backoff_delay(self, mock_sleep):
        """Test backoff delay calculation."""
        # Mock operation that fails multiple times
        mock_operation = AsyncMock(side_effect=[
            ValueError("Error 1"),
            ValueError("Error 2"),
            ValueError("Error 3"),
            "success"
        ])
        
        # Create retry policy with no jitter
        policy = RetryPolicy(
            max_retries=3,
            base_delay=1.0,
            max_delay=10.0,
            jitter_factor=0.0
        )
        
        # Call retry_with_backoff
        result = await retry_with_backoff(mock_operation, policy, "test_operation")
        
        # Verify operation was called 4 times
        self.assertEqual(mock_operation.call_count, 4)
        
        # Verify sleep was called with expected delays
        mock_sleep.assert_any_call(1.0)  # First retry: base_delay * (2^0)
        mock_sleep.assert_any_call(2.0)  # Second retry: base_delay * (2^1)
        mock_sleep.assert_any_call(4.0)  # Third retry: base_delay * (2^2)
        
        # Verify result
        self.assertEqual(result, "success")
    
    @patch("asyncio.sleep")
    async def test_max_delay(self, mock_sleep):
        """Test maximum delay cap."""
        # Mock operation that fails multiple times
        mock_operation = AsyncMock(side_effect=[
            ValueError("Error 1"),
            ValueError("Error 2"),
            ValueError("Error 3"),
            "success"
        ])
        
        # Create retry policy with low max_delay
        policy = RetryPolicy(
            max_retries=3,
            base_delay=1.0,
            max_delay=1.5,  # Cap delay at 1.5
            jitter_factor=0.0
        )
        
        # Call retry_with_backoff
        result = await retry_with_backoff(mock_operation, policy, "test_operation")
        
        # Verify operation was called 4 times
        self.assertEqual(mock_operation.call_count, 4)
        
        # Verify sleep was called with expected delays
        mock_sleep.assert_any_call(1.0)  # First retry: base_delay * (2^0)
        mock_sleep.assert_any_call(1.5)  # Second retry: capped at max_delay
        mock_sleep.assert_any_call(1.5)  # Third retry: capped at max_delay
        
        # Verify result
        self.assertEqual(result, "success")


class TestRetryWithBackoffSync(unittest.TestCase):
    """Test cases for retry_with_backoff_sync."""
    
    def test_success_first_attempt(self):
        """Test successful operation on first attempt."""
        # Mock operation that succeeds
        mock_operation = MagicMock(return_value="success")
        
        # Create retry policy
        policy = RetryPolicy(max_retries=3)
        
        # Call retry_with_backoff_sync
        result = retry_with_backoff_sync(mock_operation, policy, "test_operation")
        
        # Verify operation was called once
        mock_operation.assert_called_once()
        
        # Verify result
        self.assertEqual(result, "success")
    
    def test_success_after_retry(self):
        """Test successful operation after retry."""
        # Mock operation that fails once then succeeds
        mock_operation = MagicMock(side_effect=[ValueError("Error"), "success"])
        
        # Create retry policy
        policy = RetryPolicy(max_retries=3)
        
        # Call retry_with_backoff_sync
        result = retry_with_backoff_sync(mock_operation, policy, "test_operation")
        
        # Verify operation was called twice
        self.assertEqual(mock_operation.call_count, 2)
        
        # Verify result
        self.assertEqual(result, "success")
    
    def test_max_retries_exceeded(self):
        """Test operation that exceeds max retries."""
        # Mock operation that always fails
        error = ValueError("Error")
        mock_operation = MagicMock(side_effect=error)
        
        # Create retry policy
        policy = RetryPolicy(max_retries=2)
        
        # Call retry_with_backoff_sync and verify it raises MaxRetriesExceededError
        with self.assertRaises(MaxRetriesExceededError) as context:
            retry_with_backoff_sync(mock_operation, policy, "test_operation")
        
        # Verify operation was called max_retries + 1 times
        self.assertEqual(mock_operation.call_count, 3)
        
        # Verify error details
        self.assertEqual(context.exception.attempts, 3)
        self.assertEqual(context.exception.last_error, error)
    
    def test_retry_specific_exceptions(self):
        """Test retry with specific exceptions."""
        # Mock operation that raises different exceptions
        mock_operation = MagicMock(side_effect=[
            ValueError("Error"),  # Should retry
            TypeError("Error"),   # Should not retry
            "success"
        ])
        
        # Create retry policy with specific retry exceptions
        policy = RetryPolicy(max_retries=3, retry_exceptions=[ValueError])
        
        # Call retry_with_backoff_sync and verify it raises TypeError
        with self.assertRaises(MaxRetriesExceededError) as context:
            retry_with_backoff_sync(mock_operation, policy, "test_operation")
        
        # Verify operation was called twice (initial + 1 retry)
        self.assertEqual(mock_operation.call_count, 2)
        
        # Verify error details
        self.assertEqual(context.exception.attempts, 2)
        self.assertIsInstance(context.exception.last_error, TypeError)
    
    @patch("time.sleep")
    def test_backoff_delay(self, mock_sleep):
        """Test backoff delay calculation."""
        # Mock operation that fails multiple times
        mock_operation = MagicMock(side_effect=[
            ValueError("Error 1"),
            ValueError("Error 2"),
            ValueError("Error 3"),
            "success"
        ])
        
        # Create retry policy with no jitter
        policy = RetryPolicy(
            max_retries=3,
            base_delay=1.0,
            max_delay=10.0,
            jitter_factor=0.0
        )
        
        # Call retry_with_backoff_sync
        result = retry_with_backoff_sync(mock_operation, policy, "test_operation")
        
        # Verify operation was called 4 times
        self.assertEqual(mock_operation.call_count, 4)
        
        # Verify sleep was called with expected delays
        mock_sleep.assert_any_call(1.0)  # First retry: base_delay * (2^0)
        mock_sleep.assert_any_call(2.0)  # Second retry: base_delay * (2^1)
        mock_sleep.assert_any_call(4.0)  # Third retry: base_delay * (2^2)
        
        # Verify result
        self.assertEqual(result, "success")
    
    @patch("time.sleep")
    def test_max_delay(self, mock_sleep):
        """Test maximum delay cap."""
        # Mock operation that fails multiple times
        mock_operation = MagicMock(side_effect=[
            ValueError("Error 1"),
            ValueError("Error 2"),
            ValueError("Error 3"),
            "success"
        ])
        
        # Create retry policy with low max_delay
        policy = RetryPolicy(
            max_retries=3,
            base_delay=1.0,
            max_delay=1.5,  # Cap delay at 1.5
            jitter_factor=0.0
        )
        
        # Call retry_with_backoff_sync
        result = retry_with_backoff_sync(mock_operation, policy, "test_operation")
        
        # Verify operation was called 4 times
        self.assertEqual(mock_operation.call_count, 4)
        
        # Verify sleep was called with expected delays
        mock_sleep.assert_any_call(1.0)  # First retry: base_delay * (2^0)
        mock_sleep.assert_any_call(1.5)  # Second retry: capped at max_delay
        mock_sleep.assert_any_call(1.5)  # Third retry: capped at max_delay
        
        # Verify result
        self.assertEqual(result, "success")


if __name__ == "__main__":
    unittest.main()
