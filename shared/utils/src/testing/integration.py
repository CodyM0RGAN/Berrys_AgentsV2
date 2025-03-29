"""
Integration testing utilities for Berrys_AgentsV2.

This module provides utilities for integration testing, including:
- Service harness for spinning up test instances of services
- Test fixtures for integration testing
- Utilities for testing cross-service interactions
"""

import os
import sys
import time
import json
import socket
import signal
import asyncio
import subprocess
import multiprocessing
from typing import Dict, List, Any, Optional, Callable, Union, Tuple, Set, TypeVar

import pytest
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .database import get_in_memory_db_engine, create_test_database, drop_test_database


class ServiceHarness:
    """
    Harness for running a service for integration testing.
    
    This class provides methods for starting and stopping a service,
    as well as interacting with the service.
    """
    
    def __init__(
        self,
        service_name: str,
        service_dir: Optional[str] = None,
        host: str = "localhost",
        port: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
        startup_timeout: int = 10,
        python_path: Optional[str] = None
    ):
        """
        Initialize the service harness.
        
        Args:
            service_name: Name of the service.
            service_dir: Directory containing the service code. Defaults to the service name.
            host: Host to bind the service to (default: "localhost").
            port: Port to bind the service to. If not provided, a random port will be used.
            env: Environment variables to set for the service.
            startup_timeout: Timeout in seconds for service startup.
            python_path: Path to the Python executable to use.
        """
        self.service_name = service_name
        self.service_dir = service_dir or f"services/{service_name}"
        self.host = host
        self.port = port or self._find_free_port()
        self.env = env or {}
        self.startup_timeout = startup_timeout
        self.python_path = python_path or sys.executable
        
        self.process = None
        self.url = f"http://{host}:{self.port}"
        
    def _find_free_port(self) -> int:
        """
        Find a free port to bind the service to.
        
        Returns:
            Free port number.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]
            
    def start(self) -> None:
        """
        Start the service.
        
        This launches the service process and waits for it to start up.
        
        Raises:
            TimeoutError: If the service fails to start within the timeout.
        """
        if self.process is not None:
            raise RuntimeError("Service is already running")
            
        # Update environment variables
        env = os.environ.copy()
        env.update(self.env)
        env["PORT"] = str(self.port)
        
        # Start the service process
        self.process = subprocess.Popen(
            [self.python_path, "-m", "uvicorn", "src.main:app", "--host", self.host, "--port", str(self.port)],
            cwd=self.service_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for the service to start up
        start_time = time.time()
        while time.time() - start_time < self.startup_timeout:
            try:
                response = requests.get(f"{self.url}/health")
                if response.status_code == 200:
                    return
            except requests.RequestException:
                pass
                
            # Check if the process has exited
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                raise RuntimeError(
                    f"Service process exited with code {self.process.returncode}\n"
                    f"STDOUT: {stdout}\n"
                    f"STDERR: {stderr}"
                )
                
            time.sleep(0.1)
            
        # If we get here, the service failed to start
        self.stop()
        raise TimeoutError(f"Service {self.service_name} failed to start within {self.startup_timeout} seconds")
        
    def stop(self) -> None:
        """Stop the service."""
        if self.process is None:
            return
            
        # Try to terminate the process gracefully
        self.process.terminate()
        
        # Wait for the process to exit
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # If the process doesn't exit, kill it
            self.process.kill()
            self.process.wait()
            
        self.process = None
        
    def __enter__(self) -> "ServiceHarness":
        """
        Enter context manager.
        
        Returns:
            Self.
        """
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        self.stop()
        
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """
        Make a GET request to the service.
        
        Args:
            endpoint: Endpoint to request.
            **kwargs: Additional keyword arguments to pass to requests.get.
            
        Returns:
            Response from the service.
        """
        return requests.get(f"{self.url}{endpoint}", **kwargs)
        
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """
        Make a POST request to the service.
        
        Args:
            endpoint: Endpoint to request.
            **kwargs: Additional keyword arguments to pass to requests.post.
            
        Returns:
            Response from the service.
        """
        return requests.post(f"{self.url}{endpoint}", **kwargs)
        
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """
        Make a PUT request to the service.
        
        Args:
            endpoint: Endpoint to request.
            **kwargs: Additional keyword arguments to pass to requests.put.
            
        Returns:
            Response from the service.
        """
        return requests.put(f"{self.url}{endpoint}", **kwargs)
        
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """
        Make a DELETE request to the service.
        
        Args:
            endpoint: Endpoint to request.
            **kwargs: Additional keyword arguments to pass to requests.delete.
            
        Returns:
            Response from the service.
        """
        return requests.delete(f"{self.url}{endpoint}", **kwargs)
        
    def patch(self, endpoint: str, **kwargs) -> requests.Response:
        """
        Make a PATCH request to the service.
        
        Args:
            endpoint: Endpoint to request.
            **kwargs: Additional keyword arguments to pass to requests.patch.
            
        Returns:
            Response from the service.
        """
        return requests.patch(f"{self.url}{endpoint}", **kwargs)


class IntegrationTestHarness:
    """
    Harness for integration testing multiple services.
    
    This class provides methods for starting and stopping multiple services,
    as well as interacting with them.
    """
    
    def __init__(self):
        """Initialize the integration test harness."""
        self.services: Dict[str, ServiceHarness] = {}
        
    def add_service(
        self,
        service_name: str,
        service_dir: Optional[str] = None,
        host: str = "localhost",
        port: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
        startup_timeout: int = 10,
        python_path: Optional[str] = None
    ) -> ServiceHarness:
        """
        Add a service to the harness.
        
        Args:
            service_name: Name of the service.
            service_dir: Directory containing the service code. Defaults to the service name.
            host: Host to bind the service to (default: "localhost").
            port: Port to bind the service to. If not provided, a random port will be used.
            env: Environment variables to set for the service.
            startup_timeout: Timeout in seconds for service startup.
            python_path: Path to the Python executable to use.
            
        Returns:
            Service harness.
        """
        service = ServiceHarness(
            service_name=service_name,
            service_dir=service_dir,
            host=host,
            port=port,
            env=env,
            startup_timeout=startup_timeout,
            python_path=python_path
        )
        
        self.services[service_name] = service
        return service
        
    def get_service(self, service_name: str) -> ServiceHarness:
        """
        Get a service by name.
        
        Args:
            service_name: Name of the service.
            
        Returns:
            Service harness.
            
        Raises:
            KeyError: If the service is not found.
        """
        if service_name not in self.services:
            raise KeyError(f"Service {service_name} not found in harness")
            
        return self.services[service_name]
        
    def start_service(self, service_name: str) -> None:
        """
        Start a service.
        
        Args:
            service_name: Name of the service.
            
        Raises:
            KeyError: If the service is not found.
        """
        self.get_service(service_name).start()
        
    def stop_service(self, service_name: str) -> None:
        """
        Stop a service.
        
        Args:
            service_name: Name of the service.
            
        Raises:
            KeyError: If the service is not found.
        """
        self.get_service(service_name).stop()
        
    def start_all(self) -> None:
        """Start all services."""
        for service_name in self.services:
            self.start_service(service_name)
            
    def stop_all(self) -> None:
        """Stop all services."""
        for service_name in self.services:
            self.stop_service(service_name)
            
    def __enter__(self) -> "IntegrationTestHarness":
        """
        Enter context manager.
        
        Returns:
            Self.
        """
        self.start_all()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        self.stop_all()


class MockIntegrationService:
    """
    Mock service for integration testing.
    
    This class provides a mock service that can be used for integration testing
    without having to spin up a real service process.
    """
    
    def __init__(
        self,
        service_name: str,
        endpoints: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        """
        Initialize the mock service.
        
        Args:
            service_name: Name of the service.
            endpoints: Dictionary mapping endpoint paths to dictionaries mapping HTTP methods to response data.
        """
        self.service_name = service_name
        self.endpoints = endpoints or {}
        self.requests: List[Dict[str, Any]] = []
        
    def add_endpoint(
        self,
        path: str,
        method: str,
        response_data: Any,
        status_code: int = 200
    ) -> None:
        """
        Add an endpoint to the mock service.
        
        Args:
            path: Endpoint path.
            method: HTTP method.
            response_data: Response data to return.
            status_code: HTTP status code to return (default: 200).
        """
        if path not in self.endpoints:
            self.endpoints[path] = {}
            
        self.endpoints[path][method.upper()] = {
            "data": response_data,
            "status_code": status_code
        }
        
    def handle_request(
        self,
        path: str,
        method: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Handle a request to the mock service.
        
        Args:
            path: Endpoint path.
            method: HTTP method.
            **kwargs: Additional request data.
            
        Returns:
            Response data.
            
        Raises:
            KeyError: If the endpoint or method is not found.
        """
        # Record the request
        self.requests.append({
            "path": path,
            "method": method.upper(),
            **kwargs
        })
        
        # Check if the endpoint exists
        if path not in self.endpoints:
            return {
                "error": f"Endpoint {path} not found",
                "status_code": 404
            }
            
        # Check if the method is supported
        if method.upper() not in self.endpoints[path]:
            return {
                "error": f"Method {method.upper()} not supported for endpoint {path}",
                "status_code": 405
            }
            
        # Return the response
        return self.endpoints[path][method.upper()]
        
    def get(self, path: str, **kwargs) -> Dict[str, Any]:
        """
        Make a GET request to the mock service.
        
        Args:
            path: Endpoint path.
            **kwargs: Additional request data.
            
        Returns:
            Response data.
        """
        return self.handle_request(path, "GET", **kwargs)
        
    def post(self, path: str, **kwargs) -> Dict[str, Any]:
        """
        Make a POST request to the mock service.
        
        Args:
            path: Endpoint path.
            **kwargs: Additional request data.
            
        Returns:
            Response data.
        """
        return self.handle_request(path, "POST", **kwargs)
        
    def put(self, path: str, **kwargs) -> Dict[str, Any]:
        """
        Make a PUT request to the mock service.
        
        Args:
            path: Endpoint path.
            **kwargs: Additional request data.
            
        Returns:
            Response data.
        """
        return self.handle_request(path, "PUT", **kwargs)
        
    def delete(self, path: str, **kwargs) -> Dict[str, Any]:
        """
        Make a DELETE request to the mock service.
        
        Args:
            path: Endpoint path.
            **kwargs: Additional request data.
            
        Returns:
            Response data.
        """
        return self.handle_request(path, "DELETE", **kwargs)
        
    def patch(self, path: str, **kwargs) -> Dict[str, Any]:
        """
        Make a PATCH request to the mock service.
        
        Args:
            path: Endpoint path.
            **kwargs: Additional request data.
            
        Returns:
            Response data.
        """
        return self.handle_request(path, "PATCH", **kwargs)
        
    def reset(self) -> None:
        """Reset the mock service."""
        self.requests = []


