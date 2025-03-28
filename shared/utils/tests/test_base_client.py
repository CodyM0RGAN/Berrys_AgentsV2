"""
Tests for the BaseAPIClient class.

This module contains tests for the BaseAPIClient class in shared/utils/src/clients/base.py.
"""
import json
import unittest
from unittest.mock import patch, MagicMock

import requests

from shared.utils.src.clients.base import BaseAPIClient, APIError


class TestBaseAPIClient(unittest.TestCase):
    """Test cases for BaseAPIClient."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.base_url = "http://example.com/api"
        self.client = BaseAPIClient(base_url=self.base_url)
    
    def test_init(self):
        """Test initialization of BaseAPIClient."""
        # Test with trailing slash in base_url
        client = BaseAPIClient(base_url=self.base_url + "/")
        self.assertEqual(client.base_url, self.base_url)
        
        # Test with custom timeout
        client = BaseAPIClient(base_url=self.base_url, timeout=30)
        self.assertEqual(client.timeout, 30)
        
        # Test with default timeout
        client = BaseAPIClient(base_url=self.base_url)
        self.assertEqual(client.timeout, 10)
    
    def test_get_headers(self):
        """Test _get_headers method."""
        headers = self.client._get_headers()
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(headers["Accept"], "application/json")
    
    @patch("requests.Session.request")
    def test_request_success(self, mock_request):
        """Test successful request."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"key": "value"}'
        mock_response.json.return_value = {"key": "value"}
        mock_request.return_value = mock_response
        
        # Make request
        result = self.client.request("GET", "endpoint")
        
        # Verify request was made correctly
        mock_request.assert_called_once_with(
            method="GET",
            url=f"{self.base_url}/endpoint",
            params=None,
            data=None,
            headers=self.client._get_headers(),
            timeout=10
        )
        
        # Verify result
        self.assertEqual(result, {"key": "value"})
    
    @patch("requests.Session.request")
    def test_request_with_params(self, mock_request):
        """Test request with query parameters."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"key": "value"}'
        mock_response.json.return_value = {"key": "value"}
        mock_request.return_value = mock_response
        
        # Make request with params
        params = {"param1": "value1", "param2": "value2"}
        result = self.client.request("GET", "endpoint", params=params)
        
        # Verify request was made correctly
        mock_request.assert_called_once_with(
            method="GET",
            url=f"{self.base_url}/endpoint",
            params=params,
            data=None,
            headers=self.client._get_headers(),
            timeout=10
        )
        
        # Verify result
        self.assertEqual(result, {"key": "value"})
    
    @patch("requests.Session.request")
    def test_request_with_data(self, mock_request):
        """Test request with data."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"key": "value"}'
        mock_response.json.return_value = {"key": "value"}
        mock_request.return_value = mock_response
        
        # Make request with data
        data = {"field1": "value1", "field2": "value2"}
        result = self.client.request("POST", "endpoint", data=data)
        
        # Verify request was made correctly
        mock_request.assert_called_once_with(
            method="POST",
            url=f"{self.base_url}/endpoint",
            params=None,
            data=json.dumps(data),
            headers=self.client._get_headers(),
            timeout=10
        )
        
        # Verify result
        self.assertEqual(result, {"key": "value"})
    
    @patch("requests.Session.request")
    def test_request_with_headers(self, mock_request):
        """Test request with custom headers."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"key": "value"}'
        mock_response.json.return_value = {"key": "value"}
        mock_request.return_value = mock_response
        
        # Make request with custom headers
        headers = {"X-Custom-Header": "custom-value"}
        result = self.client.request("GET", "endpoint", headers=headers)
        
        # Verify request was made correctly
        expected_headers = self.client._get_headers()
        expected_headers.update(headers)
        mock_request.assert_called_once_with(
            method="GET",
            url=f"{self.base_url}/endpoint",
            params=None,
            data=None,
            headers=expected_headers,
            timeout=10
        )
        
        # Verify result
        self.assertEqual(result, {"key": "value"})
    
    @patch("requests.Session.request")
    def test_request_with_timeout(self, mock_request):
        """Test request with custom timeout."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"key": "value"}'
        mock_response.json.return_value = {"key": "value"}
        mock_request.return_value = mock_response
        
        # Make request with custom timeout
        result = self.client.request("GET", "endpoint", timeout=20)
        
        # Verify request was made correctly
        mock_request.assert_called_once_with(
            method="GET",
            url=f"{self.base_url}/endpoint",
            params=None,
            data=None,
            headers=self.client._get_headers(),
            timeout=20
        )
        
        # Verify result
        self.assertEqual(result, {"key": "value"})
    
    @patch("requests.Session.request")
    def test_request_http_error(self, mock_request):
        """Test request with HTTP error."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"message": "Not found"}'
        mock_response.json.return_value = {"message": "Not found"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
        mock_request.return_value = mock_response
        
        # Make request and verify it raises APIError
        with self.assertRaises(APIError) as context:
            self.client.request("GET", "endpoint")
        
        # Verify error details
        self.assertEqual(context.exception.message, "Not found")
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.response, {"message": "Not found"})
    
    @patch("requests.Session.request")
    def test_request_json_error(self, mock_request):
        """Test request with JSON parsing error."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Invalid JSON"
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_request.return_value = mock_response
        
        # Make request and verify it raises APIError
        with self.assertRaises(APIError) as context:
            self.client.request("GET", "endpoint")
        
        # Verify error details
        self.assertTrue("Invalid JSON" in context.exception.message)
        self.assertEqual(context.exception.status_code, 200)
    
    @patch("requests.Session.request")
    def test_request_network_error(self, mock_request):
        """Test request with network error."""
        # Mock request to raise ConnectionError
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Make request and verify it raises APIError
        with self.assertRaises(APIError) as context:
            self.client.request("GET", "endpoint")
        
        # Verify error details
        self.assertTrue("Connection refused" in context.exception.message)
    
    @patch("requests.Session.request")
    def test_request_timeout(self, mock_request):
        """Test request with timeout."""
        # Mock request to raise Timeout
        mock_request.side_effect = requests.exceptions.Timeout("Request timed out")
        
        # Make request and verify it raises APIError
        with self.assertRaises(APIError) as context:
            self.client.request("GET", "endpoint")
        
        # Verify error details
        self.assertTrue("Request timed out" in context.exception.message)
    
    @patch("shared.utils.src.clients.base.BaseAPIClient.request")
    def test_get(self, mock_request):
        """Test get method."""
        # Mock request
        mock_request.return_value = {"key": "value"}
        
        # Make GET request
        result = self.client.get("endpoint", params={"param": "value"}, headers={"X-Header": "value"}, timeout=20)
        
        # Verify request was made correctly
        mock_request.assert_called_once_with(
            "GET",
            "endpoint",
            params={"param": "value"},
            data=None,
            headers={"X-Header": "value"},
            timeout=20
        )
        
        # Verify result
        self.assertEqual(result, {"key": "value"})
    
    @patch("shared.utils.src.clients.base.BaseAPIClient.request")
    def test_post(self, mock_request):
        """Test post method."""
        # Mock request
        mock_request.return_value = {"key": "value"}
        
        # Make POST request
        result = self.client.post(
            "endpoint",
            data={"field": "value"},
            params={"param": "value"},
            headers={"X-Header": "value"},
            timeout=20
        )
        
        # Verify request was made correctly
        mock_request.assert_called_once_with(
            "POST",
            "endpoint",
            params={"param": "value"},
            data={"field": "value"},
            headers={"X-Header": "value"},
            timeout=20
        )
        
        # Verify result
        self.assertEqual(result, {"key": "value"})
    
    @patch("shared.utils.src.clients.base.BaseAPIClient.request")
    def test_put(self, mock_request):
        """Test put method."""
        # Mock request
        mock_request.return_value = {"key": "value"}
        
        # Make PUT request
        result = self.client.put(
            "endpoint",
            data={"field": "value"},
            params={"param": "value"},
            headers={"X-Header": "value"},
            timeout=20
        )
        
        # Verify request was made correctly
        mock_request.assert_called_once_with(
            "PUT",
            "endpoint",
            params={"param": "value"},
            data={"field": "value"},
            headers={"X-Header": "value"},
            timeout=20
        )
        
        # Verify result
        self.assertEqual(result, {"key": "value"})
    
    @patch("shared.utils.src.clients.base.BaseAPIClient.request")
    def test_delete(self, mock_request):
        """Test delete method."""
        # Mock request
        mock_request.return_value = {"key": "value"}
        
        # Make DELETE request
        result = self.client.delete(
            "endpoint",
            params={"param": "value"},
            headers={"X-Header": "value"},
            timeout=20
        )
        
        # Verify request was made correctly
        mock_request.assert_called_once_with(
            "DELETE",
            "endpoint",
            params={"param": "value"},
            data=None,
            headers={"X-Header": "value"},
            timeout=20
        )
        
        # Verify result
        self.assertEqual(result, {"key": "value"})


if __name__ == "__main__":
    unittest.main()
