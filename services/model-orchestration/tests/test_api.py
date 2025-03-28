import pytest
import json
from fastapi import status

from src.models.api import ModelProvider, ModelCapability, ModelStatus


class TestModelAPI:
    """
    Tests for the model API endpoints.
    """
    
    def test_register_model(self, client, test_model_data, mock_event_bus):
        """
        Test registering a model.
        """
        # Convert enum values to strings for JSON serialization
        model_data = test_model_data.copy()
        model_data["provider"] = model_data["provider"].value
        model_data["capabilities"] = [cap.value for cap in model_data["capabilities"]]
        model_data["status"] = model_data["status"].value
        
        # Register model
        response = client.post("/api/models", json=model_data)
        
        # Check response
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["model_id"] == model_data["model_id"]
        assert data["provider"] == model_data["provider"]
        assert data["display_name"] == model_data["display_name"]
        assert data["description"] == model_data["description"]
        assert data["max_tokens"] == model_data["max_tokens"]
        assert data["token_limit"] == model_data["token_limit"]
        assert data["cost_per_token"] == model_data["cost_per_token"]
        assert data["configuration"] == model_data["configuration"]
        assert data["metadata"] == model_data["metadata"]
        
        # Check event was published
        mock_event_bus.publish_event.assert_called_once()
        event_name, event_data = mock_event_bus.publish_event.call_args[0]
        assert event_name == "model.registered"
        assert event_data["model_id"] == model_data["model_id"]
        assert event_data["provider"] == model_data["provider"]
    
    def test_list_models(self, client, test_model_data):
        """
        Test listing models.
        """
        # Register model first
        model_data = test_model_data.copy()
        model_data["provider"] = model_data["provider"].value
        model_data["capabilities"] = [cap.value for cap in model_data["capabilities"]]
        model_data["status"] = model_data["status"].value
        client.post("/api/models", json=model_data)
        
        # List models
        response = client.get("/api/models")
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        assert any(item["model_id"] == model_data["model_id"] for item in data["items"])
    
    def test_get_model(self, client, test_model_data):
        """
        Test getting a model.
        """
        # Register model first
        model_data = test_model_data.copy()
        model_data["provider"] = model_data["provider"].value
        model_data["capabilities"] = [cap.value for cap in model_data["capabilities"]]
        model_data["status"] = model_data["status"].value
        client.post("/api/models", json=model_data)
        
        # Get model
        response = client.get(f"/api/models/{model_data['model_id']}")
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["model_id"] == model_data["model_id"]
        assert data["provider"] == model_data["provider"]
        assert data["display_name"] == model_data["display_name"]
        assert data["description"] == model_data["description"]
    
    def test_update_model(self, client, test_model_data, mock_event_bus):
        """
        Test updating a model.
        """
        # Register model first
        model_data = test_model_data.copy()
        model_data["provider"] = model_data["provider"].value
        model_data["capabilities"] = [cap.value for cap in model_data["capabilities"]]
        model_data["status"] = model_data["status"].value
        client.post("/api/models", json=model_data)
        
        # Reset mock
        mock_event_bus.publish_event.reset_mock()
        
        # Update model
        update_data = {
            "display_name": "Updated Model Name",
            "description": "Updated description",
            "status": ModelStatus.INACTIVE.value,
        }
        response = client.put(f"/api/models/{model_data['model_id']}", json=update_data)
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["model_id"] == model_data["model_id"]
        assert data["display_name"] == update_data["display_name"]
        assert data["description"] == update_data["description"]
        assert data["status"] == update_data["status"]
        
        # Check event was published
        mock_event_bus.publish_event.assert_called_once()
        event_name, event_data = mock_event_bus.publish_event.call_args[0]
        assert event_name == "model.updated"
        assert event_data["model_id"] == model_data["model_id"]
        assert "updated_fields" in event_data
        assert set(event_data["updated_fields"]) == {"display_name", "description", "status"}
    
    def test_delete_model(self, client, test_model_data, mock_event_bus):
        """
        Test deleting a model.
        """
        # Register model first
        model_data = test_model_data.copy()
        model_data["provider"] = model_data["provider"].value
        model_data["capabilities"] = [cap.value for cap in model_data["capabilities"]]
        model_data["status"] = model_data["status"].value
        client.post("/api/models", json=model_data)
        
        # Reset mock
        mock_event_bus.publish_event.reset_mock()
        
        # Delete model
        response = client.delete(f"/api/models/{model_data['model_id']}")
        
        # Check response
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Check event was published
        mock_event_bus.publish_event.assert_called_once()
        event_name, event_data = mock_event_bus.publish_event.call_args[0]
        assert event_name == "model.deleted"
        assert event_data["model_id"] == model_data["model_id"]
        
        # Verify model is deleted
        response = client.get(f"/api/models/{model_data['model_id']}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRequestAPI:
    """
    Tests for the request API endpoints.
    """
    
    def test_chat_completion(self, client, test_chat_request_data, mock_event_bus):
        """
        Test chat completion.
        """
        # Send chat request
        response = client.post("/api/models/chat", json=test_chat_request_data)
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response" in data
        assert "request_id" in data
        assert "model_id" in data
        assert "provider" in data
        assert "latency_ms" in data
        
        # Check response content
        assert data["model_id"] == test_chat_request_data["model_id"]
        assert data["response"]["choices"][0]["message"]["content"] == "This is a mock response"
        
        # Check background task was triggered (no direct way to verify)
        # In a real test, we would wait for the background task to complete
    
    def test_embedding(self, client, test_embedding_request_data, mock_event_bus):
        """
        Test embedding.
        """
        # Send embedding request
        response = client.post("/api/models/embedding", json=test_embedding_request_data)
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response" in data
        assert "request_id" in data
        assert "model_id" in data
        assert "provider" in data
        assert "latency_ms" in data
        
        # Check response content
        assert data["model_id"] == test_embedding_request_data["model_id"]
        assert len(data["response"]["data"]) > 0
        assert len(data["response"]["data"][0]["embedding"]) > 0
        
        # Check background task was triggered (no direct way to verify)
        # In a real test, we would wait for the background task to complete


class TestErrorHandling:
    """
    Tests for error handling.
    """
    
    def test_model_not_found(self, client):
        """
        Test model not found error.
        """
        # Get non-existent model
        response = client.get("/api/models/non-existent-model")
        
        # Check response
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert "code" in data
        assert data["code"] == "model_not_found"
    
    def test_invalid_request(self, client):
        """
        Test invalid request error.
        """
        # Send invalid chat request (missing messages)
        response = client.post("/api/models/chat", json={"model_id": "gpt-3.5-turbo"})
        
        # Check response
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
