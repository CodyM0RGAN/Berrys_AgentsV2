"""
Base API client and error handling for external service communication.
"""
import json
import logging
from typing import Any, Dict, Optional, Union

import requests
from flask import current_app

# Set up logger
logger = logging.getLogger(__name__)

class APIError(Exception):
    """Exception raised for API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict[str, Any]] = None):
        """
        Initialize APIError.
        
        Args:
            message: Error message
            status_code: HTTP status code
            response: Raw API response
        """
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

class BaseAPIClient:
    """Base API client for external service communication."""
    
    def __init__(self, base_url: str, timeout: Optional[int] = None):
        """
        Initialize BaseAPIClient.
        
        Args:
            base_url: Base URL for API requests
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout or current_app.config.get('API_TIMEOUT', 10)
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers.
        
        Returns:
            Dict of headers
        """
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response.
        
        Args:
            response: Response object
            
        Returns:
            Parsed response data
            
        Raises:
            APIError: If the response indicates an error
        """
        try:
            response.raise_for_status()
            
            # Handle empty response
            if not response.text:
                return {}
            
            # Parse JSON response
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            # Try to parse error response
            error_data = {}
            error_message = str(e)
            
            try:
                error_data = response.json()
                if isinstance(error_data, dict) and 'message' in error_data:
                    error_message = error_data['message']
            except (ValueError, json.JSONDecodeError):
                if response.text:
                    error_message = response.text
            
            logger.error(f"API Error: {error_message} (Status: {response.status_code})")
            raise APIError(error_message, response.status_code, error_data)
        
        except (ValueError, json.JSONDecodeError) as e:
            error_message = f"Invalid JSON response: {str(e)}"
            logger.error(error_message)
            raise APIError(error_message, response.status_code)
    
    def request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make an API request.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            params: Query parameters
            data: Request data
            headers: Additional headers
            timeout: Request timeout in seconds
            
        Returns:
            Parsed response data
            
        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self._get_headers()
        
        if headers:
            request_headers.update(headers)
        
        request_timeout = timeout or self.timeout
        
        try:
            # Convert data to JSON if provided
            json_data = json.dumps(data) if data else None
            
            logger.debug(f"API Request: {method} {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=json_data,
                headers=request_headers,
                timeout=request_timeout
            )
            
            return self._handle_response(response)
        
        except requests.exceptions.RequestException as e:
            error_message = f"Request failed: {str(e)}"
            logger.error(error_message)
            raise APIError(error_message)
    
    def get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make a GET request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout in seconds
            
        Returns:
            Parsed response data
        """
        return self.request('GET', endpoint, params=params, headers=headers, timeout=timeout)
    
    def post(
        self, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make a POST request.
        
        Args:
            endpoint: API endpoint
            data: Request data
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout in seconds
            
        Returns:
            Parsed response data
        """
        return self.request('POST', endpoint, params=params, data=data, headers=headers, timeout=timeout)
    
    def put(
        self, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make a PUT request.
        
        Args:
            endpoint: API endpoint
            data: Request data
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout in seconds
            
        Returns:
            Parsed response data
        """
        return self.request('PUT', endpoint, params=params, data=data, headers=headers, timeout=timeout)
    
    def delete(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make a DELETE request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout in seconds
            
        Returns:
            Parsed response data
        """
        return self.request('DELETE', endpoint, params=params, headers=headers, timeout=timeout)