@pytest.fixture
def integration_harness() -> IntegrationTestHarness:
    """
    Integration test harness fixture.
    
    This fixture provides an integration test harness for testing
    multiple services together.
    
    Returns:
        Integration test harness.
    """
    harness = IntegrationTestHarness()
    yield harness
    harness.stop_all()
    
    
@pytest.fixture
def mock_integration_service() -> MockIntegrationService:
    """
    Mock integration service fixture.
    
    This fixture provides a mock service that can be used for integration testing
    without having to spin up a real service process.
    
    Returns:
        Mock integration service.
    """
    service = MockIntegrationService("mock-service")
    return service


@pytest.fixture
def integration_db() -> Session:
    """
    Integration test database fixture.
    
    This fixture provides a database session for integration testing.
    
    Returns:
        Database session.
    """
    # Create an in-memory database
    engine = get_in_memory_db_engine()
    create_test_database(engine)
    
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Clean up
    session.close()
    drop_test_database(engine)


def integration_test(
    services: List[str],
    mock_services: Optional[List[str]] = None,
    dependencies: Optional[List[str]] = None
) -> Callable:
    """
    Decorator for integration tests.
    
    This decorator provides a harness for integration testing with
    the specified services.
    
    Args:
        services: List of service names to start.
        mock_services: List of service names to mock.
        dependencies: List of dependencies to install before running the test.
        
    Returns:
        Decorated test function.
    """
    def decorator(func: Callable) -> Callable:
        @pytest.mark.integration
        @pytest.mark.asyncio
        async def wrapper(*args, **kwargs) -> Any:
            # Set up the harness
            harness = IntegrationTestHarness()
            
            # Add the services
            for service_name in services:
                harness.add_service(service_name)
                
            # Add the mock services
            mock_service_dict = {}
            if mock_services:
                for service_name in mock_services:
                    mock_service = MockIntegrationService(service_name)
                    mock_service_dict[service_name] = mock_service
                    
            # Start the services
            harness.start_all()
            
            try:
                # Call the test function
                result = await func(
                    *args,
                    harness=harness,
                    mock_services=mock_service_dict,
                    **kwargs
                )
                return result
            finally:
                # Stop the services
                harness.stop_all()
                
        return wrapper
        
    return decorator


T = TypeVar("T")


def with_retries(
    func: Callable[..., T],
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
) -> Callable[..., T]:
    """
    Decorator for retrying a function on failure.
    
    Args:
        func: Function to retry.
        retries: Number of retries.
        delay: Initial delay between retries.
        backoff: Backoff factor for the delay.
        exceptions: Exception types to catch.
        
    Returns:
        Decorated function.
    """
    async def async_wrapper(*args, **kwargs) -> T:
        """Async wrapper for the function."""
        last_exception = None
        current_delay = delay
        
        for i in range(retries + 1):
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if i < retries:
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                    
        raise last_exception
        
    def sync_wrapper(*args, **kwargs) -> T:
        """Sync wrapper for the function."""
        last_exception = None
        current_delay = delay
        
        for i in range(retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if i < retries:
                    time.sleep(current_delay)
                    current_delay *= backoff
                    
        raise last_exception
        
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
