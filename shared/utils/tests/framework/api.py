"""
API testing utilities.

This module provides utilities for API testing, including request building,
response validation, and authentication helpers.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Type, Union, AsyncGenerator, Tuple
import pytest
import pytest_asyncio
from httpx import AsyncClient, Response

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.testclient import TestClient


class APITestConfig:
    """
    Configuration for API tests.
    
    This class provides configuration options for API tests.
    """
    
    def __init__(
        self,
        base_url: str = "http://test",
        include_headers: bool = True,
        timeout: float = 10.0,
    ):
        """
        Initialize the configuration.
        
        Args:
            base_url: Base URL for requests
            include_headers: Whether to include default headers
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.include_headers = include_headers
        self.timeout = timeout


class APITestHelper:
    """
    Helper for API tests.
    
    This class provides utilities for API tests, including request building,
    response validation, and authentication helpers.
    """
    
    def __init__(self, app: FastAPI, config: Optional[APITestConfig] = None):
        """
        Initialize the helper.
        
        Args:
            app: FastAPI application
            config: API test configuration
        """
        self.app = app
        self.config = config or APITestConfig()
        self.test_client = TestClient(app)
        self.auth_token = None
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get request headers.
        
        Returns:
            Dict[str, str]: Request headers
        """
        headers = {}
        
        if self.config.include_headers:
            headers.update({
                "Content-Type": "application/json",
                "Accept": "application/json",
            })
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        return headers
    
    def set_auth_token(self, token: str):
        """
        Set authentication token.
        
        Args:
            token: Authentication token
        """
        self.auth_token = token
    
    def clear_auth_token(self):
        """Clear authentication token."""
        self.auth_token = None
    
    def build_url(self, path: str) -> str:
        """
        Build a URL from path.
        
        Args:
            path: Path
            
        Returns:
            str: Full URL
        """
        # Remove trailing slash from base URL
        base_url = self.config.base_url
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        
        # Remove leading slash from path
        if path.startswith("/"):
            path = path[1:]
        
        return f"{base_url}/{path}"
    
    @pytest_asyncio.fixture
    async def async_client(self) -> AsyncGenerator[AsyncClient, None]:
        """
        Create an async test client.
        
        Yields:
            AsyncClient: Async test client
        """
        async with AsyncClient(app=self.app, base_url=self.config.base_url) as client:
            # Set default headers
            client.headers.update(self.get_headers())
            
            yield client
    
    async def get(
        self,
        client: AsyncClient,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        Send a GET request.
        
        Args:
            client: Async client
            path: Request path
            params: Query parameters
            headers: Request headers
            
        Returns:
            Response: Response
        """
        return await client.get(
            path,
            params=params,
            headers=headers,
            timeout=self.config.timeout,
        )
    
    async def post(
        self,
        client: AsyncClient,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        Send a POST request.
        
        Args:
            client: Async client
            path: Request path
            json_data: JSON data
            params: Query parameters
            headers: Request headers
            
        Returns:
            Response: Response
        """
        return await client.post(
            path,
            json=json_data,
            params=params,
            headers=headers,
            timeout=self.config.timeout,
        )
    
    async def put(
        self,
        client: AsyncClient,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        Send a PUT request.
        
        Args:
            client: Async client
            path: Request path
            json_data: JSON data
            params: Query parameters
            headers: Request headers
            
        Returns:
            Response: Response
        """
        return await client.put(
            path,
            json=json_data,
            params=params,
            headers=headers,
            timeout=self.config.timeout,
        )
    
    async def delete(
        self,
        client: AsyncClient,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        Send a DELETE request.
        
        Args:
            client: Async client
            path: Request path
            params: Query parameters
            headers: Request headers
            
        Returns:
            Response: Response
        """
        return await client.delete(
            path,
            params=params,
            headers=headers,
            timeout=self.config.timeout,
        )
    
    @staticmethod
    def assert_status_code(response: Response, expected_status_code: int):
        """
        Assert that a response has the expected status code.
        
        Args:
            response: Response
            expected_status_code: Expected status code
        """
        assert response.status_code == expected_status_code, \
            f"Expected status code {expected_status_code}, got {response.status_code}: {response.text}"
    
    @staticmethod
    def assert_json_response(response: Response, expected_data: Optional[Dict[str, Any]] = None):
        """
        Assert that a response is JSON and optionally has the expected data.
        
        Args:
            response: Response
            expected_data: Expected data
        """
        assert response.headers["Content-Type"] == "application/json"
        data = response.json()
        
        if expected_data:
            for key, value in expected_data.items():
                assert key in data, f"Key {key} not found in response"
                assert data[key] == value, f"Expected {key}={value}, got {data[key]}"
    
    @staticmethod
    def assert_successful_response(response: Response, expected_data: Optional[Dict[str, Any]] = None):
        """
        Assert that a response is successful and optionally has the expected data.
        
        Args:
            response: Response
            expected_data: Expected data
        """
        assert response.status_code in (200, 201, 202, 204), \
            f"Expected successful status code, got {response.status_code}: {response.text}"
        
        if response.status_code != 204:  # No content
            assert response.headers["Content-Type"] == "application/json"
            data = response.json()
            
            if expected_data:
                for key, value in expected_data.items():
                    assert key in data, f"Key {key} not found in response"
                    assert data[key] == value, f"Expected {key}={value}, got {data[key]}"
    
    @staticmethod
    def assert_error_response(response: Response, expected_status_code: int, expected_error: Optional[str] = None):
        """
        Assert that a response is an error with the expected status code and optionally the expected error message.
        
        Args:
            response: Response
            expected_status_code: Expected status code
            expected_error: Expected error message
        """
        assert response.status_code == expected_status_code, \
            f"Expected status code {expected_status_code}, got {response.status_code}: {response.text}"
        
        assert response.headers["Content-Type"] == "application/json"
        data = response.json()
        
        assert "detail" in data, "Error response missing 'detail' field"
        
        if expected_error:
            assert data["detail"] == expected_error, \
                f"Expected error message '{expected_error}', got '{data['detail']}'"
    
    @staticmethod
    def assert_pagination(response: Response, expected_page: int, expected_page_size: int):
        """
        Assert that a response has the expected pagination.
        
        Args:
            response: Response
            expected_page: Expected page number
            expected_page_size: Expected page size
        """
        data = response.json()
        
        assert "page" in data, "Response missing 'page' field"
        assert "page_size" in data, "Response missing 'page_size' field"
        assert "total" in data, "Response missing 'total' field"
        
        assert data["page"] == expected_page, \
            f"Expected page {expected_page}, got {data['page']}"
        assert data["page_size"] == expected_page_size, \
            f"Expected page_size {expected_page_size}, got {data['page_size']}"
        
        # Verify that items length matches page_size (unless it's the last page)
        if "items" in data:
            items_length = len(data["items"])
            if data["page"] < (data["total"] + expected_page_size - 1) // expected_page_size:
                assert items_length == expected_page_size, \
                    f"Expected {expected_page_size} items, got {items_length}"
            else:
                assert items_length <= expected_page_size, \
                    f"Expected at most {expected_page_size} items, got {items_length}"


class MockAuthHelper:
    """
    Helper for mocking authentication in tests.
    
    This class provides utilities for mocking authentication in tests.
    """
    
    def __init__(self, app: FastAPI, token_url: str = "token"):
        """
        Initialize the helper.
        
        Args:
            app: FastAPI application
            token_url: Token URL
        """
        self.app = app
        self.token_url = token_url
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl=token_url)
        self.users = {}
        self.tokens = {}
    
    def add_user(self, username: str, password: str, scopes: Optional[List[str]] = None):
        """
        Add a user.
        
        Args:
            username: Username
            password: Password
            scopes: Optional scopes
        """
        self.users[username] = {
            "username": username,
            "password": password,
            "scopes": scopes or [],
        }
    
    def create_token(self, username: str) -> str:
        """
        Create a token for a user.
        
        Args:
            username: Username
            
        Returns:
            str: Token
        """
        if username not in self.users:
            raise ValueError(f"User {username} not found")
        
        token = f"mock_token_{username}"
        self.tokens[token] = username
        
        return token
    
    def setup_mock_auth(self):
        """Set up mock authentication."""
        
        async def get_current_user(token: str = Depends(self.oauth2_scheme)):
            if token not in self.tokens:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            username = self.tokens[token]
            return self.users[username]
        
        # Override the dependency
        self.app.dependency_overrides[self.oauth2_scheme] = lambda: "mock_token"
        
        # Add token endpoint
        @self.app.post(f"/{self.token_url}")
        async def login(username: str, password: str):
            if username not in self.users or self.users[username]["password"] != password:
                raise HTTPException(
                    status_code=401,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            token = self.create_token(username)
            
            return {
                "access_token": token,
                "token_type": "bearer",
            }
        
        return get_current_user
    
    def teardown_mock_auth(self):
        """Tear down mock authentication."""
        if self.oauth2_scheme in self.app.dependency_overrides:
            del self.app.dependency_overrides[self.oauth2_scheme]


class MockResponse:
    """
    Mock response for testing.
    
    This class provides a mock response for testing without sending actual requests.
    """
    
    def __init__(
        self,
        status_code: int = 200,
        content: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the mock response.
        
        Args:
            status_code: Status code
            content: Response content
            headers: Response headers
        """
        self.status_code = status_code
        self.content = content or {}
        self.headers = headers or {"Content-Type": "application/json"}
    
    def json(self) -> Dict[str, Any]:
        """
        Get response content as JSON.
        
        Returns:
            Dict[str, Any]: Response content
        """
        return self.content
    
    @property
    def text(self) -> str:
        """
        Get response content as text.
        
        Returns:
            str: Response content
        """
        return json.dumps(self.content)
    
    def raise_for_status(self):
        """Raise an exception if the status code indicates an error."""
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")


class MockClient:
    """
    Mock client for testing.
    
    This class provides a mock client for testing without sending actual requests.
    """
    
    def __init__(self):
        """Initialize the mock client."""
        self.responses = {}
        self.requests = []
    
    def add_response(
        self,
        method: str,
        path: str,
        status_code: int = 200,
        content: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Add a mock response.
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Status code
            content: Response content
            headers: Response headers
        """
        key = f"{method.upper()}:{path}"
        self.responses[key] = MockResponse(status_code, content, headers)
    
    def get_request(self, index: int) -> Dict[str, Any]:
        """
        Get a request by index.
        
        Args:
            index: Request index
            
        Returns:
            Dict[str, Any]: Request
        """
        if index >= len(self.requests):
            raise IndexError(f"Request index {index} out of range")
        
        return self.requests[index]
    
    def get_last_request(self) -> Dict[str, Any]:
        """
        Get the last request.
        
        Returns:
            Dict[str, Any]: Request
        """
        if not self.requests:
            raise IndexError("No requests recorded")
        
        return self.requests[-1]
    
    def clear_requests(self):
        """Clear recorded requests."""
        self.requests = []
    
    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> MockResponse:
        """
        Send a mock request.
        
        Args:
            method: HTTP method
            path: Request path
            params: Query parameters
            json_data: JSON data
            headers: Request headers
            
        Returns:
            MockResponse: Mock response
        """
        # Record request
        self.requests.append({
            "method": method.upper(),
            "path": path,
            "params": params,
            "json": json_data,
            "headers": headers,
        })
        
        # Get response
        key = f"{method.upper()}:{path}"
        if key in self.responses:
            return self.responses[key]
        
        # Default response
        return MockResponse(404, {"detail": "Not Found"})
    
    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> MockResponse:
        """
        Send a GET request.
        
        Args:
            path: Request path
            params: Query parameters
            headers: Request headers
            
        Returns:
            MockResponse: Mock response
        """
        return self.request("GET", path, params=params, headers=headers)
    
    def post(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> MockResponse:
        """
        Send a POST request.
        
        Args:
            path: Request path
            json_data: JSON data
            params: Query parameters
            headers: Request headers
            
        Returns:
            MockResponse: Mock response
        """
        return self.request("POST", path, params=params, json_data=json_data, headers=headers)
    
    def put(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> MockResponse:
        """
        Send a PUT request.
        
        Args:
            path: Request path
            json_data: JSON data
            params: Query parameters
            headers: Request headers
            
        Returns:
            MockResponse: Mock response
        """
        return self.request("PUT", path, params=params, json_data=json_data, headers=headers)
    
    def delete(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> MockResponse:
        """
        Send a DELETE request.
        
        Args:
            path: Request path
            params: Query parameters
            headers: Request headers
            
        Returns:
            MockResponse: Mock response
        """
        return self.request("DELETE", path, params=params, headers=headers)
