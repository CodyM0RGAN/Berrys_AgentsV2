"""
Service Client implementation.

This module provides client functionality for communicating with other services,
with circuit breaker protection.
"""
from typing import Dict, Any, Optional, List, Callable
import aiohttp
import logging
import json
import time
import asyncio
from datetime import datetime

from ....models.api import ServiceInfo
from ....exceptions import (
    ServiceConnectionError, 
    ServiceTimeoutError, 
    ServiceUnavailableError,
    ServiceNotFoundError
)
from ..discovery.service import ServiceDiscovery
from .circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitBreakerRegistry


class ServiceClient:
    """
    Service Client for making HTTP requests to other services.
    
    This client includes circuit breaker protection and automatic discovery
    of service endpoints.
    """
    
    def __init__(
        self,
        service_discovery: ServiceDiscovery,
        logger: Optional[logging.Logger] = None,
        default_timeout: float = 30.0,
        circuit_breaker_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the service client.
        
        Args:
            service_discovery: Service discovery instance
            logger: Logger instance (optional)
            default_timeout: Default timeout for requests in seconds
            circuit_breaker_config: Circuit breaker configuration override
        """
        self.service_discovery = service_discovery
        self.logger = logger or logging.getLogger("service_client")
        self.default_timeout = default_timeout
        self.session = None
        
        # Circuit breaker configuration
        self.circuit_breaker_config = circuit_breaker_config or {}
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=self.default_timeout)
            )
    
    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    def _get_circuit_breaker(self, service_id: str) -> CircuitBreaker:
        """Get a circuit breaker for a service."""
        return CircuitBreakerRegistry.get_circuit_breaker(
            name=service_id,
            failure_threshold=self.circuit_breaker_config.get("failure_threshold", 5),
            reset_timeout=self.circuit_breaker_config.get("reset_timeout", 30),
            half_open_max_calls=self.circuit_breaker_config.get("half_open_max_calls", 3)
        )
    
    async def get(
        self,
        service: ServiceInfo,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Make a GET request to a service.
        
        Args:
            service: Service information
            endpoint: Endpoint path (e.g., "/api/resource")
            params: Query parameters (optional)
            headers: HTTP headers (optional)
            timeout: Request timeout in seconds (optional)
            
        Returns:
            Response data as a dictionary
            
        Raises:
            ServiceConnectionError: If the connection fails
            ServiceTimeoutError: If the request times out
            ServiceUnavailableError: If the circuit is open
            Exception: Other request failures
        """
        return await self._request(
            method="GET",
            service=service,
            endpoint=endpoint,
            params=params,
            headers=headers,
            timeout=timeout
        )
    
    async def post(
        self,
        service: ServiceInfo,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Make a POST request to a service.
        
        Args:
            service: Service information
            endpoint: Endpoint path (e.g., "/api/resource")
            data: Request body data
            params: Query parameters (optional)
            headers: HTTP headers (optional)
            timeout: Request timeout in seconds (optional)
            
        Returns:
            Response data as a dictionary
            
        Raises:
            ServiceConnectionError: If the connection fails
            ServiceTimeoutError: If the request times out
            ServiceUnavailableError: If the circuit is open
            Exception: Other request failures
        """
        return await self._request(
            method="POST",
            service=service,
            endpoint=endpoint,
            data=data,
            params=params,
            headers=headers,
            timeout=timeout
        )
    
    async def put(
        self,
        service: ServiceInfo,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Make a PUT request to a service.
        
        Args:
            service: Service information
            endpoint: Endpoint path (e.g., "/api/resource")
            data: Request body data
            params: Query parameters (optional)
            headers: HTTP headers (optional)
            timeout: Request timeout in seconds (optional)
            
        Returns:
            Response data as a dictionary
            
        Raises:
            ServiceConnectionError: If the connection fails
            ServiceTimeoutError: If the request times out
            ServiceUnavailableError: If the circuit is open
            Exception: Other request failures
        """
        return await self._request(
            method="PUT",
            service=service,
            endpoint=endpoint,
            data=data,
            params=params,
            headers=headers,
            timeout=timeout
        )
    
    async def delete(
        self,
        service: ServiceInfo,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Make a DELETE request to a service.
        
        Args:
            service: Service information
            endpoint: Endpoint path (e.g., "/api/resource")
            params: Query parameters (optional)
            headers: HTTP headers (optional)
            timeout: Request timeout in seconds (optional)
            
        Returns:
            Response data as a dictionary
            
        Raises:
            ServiceConnectionError: If the connection fails
            ServiceTimeoutError: If the request times out
            ServiceUnavailableError: If the circuit is open
            Exception: Other request failures
        """
        return await self._request(
            method="DELETE",
            service=service,
            endpoint=endpoint,
            params=params,
            headers=headers,
            timeout=timeout
        )
    
    async def request_by_service_type(
        self,
        service_type: str,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make a request to a service by type.
        
        This automatically discovers a service of the specified type.
        
        Args:
            service_type: Type of service to request
            method: HTTP method (GET, POST, etc.)
            endpoint: Endpoint path
            **kwargs: Additional arguments for the request
            
        Returns:
            Response data as a dictionary
            
        Raises:
            ServiceNotFoundError: If no service of the type is found
            Other exceptions from the request method
        """
        # Find a service of the specified type
        service = await self.service_discovery.get_service_by_type(service_type)
        
        # Make the request
        return await self._request(
            method=method,
            service=service,
            endpoint=endpoint,
            **kwargs
        )
    
    async def _request(
        self,
        method: str,
        service: ServiceInfo,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Make a request to a service with circuit breaker protection.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            service: Service information
            endpoint: Endpoint path
            data: Request body data (optional)
            params: Query parameters (optional)
            headers: HTTP headers (optional)
            timeout: Request timeout in seconds (optional)
            
        Returns:
            Response data as a dictionary
            
        Raises:
            ServiceConnectionError: If the connection fails
            ServiceTimeoutError: If the request times out
            ServiceUnavailableError: If the circuit is open
            Exception: Other request failures
        """
        await self._ensure_session()
        
        url = f"{service.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Get circuit breaker for this service
        circuit_breaker = self._get_circuit_breaker(service.service_id)
        
        # Execute request with circuit breaker protection
        try:
            return await circuit_breaker.execute(
                self._do_request, method, url, data, params, headers, timeout
            )
        except CircuitOpenError as e:
            self.logger.error(f"Circuit open for service {service.name}: {str(e)}")
            raise ServiceUnavailableError(f"Service {service.name} is unavailable (circuit open)")
            
    async def _do_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute the actual HTTP request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL
            data: Request body data (optional)
            params: Query parameters (optional)
            headers: HTTP headers (optional)
            timeout: Request timeout in seconds (optional)
            
        Returns:
            Response data as a dictionary
            
        Raises:
            ServiceConnectionError: If the connection fails
            ServiceTimeoutError: If the request times out
            Exception: Other request failures
        """
        start_time = time.time()
        self.logger.debug(f"{method} request to {url}")
        
        request_timeout = aiohttp.ClientTimeout(total=timeout or self.default_timeout)
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=request_timeout
            ) as response:
                execution_time = time.time() - start_time
                self.logger.debug(f"{method} {url} completed in {execution_time:.2f}s with status {response.status}")
                
                # Read response body
                if response.content_type == 'application/json':
                    response_data = await response.json()
                else:
                    text = await response.text()
                    try:
                        response_data = json.loads(text)
                    except json.JSONDecodeError:
                        response_data = {"text": text}
                
                # Handle non-success status codes
                if response.status >= 400:
                    error_msg = response_data.get("detail", str(response_data))
                    
                    if response.status >= 500:
                        self.logger.error(f"Service error from {url}: {response.status} - {error_msg}")
                        raise ServiceConnectionError(f"Service error: {response.status} - {error_msg}")
                    else:
                        self.logger.warning(f"Request error from {url}: {response.status} - {error_msg}")
                        # Regular exceptions for client errors (4xx)
                        if response.status == 404:
                            raise ServiceNotFoundError(f"Resource not found: {error_msg}")
                        # For other error codes, raise a regular exception
                        raise Exception(f"Request error: {response.status} - {error_msg}")
                        
                return response_data
                
        except aiohttp.ClientConnectorError as e:
            self.logger.error(f"Connection error for {url}: {str(e)}")
            raise ServiceConnectionError(f"Connection error: {str(e)}")
            
        except asyncio.TimeoutError:
            self.logger.error(f"Request timeout for {url}")
            raise ServiceTimeoutError(f"Request timed out after {timeout or self.default_timeout} seconds")
            
        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP client error for {url}: {str(e)}")
            raise ServiceConnectionError(f"HTTP client error: {str(e)}")
